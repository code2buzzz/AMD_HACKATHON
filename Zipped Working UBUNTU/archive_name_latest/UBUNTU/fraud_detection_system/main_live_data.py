import os
import time
import uuid
import random
from datetime import datetime, timedelta
from neo4j import GraphDatabase

# Source component imports
from src.components.agents.graph import graph
from src.components.data_gen.generator import generate_data
from src.components.database.neo4j_ingest import Neo4jIngestor
from src.components.database.postgres_ingest import PostgresIngestor
from src.components.database.postgres_client import PostgresClient
from src.components.agents.rag.rag_manager import RAG_Manager

# Settings configurations
from config.settings import (
    TABLE_CREATION_SCHEMA_PATH, 
    SYNTHETIC_DATA_DIR, 
    BATCH_SIZE, 
    NEO4J_CONFIG
)


def generate_live_transaction() -> dict:
    """
    Dynamically generates transaction payloads alternating between normal 
    and anomalous features while strictly preserving database schema structures.
    """
    is_fraud = random.random() < 0.20  # 20% simulated fraud distribution
    
    # Standardized 32-character full Hex UUID string
    tx_id = f"TX_{uuid.uuid4().hex.upper()}"
    
    customer_id = f"CUST_{random.randint(1, 1000):05d}"
    device_id = f"DEV_{random.randint(1, 200):05d}"
    
    if random.random() > 0.4:
        beneficiary_id = f"BENE_{random.randint(1, 300):05d}"
        merchant_id = None
        tx_type = "INSTANT_TRANSFER" if random.random() > 0.5 else "WIRE"
    else:
        beneficiary_id = None
        merchant_id = f"MERCH_{random.randint(1, 150):05d}"
        tx_type = "POS" if random.random() > 0.5 else "E_COMMERCE"

    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    hour_of_day = now.hour

    currency_pool = ["INR", "USD", "EUR", "GBP", "CAD"]
    currency = random.choice(currency_pool)

    if is_fraud:
        # Currency-aware realistic fraud bounds
        amount = round(random.uniform(25000.00, 450000.00), 2) if currency == "INR" else round(random.uniform(800.00, 9500.00), 2)
        account_age = random.randint(1, 15)
        freq_24h = random.randint(12, 45)
        failed_tx = random.randint(3, 10)
        device_risk = round(random.uniform(65.0, 99.5), 2)
        session_duration = round(random.uniform(5.0, 25.0), 1)
        avg_tx_7d = round(amount * random.uniform(0.1, 0.3), 2)
        
        return {
            "transaction_id": tx_id, "customer_id": customer_id, "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id, "device_id": device_id, "transaction_timestamp": timestamp_str,
            "transaction_type": tx_type, "transaction_amount": amount, "currency": currency,
            "payment_method": random.choice(["NET_BANKING", "CREDIT_CARD"]),
            "ip_address": f"103.{random.randint(10,99)}.{random.randint(0,255)}.{random.randint(0,255)}",
            "origin_country": "IN", "destination_country": random.choice(["KY", "RU", "KP"]),
            "transaction_status": "PENDING", "is_international": True, "hour_of_day": hour_of_day,
            "account_age_days": account_age, "transaction_frequency_24h": freq_24h, "failed_transaction_count_24h": failed_tx,
            "avg_transaction_amount_7d": avg_tx_7d, "session_duration_minutes": session_duration,
            "device_risk_score": device_risk, "unusual_amount_flag": True, "unusual_location_flag": True,
            "typing_speed_flag": random.choice([True, False]), "shared_device_mule_count": random.randint(5, 25),
            "known_fraud_ring_edge": True, "biometric_anomaly_detected": random.choice([True, False]),
            "automation_script_suspected": random.choice([True, False]), "attack_vector_type": random.choice(["MONEY_LAUNDERING", "ACCOUNT_TAKEOVER"]),
            "features_for_classifier": {
                "account_age_days": account_age, "transaction_frequency_24h": freq_24h, "failed_transaction_count_24h": failed_tx,
                "avg_transaction_amount_7d": avg_tx_7d, "session_duration_minutes": session_duration,
                "device_risk_score": device_risk, "unusual_amount_flag": True, "unusual_location_flag": True, "typing_speed_flag": random.choice([True, False]),
            },
            "agent_pipelines_telemetry": {
                "initial_llm_probability": round(random.uniform(0.85, 0.99), 2), "initial_risk_category": "CRITICAL", "orchestrator_decision": "TERMINATE_TRANSACTION",
                "behavioral_agent_context": {"biometric_anomaly_detected": False, "automation_script_suspected": False},
                "graph_agent_context": {"shared_device_mule_count": random.randint(5, 25), "known_fraud_ring_edge": True},
                "risk_agent_context": {"sanction_list_match": random.choice([True, False]), "pep_flag": False, "beneficiary_risk_rating": "HIGH"},
            },
        }
    else:
        # Standard domestic everyday bounds
        amount = round(random.uniform(100.00, 12000.00), 2) if currency == "INR" else round(random.uniform(10.00, 450.00), 2)
        avg_tx_7d = round(random.uniform(2000.00, 8000.00), 2) if currency == "INR" else round(random.uniform(50.00, 350.00), 2)
        account_age = random.randint(120, 1800)
        freq_24h = random.randint(1, 4)
        failed_tx = 0
        device_risk = round(random.uniform(1.0, 12.0), 2)
        session_duration = round(random.uniform(1.0, 4.0), 1)
        
        return {
            "transaction_id": tx_id, "customer_id": customer_id, "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id, "device_id": device_id, "transaction_timestamp": timestamp_str,
            "transaction_type": tx_type, "transaction_amount": amount, "currency": currency,
            "payment_method": random.choice(["UPI", "DEBIT_CARD"]),
            "ip_address": f"122.161.{random.randint(10,99)}.{random.randint(0,255)}", "origin_country": "IN", "destination_country": "IN",
            "transaction_status": "SUCCESS", "is_international": False, "hour_of_day": hour_of_day,
            "account_age_days": account_age, "transaction_frequency_24h": freq_24h, "failed_transaction_count_24h": failed_tx,
            "avg_transaction_amount_7d": avg_tx_7d, "session_duration_minutes": session_duration,
            "device_risk_score": device_risk, "unusual_amount_flag": False, "unusual_location_flag": False, "typing_speed_flag": False,
            "shared_device_mule_count": 0, "known_fraud_ring_edge": False, "biometric_anomaly_detected": False, "automation_script_suspected": False, "attack_vector_type": "NONE",
            "features_for_classifier": {
                "account_age_days": account_age, "transaction_frequency_24h": freq_24h, "failed_transaction_count_24h": failed_tx,
                "avg_transaction_amount_7d": avg_tx_7d, "session_duration_minutes": session_duration,
                "device_risk_score": device_risk, "unusual_amount_flag": False, "unusual_location_flag": False, "typing_speed_flag": False,
            },
            "agent_pipelines_telemetry": {
                "initial_llm_probability": round(random.uniform(0.0, 0.04), 2), "initial_risk_category": "LOW", "orchestrator_decision": "ALLOW_TRANSACTION",
                "behavioral_agent_context": {"biometric_anomaly_detected": False, "automation_script_suspected": False},
                "graph_agent_context": {"shared_device_mule_count": 0, "known_fraud_ring_edge": False},
                "risk_agent_context": {"sanction_list_match": False, "pep_flag": False, "beneficiary_risk_rating": "LOW"},
            },
        }


