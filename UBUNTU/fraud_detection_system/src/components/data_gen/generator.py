import os
import json
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from config.settings import SYNTHETIC_DATA_DIR, REQUIRED_FILES, COUNTS


def data_exists() -> bool:
    """Verifies if all synthetic fraud dataset CSV files are already present."""
    if not os.path.exists(SYNTHETIC_DATA_DIR):
        return False
    return all(os.path.exists(os.path.join(SYNTHETIC_DATA_DIR, f)) for f in REQUIRED_FILES)


def generate_data():

    if data_exists():
        print("✅ All synthetic data files already exist. Skipping generation.")
        return

    # Data don't exist, start generating
    fake = Faker()
    Faker.seed(42)
    random.seed(42)
    np.random.seed(42)

    print("🚀 Starting synthetic fraud data generation (Collision-Proof Edition)...")

    # ----------------------------------------------------
    # 1. SANCTION LIST
    # ----------------------------------------------------
    sanction_data = []
    sanction_ids = [f"SANC_{uuid.uuid4().hex}" for _ in range(COUNTS["sanction_list"])]
    countries = [fake.country() for _ in range(20)] + [
        "Iran",
        "North Korea",
        "Russia",
        "Syria",
    ]

    for i in range(COUNTS["sanction_list"]):
        eff_date = fake.date_between(start_date="-3y", end_date="-1y")
        sanction_data.append(
            {
                "entity_id": sanction_ids[i],
                "entity_name": fake.company() if random.random() > 0.5 else fake.name(),
                "entity_type": random.choice(["Individual", "Organization", "Vessel"]),
                "country": random.choice(countries),
                "sanction_source": random.choice(["OFAC", "EU", "UN", "UKHM"]),
                "sanction_category": random.choice(
                    [
                        "Terrorism Financing",
                        "Narcotics",
                        "Cyber Crime",
                        "Regime Sanctions",
                    ]
                ),
                "reason_for_sanction": fake.sentence(),
                "risk_level": random.choice(["High", "Critical"]),
                "pep_flag": random.choice([True, False]),
                "fraudster_flag": random.choice([True, False]),
                "blacklist_flag": True,
                "regulatory_reference": f"REG-202{random.randint(1,5)}-{random.randint(100,999)}",
                "effective_date": eff_date,
                "expiry_date": (
                    eff_date + timedelta(days=random.randint(365, 1095))
                    if random.random() > 0.3
                    else None
                ),
                "status": "Active",
                "created_at": datetime.now() - timedelta(days=random.randint(100, 500)),
                "updated_at": datetime.now() - timedelta(days=random.randint(1, 99)),
            }
        )
    df_sanction = pd.DataFrame(sanction_data)

    sanctioned_names = df_sanction["entity_name"].tolist()
    sanctioned_countries = df_sanction["country"].tolist()

    # ----------------------------------------------------
    # 2. CUSTOMERS
    # ----------------------------------------------------
    customer_data = []
    customer_ids = [f"CUST_{uuid.uuid4().hex}" for _ in range(COUNTS["customers"])]

    for i in range(COUNTS["customers"]):
        open_date = fake.date_between(start_date="-5y", end_date="-30d")
        age_days = (datetime.now().date() - open_date).days
        is_fraudulent_history = random.random() < 0.03

        customer_data.append(
            {
                "customer_id": customer_ids[i],
                "customer_name": fake.name(),
                "email": fake.unique.email(),
                "phone_number": fake.unique.msisdn()[:15],
                "account_number": fake.unique.iban()[:30],
                "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80),
                "gender": random.choice(
                    ["Male", "Female", "Other", "Prefer not to say"]
                ),
                "account_type": random.choice(
                    ["Savings", "Checking", "Premium", "Business"]
                ),
                "account_open_date": open_date,
                "account_age_days": age_days,
                "nationality": fake.country(),
                "country": fake.country(),
                "city": fake.city(),
                "address": fake.address().replace("\n", ", "),
                "occupation": fake.job(),
                "annual_income": round(random.uniform(20000, 250000), 2),
                "kyc_status": random.choice(
                    ["Verified", "Verified", "Verified", "Pending", "Failed"]
                ),
                "customer_risk_rating": (
                    "High"
                    if is_fraudulent_history
                    else random.choice(["Low", "Low", "Medium"])
                ),
                "previous_fraud_flag": is_fraudulent_history,
                "fraud_incident_count": (
                    random.randint(1, 4) if is_fraudulent_history else 0
                ),
                "created_at": datetime.now() - timedelta(days=age_days),
                "updated_at": datetime.now() - timedelta(days=random.randint(1, 30)),
            }
        )
    df_customers = pd.DataFrame(customer_data)

    # ----------------------------------------------------
    # 3. DEVICES
    # ----------------------------------------------------
    device_data = []
    device_ids = [f"DEV_{uuid.uuid4().hex}" for _ in range(COUNTS["devices"])]

    for i in range(COUNTS["devices"]):
        is_bad_device = random.random() < 0.04

        device_data.append(
            {
                "device_id": device_ids[i],
                "device_fingerprint": fake.unique.sha256(),
                "device_type": random.choice(["Mobile", "Desktop", "Tablet"]),
                "operating_system": random.choice(
                    ["iOS", "Android", "Windows", "MacOS", "Linux"]
                ),
                "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
                "first_seen": fake.date_time_between(start_date="-2y", end_date="-1y"),
                "last_seen": fake.date_time_between(start_date="-30d", end_date="now"),
                "device_risk_score": (
                    round(random.uniform(75.0, 100.0), 2)
                    if is_bad_device
                    else round(random.uniform(0.0, 45.0), 2)
                ),
                "is_blacklisted": is_bad_device,
                "created_at": datetime.now() - timedelta(days=random.randint(200, 600)),
            }
        )
    df_devices = pd.DataFrame(device_data)

    # ----------------------------------------------------
    # 4. BENEFICIARIES
    # ----------------------------------------------------
    beneficiary_data = []
    beneficiary_ids = [
        f"BENE_{uuid.uuid4().hex}" for _ in range(COUNTS["beneficiaries"])
    ]

    for i in range(COUNTS["beneficiaries"]):
        hit_sanction = random.random() < 0.02
        name = random.choice(sanctioned_names) if hit_sanction else fake.name()
        country = (
            random.choice(sanctioned_countries) if hit_sanction else fake.country()
        )

        beneficiary_data.append(
            {
                "beneficiary_id": beneficiary_ids[i],
                "receiver_account": fake.unique.iban()[:30],
                "receiver_name": name,
                "bank_name": fake.company() + " Bank",
                "country": country,
                "risk_rating": (
                    "Critical"
                    if hit_sanction
                    else random.choice(["Low", "Low", "Medium", "High"])
                ),
                "fraud_link_count": (
                    random.randint(2, 8)
                    if hit_sanction
                    else random.choice([0, 0, 0, 1])
                ),
                "sanction_match_flag": hit_sanction,
                "created_at": datetime.now()
                - timedelta(days=random.randint(100, 1000)),
            }
        )
    df_beneficiaries = pd.DataFrame(beneficiary_data)

    # ----------------------------------------------------
    # 5. MERCHANTS
    # ----------------------------------------------------
    merchant_data = []
    merchant_ids = [f"MERCH_{uuid.uuid4().hex}" for _ in range(COUNTS["merchants"])]

    for i in range(COUNTS["merchants"]):
        is_shell_merch = random.random() < 0.05
        merchant_data.append(
            {
                "merchant_id": merchant_ids[i],
                "merchant_name": fake.unique.company(),
                "merchant_category": random.choice(
                    [
                        "Retail",
                        "Gaming",
                        "Crypto Exchange",
                        "Electronics",
                        "Shell Utility",
                    ]
                ),
                "merchant_country": fake.country(),
                "merchant_risk_rating": (
                    "High" if is_shell_merch else random.choice(["Low", "Medium"])
                ),
                "fraud_transaction_count": (
                    random.randint(15, 80) if is_shell_merch else random.randint(0, 2)
                ),
                "total_transaction_count": random.randint(500, 5000),
                "merchant_status": "Under Review" if is_shell_merch else "Active",
                "created_at": datetime.now()
                - timedelta(days=random.randint(300, 1200)),
            }
        )
    df_merchants = pd.DataFrame(merchant_data)

    # ----------------------------------------------------
    # 6. RELATIONAL MAPPING TABLES (Many-to-Many)
    # ----------------------------------------------------
    cust_dev_pairs = set()
    blacklisted_devs = df_devices[df_devices["is_blacklisted"] == True][
        "device_id"
    ].tolist()

    mule_device = blacklisted_devs[0] if blacklisted_devs else device_ids[0]
    for m_cust in customer_ids[:45]:
        cust_dev_pairs.add((m_cust, mule_device))

    while len(cust_dev_pairs) < COUNTS["customer_devices"]:
        cust_dev_pairs.add((random.choice(customer_ids), random.choice(device_ids)))

    cust_devices_data = [
        {
            "customer_device_id": f"CDEV_{uuid.uuid4().hex}",
            "customer_id": p[0],
            "device_id": p[1],
            "first_seen": datetime.now() - timedelta(days=random.randint(30, 300)),
            "last_seen": datetime.now() - timedelta(days=random.randint(1, 29)),
        }
        for p in cust_dev_pairs
    ]
    df_customer_devices = pd.DataFrame(cust_devices_data)

    cust_bene_pairs = set()
    high_risk_benes = df_beneficiaries[df_beneficiaries["sanction_match_flag"] == True][
        "beneficiary_id"
    ].tolist()

    mule_bene = high_risk_benes[0] if high_risk_benes else beneficiary_ids[0]
    for m_cust in customer_ids[100:160]:
        cust_bene_pairs.add((m_cust, mule_bene))

    while len(cust_bene_pairs) < COUNTS["customer_beneficiaries"]:
        cust_bene_pairs.add(
            (random.choice(customer_ids), random.choice(beneficiary_ids))
        )

    cust_benes_data = [
        {
            "customer_beneficiary_id": f"CBEN_{uuid.uuid4().hex}",
            "customer_id": p[0],
            "beneficiary_id": p[1],
            "first_transaction_date": datetime.now()
            - timedelta(days=random.randint(60, 400)),
            "last_transaction_date": datetime.now()
            - timedelta(days=random.randint(1, 59)),
            "relationship_risk_score": (
                round(random.uniform(70.0, 100.0), 2)
                if p[1] == mule_bene
                else round(random.uniform(0.0, 50.0), 2)
            ),
        }
        for p in cust_bene_pairs
    ]
    df_customer_beneficiaries = pd.DataFrame(cust_benes_data)

    # ----------------------------------------------------
    # 7. TRANSACTIONS
    # ----------------------------------------------------
    transaction_data = []
    tx_ids = [f"TX_{uuid.uuid4().hex}" for _ in range(COUNTS["transactions"])]

    cust_to_devs = (
        df_customer_devices.groupby("customer_id")["device_id"].apply(list).to_dict()
    )
    cust_to_benes = (
        df_customer_beneficiaries.groupby("customer_id")["beneficiary_id"]
        .apply(list)
        .to_dict()
    )

    start_timeline = datetime.now() - timedelta(days=180)

    for i in range(COUNTS["transactions"]):
        t_id = tx_ids[i]
        c_id = random.choice(customer_ids)

        d_id = (
            random.choice(cust_to_devs[c_id])
            if c_id in cust_to_devs
            else random.choice(device_ids)
        )

        is_p2p = random.random() > 0.4
        b_id = (
            (
                random.choice(cust_to_benes[c_id])
                if c_id in cust_to_benes
                else random.choice(beneficiary_ids)
            )
            if is_p2p
            else None
        )
        m_id = random.choice(merchant_ids) if not is_p2p else None

        is_fraud_infrastructure = (d_id == mule_device) or (b_id == mule_bene)

        tx_type = (
            random.choice(["Instant Transfer", "ACH", "Wire"])
            if is_p2p
            else random.choice(["POS", "E-Commerce"])
        )
        amount = (
            round(random.uniform(5000, 50000), 2)
            if is_fraud_infrastructure
            else round(random.uniform(5, 1200), 2)
        )

        orig_ctry = fake.country()
        dest_ctry = (
            orig_ctry
            if not is_fraud_infrastructure
            else "North Korea" if random.random() > 0.5 else "Russia"
        )
        is_intl = orig_ctry != dest_ctry

        status = (
            "Declined"
            if (is_fraud_infrastructure and random.random() > 0.5)
            else random.choice(["Approved", "Approved", "Approved", "Pending"])
        )

        transaction_data.append(
            {
                "transaction_id": t_id,
                "customer_id": c_id,
                "beneficiary_id": b_id,
                "merchant_id": m_id,
                "device_id": d_id,
                "transaction_timestamp": start_timeline
                + timedelta(minutes=int(i * (180 * 24 * 60 / COUNTS["transactions"]))),
                "transaction_type": tx_type,
                "transaction_amount": amount,
                "currency": random.choice(["USD", "EUR", "GBP", "CAD"]),
                "payment_method": random.choice(
                    ["Account Balance", "Credit Card", "Debit Card"]
                ),
                "transaction_status": status,
                "ip_address": fake.ipv4(),
                "origin_country": orig_ctry,
                "destination_country": dest_ctry,
                "is_international": is_intl,
                "created_at": datetime.now(),
            }
        )
    df_transactions = pd.DataFrame(transaction_data)

    # ----------------------------------------------------
    # 8. CUSTOMER BEHAVIOR LOGS
    # ----------------------------------------------------
    behavior_data = []
    behavior_ids = [
        f"BEH_{uuid.uuid4().hex}" for _ in range(COUNTS["customer_behavior"])
    ]
    tx_sample_pool = df_transactions.sample(
        n=COUNTS["customer_behavior"], replace=False
    ).to_dict(orient="records")

    for i in range(COUNTS["customer_behavior"]):
        tx_ref = tx_sample_pool[i]
        is_bad = (
            tx_ref["device_id"] == mule_device or tx_ref["beneficiary_id"] == mule_bene
        )

        login_t = tx_ref["transaction_timestamp"] - timedelta(
            minutes=random.randint(2, 15)
        )
        logout_t = tx_ref["transaction_timestamp"] + timedelta(
            minutes=random.randint(1, 10)
        )

        behavior_data.append(
            {
                "behavior_id": behavior_ids[i],
                "customer_id": tx_ref["customer_id"],
                "transaction_id": tx_ref["transaction_id"],
                "device_id": tx_ref["device_id"],
                "login_timestamp": login_t,
                "logout_timestamp": logout_t,
                "session_duration_minutes": int(
                    (logout_t - login_t).total_seconds() / 60
                ),
                "behavior_risk_score": (
                    round(random.uniform(75.0, 100.0), 2)
                    if is_bad
                    else round(random.uniform(0.0, 40.0), 2)
                ),
                "account_takeover_suspected": is_bad and random.random() > 0.3,
                "transaction_frequency_24h": (
                    random.randint(12, 50) if is_bad else random.randint(1, 5)
                ),
                "avg_transaction_amount_7d": (
                    round(random.uniform(8000, 60000), 2)
                    if is_bad
                    else round(random.uniform(10, 500), 2)
                ),
                "failed_transaction_count_24h": (
                    random.randint(4, 15) if is_bad else random.randint(0, 1)
                ),
                "unusual_amount_flag": is_bad,
                "unusual_location_flag": is_bad or random.random() < 0.02,
                "typing_speed_flag": is_bad and random.random() > 0.5,
                "fraud_flag": is_bad,
                "fraud_risk": "High" if is_bad else "Low",
                "created_at": datetime.now(),
            }
        )
    df_customer_behavior = pd.DataFrame(behavior_data)

    # ----------------------------------------------------
    # 9. TRANSACTION ANALYSIS LOGS
    # ----------------------------------------------------
    analysis_data = []
    analysis_ids = [
        f"ANAL_{uuid.uuid4().hex}" for _ in range(COUNTS["transaction_analysis_logs"])
    ]
    tx_list = df_transactions.to_dict(orient="records")
    behavior_map = df_customer_behavior.set_index("transaction_id").to_dict(
        orient="index"
    )

    for i in range(COUNTS["transaction_analysis_logs"]):
        tx_ref = tx_list[i]
        tx_id = tx_ref["transaction_id"]

        has_behavior = tx_id in behavior_map
        is_graph_fraud = (
            tx_ref["device_id"] == mule_device or tx_ref["beneficiary_id"] == mule_bene
        )

        b_score = (
            behavior_map[tx_id]["behavior_risk_score"]
            if has_behavior
            else round(random.uniform(0, 30), 2)
        )
        g_score = (
            round(random.uniform(85, 100), 2)
            if is_graph_fraud
            else round(random.uniform(0, 35), 2)
        )
        s_score = (
            round(random.uniform(90, 100), 2)
            if tx_ref["destination_country"] in ["North Korea", "Russia"]
            else round(random.uniform(0, 10), 2)
        )

        overall = max(b_score, g_score, s_score)
        prob = round(overall / 100.0, 2)

        category = "High" if overall > 75 else "Medium" if overall > 40 else "Low"
        decision = "Block" if overall > 75 else "Review" if overall > 40 else "Approve"

        agent_1 = {
            "agent_name": "VelocityParser",
            "status": "flagged" if b_score > 60 else "clear",
            "metrics": {"24h_count": random.randint(10, 50) if is_graph_fraud else 2},
        }
        agent_2 = {
            "agent_name": "DeviceGraphSpy",
            "status": "shared_mule_pool" if is_graph_fraud else "isolated",
        }
        agent_3 = {"agent_name": "SanctionScanner", "matches": 1 if s_score > 50 else 0}
        agent_4 = {
            "agent_name": "Geolocator",
            "distance_miles": (
                random.randint(2000, 7000) if is_graph_fraud else random.randint(0, 15)
            ),
        }
        agent_5 = {
            "agent_name": "LLMSummarizer",
            "verdict": (
                "Suspicious pattern tracking cluster matching known syndicate"
                if is_graph_fraud
                else "Safe user footprint"
            ),
        }

        analysis_data.append(
            {
                "transaction_analysis_id": analysis_ids[i],
                "transaction_id": tx_id,
                "customer_id": tx_ref["customer_id"],
                "fraud_probability": prob,
                "behavior_score": b_score,
                "graph_score": g_score,
                "sanction_score": s_score,
                "overall_risk_score": overall,
                "risk_category": category,
                "decision": decision,
                "agent1_output": json.dumps(agent_1),
                "agent2_output": json.dumps(agent_2),
                "agent3_output": json.dumps(agent_3),
                "agent4_output": json.dumps(agent_4),
                "agent5_output": json.dumps(agent_5),
                "recommended_action": (
                    "Freeze Account immediately & report SAR"
                    if overall > 75
                    else "None"
                ),
                "investigation_status": "Open" if overall > 75 else "Closed",
                "report": b"Raw investigation binary stream context telemetry data standard dump log metrics string placeholder format",
                "created_at": tx_ref["transaction_timestamp"] + timedelta(seconds=2),
            }
        )
    df_analysis_logs = pd.DataFrame(analysis_data)

    # ----------------------------------------------------
    # 10. SAVE AND EXPORT
    # ----------------------------------------------------
    output_dir = SYNTHETIC_DATA_DIR
    os.makedirs(SYNTHETIC_DATA_DIR, exist_ok=True)

    exports = {
        "customers": df_customers,
        "devices": df_devices,
        "beneficiaries": df_beneficiaries,
        "merchants": df_merchants,
        "customer_devices": df_customer_devices,
        "customer_beneficiaries": df_customer_beneficiaries,
        "sanction_list": df_sanction,
        "transactions": df_transactions,
        "customer_behavior": df_customer_behavior,
        "transaction_analysis_logs": df_analysis_logs,
    }

    # Save each DataFrame to CSV
    print("\n💾 Writing CSV Datasets to system directory...")
    for name, dataframe in exports.items():
        file_path = os.path.join(output_dir, f"{name}.csv")
        dataframe.to_csv(file_path, index=False)
        print(f"   ↳ Written {file_path:<40} Rows Generated: {len(dataframe)}")

    print("\n✨ Data generation complete! Ready for PostgreSQL and Neo4j processing.")


if __name__ == "__main__":
    generate_data()

