import os
import sys
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from config.settings import NEO4J_CONFIG


class Neo4jIngestor:
    def __init__(self, data_dir: str, batch_size: int = 2000):
        # synthetic_data_dir,batch size = 2000
        self.synthetic_data_dir = data_dir
        self.batch_size = batch_size

    def verify_data_directory(self, path):
        if not os.path.exists(path):
            print(f"❌ Error: Data directory '{path}' not found.")
            sys.exit(1)

    def execute_batch(self, session, query, df, description):
        print(f"⏳ Ingesting {description}...")

        # Safe conversion: Replace all NaN values with Python None to cleanly map to Cypher NULL values
        df_clean = df.where(pd.notnull(df), None)
        records = df_clean.to_dict(orient="records")

        total_records = len(records)
        for i in range(0, total_records, self.batch_size):
            batch = records[i : i + self.batch_size]
            session.execute_write(lambda tx: tx.run(query, batch=batch))
        print(f"   ↳ Loaded {total_records} records successfully.")

    def ingest_data(self):

        print("🚀 Connecting to Neo4j Aura Database...")
        try:
            print(f"   ↳ URI: {NEO4J_CONFIG['uri']}")
            print(f"   ↳ User: {NEO4J_CONFIG['user']}")
            print(f"   ↳ Password: {NEO4J_CONFIG['password']}")

            driver = GraphDatabase.driver(
                NEO4J_CONFIG["uri"],
                auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]),
            )
            driver.verify_connectivity()
            print("✅ Connection verified successfully!")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return

        # FIXED: session context is left completely empty.
        # This prevents the DatabaseNotFound error on Aura Free instances.
        with driver.session() as session:
            # ----------------------------------------------------
            # 1. CREATE UNIQUENESS CONSTRAINTS & OPTIMIZATION INDEXES
            # ----------------------------------------------------
            print("🛠️ Creating uniqueness constraints and text performance indexes...")
            constraints = [
                "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;",
                "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;",
                "CREATE CONSTRAINT beneficiary_id_unique IF NOT EXISTS FOR (b:Beneficiary) REQUIRE b.beneficiary_id IS UNIQUE;",
                "CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (m:Merchant) REQUIRE m.merchant_id IS UNIQUE;",
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (s:SanctionEntity) REQUIRE s.entity_id IS UNIQUE;",
                "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE;",
                "CREATE INDEX beneficiary_name_idx IF NOT EXISTS FOR (b:Beneficiary) ON (b.receiver_name);",
                "CREATE INDEX sanction_name_idx IF NOT EXISTS FOR (s:SanctionEntity) ON (s.entity_name);",
            ]
            for constraint in constraints:
                session.execute_write(lambda tx: tx.run(constraint))

            # ----------------------------------------------------
            # 2. INGEST CORE ENTITIES (Nodes)
            # ----------------------------------------------------

            # Sanction List
            df_sanction = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "sanction_list.csv")
            )
            cypher_sanction = """
            UNWIND $batch AS row
            MERGE (s:SanctionEntity {entity_id: row.entity_id})
            SET s.entity_name = row.entity_name,
                s.entity_type = row.entity_type,
                s.country = row.country,
                s.sanction_source = row.sanction_source,
                s.sanction_category = row.sanction_category,
                s.reason_for_sanction = row.reason_for_sanction,
                s.risk_level = row.risk_level,
                s.pep_flag = toBoolean(row.pep_flag),
                s.fraudster_flag = toBoolean(row.fraudster_flag),
                s.blacklist_flag = toBoolean(row.blacklist_flag),
                s.regulatory_reference = row.regulatory_reference,
                s.effective_date = row.effective_date,
                s.expiry_date = row.expiry_date,
                s.status = row.status
            """
            self.execute_batch(
                session, cypher_sanction, df_sanction, "Sanction Entities"
            )

            # Customers
            df_customers = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "customers.csv")
            )
            cypher_customers = """
            UNWIND $batch AS row
            MERGE (c:Customer {customer_id: row.customer_id})
            SET c.customer_name = row.customer_name,
                c.email = row.email,
                c.phone_number = row.phone_number,
                c.account_number = row.account_number,
                c.date_of_birth = row.date_of_birth,
                c.gender = row.gender,
                c.account_type = row.account_type,
                c.account_open_date = row.account_open_date,
                c.account_age_days = toInteger(row.account_age_days),
                c.nationality = row.nationality,
                c.country = row.country,
                c.city = row.city,
                c.address = row.address,
                c.occupation = row.occupation,
                c.annual_income = toFloat(row.annual_income),
                c.kyc_status = row.kyc_status,
                c.customer_risk_rating = row.customer_risk_rating,
                c.previous_fraud_flag = toBoolean(row.previous_fraud_flag),
                c.fraud_incident_count = toInteger(row.fraud_incident_count)
            """
            self.execute_batch(session, cypher_customers, df_customers, "Customers")

            # Devices
            df_devices = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "devices.csv")
            )
            cypher_devices = """
            UNWIND $batch AS row
            MERGE (d:Device {device_id: row.device_id})
            SET d.device_fingerprint = row.device_fingerprint,
                d.device_type = row.device_type,
                d.operating_system = row.operating_system,
                d.browser = row.browser,
                d.first_seen = row.first_seen,
                d.last_seen = row.last_seen,
                d.device_risk_score = toFloat(row.device_risk_score),
                d.is_blacklisted = toBoolean(row.is_blacklisted)
            """
            self.execute_batch(session, cypher_devices, df_devices, "Devices")

            # Beneficiaries
            df_beneficiaries = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "beneficiaries.csv")
            )
            cypher_beneficiaries = """
            UNWIND $batch AS row
            MERGE (b:Beneficiary {beneficiary_id: row.beneficiary_id})
            SET b.receiver_account = row.receiver_account,
                b.receiver_name = row.receiver_name,
                b.bank_name = row.bank_name,
                b.country = row.country,
                b.risk_rating = row.risk_rating,
                b.fraud_link_count = toInteger(row.fraud_link_count),
                b.sanction_match_flag = toBoolean(row.sanction_match_flag)
            """
            self.execute_batch(
                session, cypher_beneficiaries, df_beneficiaries, "Beneficiaries"
            )

            # Merchants
            df_merchants = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "merchants.csv")
            )
            cypher_merchants = """
            UNWIND $batch AS row
            MERGE (m:Merchant {merchant_id: row.merchant_id})
            SET m.merchant_name = row.merchant_name,
                m.merchant_category = row.merchant_category,
                m.merchant_country = row.merchant_country,
                m.merchant_risk_rating = row.merchant_risk_rating,
                m.fraud_transaction_count = toInteger(row.fraud_transaction_count),
                m.total_transaction_count = toInteger(row.total_transaction_count),
                m.merchant_status = row.merchant_status
            """
            self.execute_batch(session, cypher_merchants, df_merchants, "Merchants")

            # Transactions & Core Customer Links
            # Transactions & Core Customer Links
            df_transactions = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "transactions.csv")
            )
            cypher_transactions = """
            UNWIND $batch AS row
            MATCH (c:Customer {customer_id: row.customer_id})
            MERGE (t:Transaction {transaction_id: row.transaction_id})
            SET t.transaction_timestamp = row.transaction_timestamp,
                t.transaction_type = row.transaction_type,
                t.transaction_amount = toFloat(row.transaction_amount),
                t.currency = row.currency,
                t.payment_method = row.payment_method,
                t.transaction_status = row.transaction_status,
                t.ip_address = row.ip_address,
                t.origin_country = row.origin_country,
                t.destination_country = row.destination_country,
                t.is_international = toBoolean(row.is_international)
            MERGE (c)-[:MADE_TRANSACTION]->(t)
            """
            self.execute_batch(
                session,
                cypher_transactions,
                df_transactions,
                "Transactions (and MADE_TRANSACTION links)",
            )

            # ----------------------------------------------------
            # 3. ENRICH TRANSACTION PROPERTIES (Behavior & Logs)
            # ----------------------------------------------------

            # Customer Behavior Profiles
            df_behavior = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "customer_behavior.csv")
            )
            cypher_behavior = """
            UNWIND $batch AS row
            MATCH (t:Transaction {transaction_id: row.transaction_id})
            SET t.behavior_id = row.behavior_id,
                t.login_timestamp = row.login_timestamp,
                t.logout_timestamp = row.logout_timestamp,
                t.session_duration_minutes = toInteger(row.session_duration_minutes),
                t.behavior_risk_score = toFloat(row.behavior_risk_score),
                t.account_takeover_suspected = toBoolean(row.account_takeover_suspected),
                t.transaction_frequency_24h = toInteger(row.transaction_frequency_24h),
                t.avg_transaction_amount_7d = toFloat(row.avg_transaction_amount_7d),
                t.failed_transaction_count_24h = toInteger(row.failed_transaction_count_24h),
                t.unusual_amount_flag = toBoolean(row.unusual_amount_flag),
                t.unusual_location_flag = toBoolean(row.unusual_location_flag),
                t.typing_speed_flag = toBoolean(row.typing_speed_flag),
                t.behavior_fraud_flag = toBoolean(row.fraud_flag),
                t.behavior_fraud_risk = row.fraud_risk
            """
            self.execute_batch(
                session, cypher_behavior, df_behavior, "Transaction Behavioral Data"
            )

            # Transaction Analytics Logs
            df_analysis = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "transaction_analysis_logs.csv")
            )
            cypher_analysis = """
            UNWIND $batch AS row
            MATCH (t:Transaction {transaction_id: row.transaction_id})
            SET t.transaction_analysis_id = row.transaction_analysis_id,
                t.fraud_probability = toFloat(row.fraud_probability),
                t.behavior_score = toFloat(row.behavior_score),
                t.graph_score = toFloat(row.graph_score),
                t.sanction_score = toFloat(row.sanction_score),
                t.overall_risk_score = toFloat(row.overall_risk_score),
                t.risk_category = row.risk_category,
                t.decision = row.decision,
                t.agent1_output = row.agent1_output,
                t.agent2_output = row.agent2_output,
                t.agent3_output = row.agent3_output,
                t.agent4_output = row.agent4_output,
                t.agent5_output = row.agent5_output,
                t.recommended_action = row.recommended_action,
                t.investigation_status = row.investigation_status
            """
            self.execute_batch(
                session,
                cypher_analysis,
                df_analysis,
                "Transaction AI Agent Analytics Logs",
            )

            # ----------------------------------------------------
            # 4. INGEST INTERMEDIARY MAPS & TRANSACTION EDGES
            # ----------------------------------------------------

            # Customer Device Relations
            df_cust_dev = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "customer_devices.csv")
            )
            cypher_cust_dev = """
            UNWIND $batch AS row
            MATCH (c:Customer {customer_id: row.customer_id})
            MATCH (d:Device {device_id: row.device_id})
            MERGE (c)-[r:HAS_DEVICE]->(d)
            SET r.customer_device_id = row.customer_device_id,
                r.first_seen = row.first_seen,
                r.last_seen = row.last_seen
            """
            self.execute_batch(
                session, cypher_cust_dev, df_cust_dev, "Customer ↔ Device Mapping"
            )

            # Customer Beneficiary Relations
            df_cust_bene = pd.read_csv(
                os.path.join(self.synthetic_data_dir, "customer_beneficiaries.csv")
            )
            cypher_cust_bene = """
            UNWIND $batch AS row
            MATCH (c:Customer {customer_id: row.customer_id})
            MATCH (b:Beneficiary {beneficiary_id: row.beneficiary_id})
            MERGE (c)-[r:HAS_BENEFICIARY]->(b)
            SET r.customer_beneficiary_id = row.customer_beneficiary_id,
                r.first_transaction_date = row.first_transaction_date,
                r.last_transaction_date = row.last_transaction_date,
                r.relationship_risk_score = toFloat(row.relationship_risk_score)
            """
            self.execute_batch(
                session,
                cypher_cust_bene,
                df_cust_bene,
                "Customer ↔ Beneficiary Mapping",
            )

            # Edge Maps
            df_tx_device = df_transactions[df_transactions["device_id"].notna()]
            cypher_tx_device = """
            UNWIND $batch AS row
            MATCH (t:Transaction {transaction_id: row.transaction_id})
            MATCH (d:Device {device_id: row.device_id})
            MERGE (t)-[:VIA_DEVICE]->(d)
            """
            self.execute_batch(
                session, cypher_tx_device, df_tx_device, "Transaction → Device Links"
            )

            df_tx_bene = df_transactions[df_transactions["beneficiary_id"].notna()]
            cypher_tx_bene = """
            UNWIND $batch AS row
            MATCH (t:Transaction {transaction_id: row.transaction_id})
            MATCH (b:Beneficiary {beneficiary_id: row.beneficiary_id})
            MERGE (t)-[:TO_BENEFICIARY]->(b)
            """
            self.execute_batch(
                session, cypher_tx_bene, df_tx_bene, "Transaction → Beneficiary Links"
            )

            df_tx_merch = df_transactions[df_transactions["merchant_id"].notna()]
            cypher_tx_merch = """
            UNWIND $batch AS row
            MATCH (t:Transaction {transaction_id: row.transaction_id})
            MATCH (m:Merchant {merchant_id: row.merchant_id})
            MERGE (t)-[:AT_MERCHANT]->(m)
            """
            self.execute_batch(
                session, cypher_tx_merch, df_tx_merch, "Transaction → Merchant Links"
            )

            # ----------------------------------------------------
            # 5. POST-PROCESSING (Cross-Entity Graph Matching)
            # ----------------------------------------------------
            print(
                "🔗 Cross-connecting Beneficiaries to Sanction Entities using name matching..."
            )
            cypher_post_process = """
            MATCH (b:Beneficiary), (s:SanctionEntity)
            WHERE b.receiver_name = s.entity_name
            MERGE (b)-[:SANCTION_MATCH]->(s)
            """
            session.execute_write(lambda tx: tx.run(cypher_post_process))
            print("   ↳ Sanction matching links generated successfully.")

        driver.close()
        print(
            "\n✨ Bulk Ingestion to Neo4j Aura Completed! Your graph data is fully connected."
        )