def ingest_to_postgres(pg_client, tx: dict, behavior_id: str):
    """Inserts a streaming transaction item context explicitly into SQL DB blocks."""
    base_time = datetime.strptime(tx["transaction_timestamp"], "%Y-%m-%dT%H:%M:%SZ")
    
    query_tx = """
        INSERT INTO transactions (
            transaction_id, customer_id, beneficiary_id, merchant_id, device_id,
            transaction_timestamp, transaction_type, transaction_amount, currency,
            payment_method, transaction_status, ip_address, origin_country,
            destination_country, is_international
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
    """
    with pg_client.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_tx, (
                tx["transaction_id"], tx["customer_id"], tx["beneficiary_id"], tx["merchant_id"], tx["device_id"],
                base_time, tx["transaction_type"], tx["transaction_amount"], tx["currency"][:3], tx["payment_method"],
                tx["transaction_status"], tx["ip_address"], tx["origin_country"], tx["destination_country"], tx["is_international"]
            ))
            conn.commit()


def ingest_to_neo4j(neo4j_session, tx: dict, behavior_id: str):
    """Synchronizes live structural transactional nodes directly with Neo4j instances."""
    cypher_tx = """
    MATCH (c:Customer {customer_id: $row.customer_id})
    MERGE (t:Transaction {transaction_id: $row.transaction_id})
    SET t.transaction_timestamp = $row.transaction_timestamp, t.transaction_type = $row.transaction_type,
        t.transaction_amount = toFloat($row.transaction_amount), t.currency = $row.currency,
        t.payment_method = $row.payment_method, t.transaction_status = $row.transaction_status,
        t.ip_address = $row.ip_address, t.origin_country = $row.origin_country,
        t.destination_country = $row.destination_country, t.is_international = toBoolean($row.is_international)
    MERGE (c)-[:MADE_TRANSACTION]->(t)
    """
    neo4j_session.execute_write(lambda tx_op: tx_op.run(cypher_tx, row={**tx, "behavior_id": behavior_id}))
    neo4j_session.execute_write(lambda tx_op: tx_op.run("MATCH (t:Transaction {transaction_id: $tx_id}), (d:Device {device_id: $d_id}) MERGE (t)-[:VIA_DEVICE]->(d)", tx_id=tx["transaction_id"], d_id=tx["device_id"]))
    if tx["beneficiary_id"]:
        neo4j_session.execute_write(lambda tx_op: tx_op.run("MATCH (t:Transaction {transaction_id: $tx_id}), (b:Beneficiary {beneficiary_id: $b_id}) MERGE (t)-[:TO_BENEFICIARY]->(b)", tx_id=tx["transaction_id"], b_id=tx["beneficiary_id"]))
    if tx["merchant_id"]:
        neo4j_session.execute_write(lambda tx_op: tx_op.run("MATCH (t:Transaction {transaction_id: $tx_id}), (m:Merchant {merchant_id: $m_id}) MERGE (t)-[:AT_MERCHANT]->(m)", tx_id=tx["transaction_id"], m_id=tx["merchant_id"]))


def main():
    print("🔄 Initializing Distributed Ingestor Drivers & Engines...")
    pg_client = PostgresClient()
    
    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]),
    )
    driver.verify_connectivity()
    
    iteration = 0
    with driver.session() as neo4j_session:
        try:
            while True:
                iteration += 1
                live_tx = generate_live_transaction()
                
                timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S")
                behavior_id = f"BEH_{timestamp_id}_{iteration:06d}"
                analysis_id = f"ANAL_{timestamp_id}_{iteration:06d}"
                
                print(f"\n🚀 [ITERATION {iteration}] | Analysis ID: {analysis_id}")
                print(f"   ↳ TX ID: {live_tx['transaction_id']}  |  Type: {live_tx['transaction_type']}  |  Amount: {live_tx['transaction_amount']} {live_tx['currency']}")
                print(f"   ↳ Links  -> Customer: {live_tx['customer_id']}  |  Device: {live_tx['device_id']}  |  Dest: {live_tx['destination_country']}")
                
                # Execute base multi-database writes
                try:
                    ingest_to_postgres(pg_client, live_tx, behavior_id)
                    ingest_to_neo4j(neo4j_session, live_tx, behavior_id)
                except Exception as db_err:
                    print(f"❌ DB Write Error skipped during ingestion tracking step: {db_err}")
                    continue

                # State initialization structure includes local graph retry keys
                state = {
                    "transaction": live_tx,
                    "analysis_id": analysis_id,
                    "behavior_id": behavior_id,
                    "iteration_count": iteration,
                    "graph_retry_count": 0,  # CRITICAL: Rebuilt for confidence router logic
                    "confidence_score": 0,
                    "messages": [],
                }
                
                try:
                    result = graph.invoke(state)
                    # Safely unpack the inner decision engine output
                    decision_status = result.get("decision_result", {}).get("system_action", "PROCESSED")
                    print(f"🔍 [VERDICT] -> System Action Taken: {decision_status}")
                except Exception as graph_err:
                    print(f"❌ Error during graph execution engine logic: {graph_err}")
                
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n🛑 Execution paused by user. Stopping ingestion loop gracefully.")
        finally:
            driver.close()


if __name__ == "__main__":
    main()