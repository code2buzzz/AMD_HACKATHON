import os
import sys
import time
import json
import random
import uuid
from datetime import datetime
import numpy as np
from confluent_kafka import Producer
from dotenv import load_dotenv
from config.settings import KAFKA_CONFIG

# Load environment configuration
load_dotenv("")

config = {
    "bootstrap.servers": KAFKA_CONFIG["bootstrap.servers"],
    "client.id": KAFKA_CONFIG["client.id"],
}
producer = Producer(config)
TOPIC_NAME = "fraud-transactions"


def delivery_report(err, msg):
    if err is not None:
        print(f"[-] Message delivery failed: {err}")
    else:
        print(
            f"[+] Broadcasted Event -> Partition [{msg.partition()}] at offset {msg.offset()}"
        )


# --- 1. SEEDING SCHEMA-ALIGNED SIMULATION DATA ---
CUSTOMERS = [f"CUST_{10000 + i}" for i in range(500)]
FRAUD_RING_CUSTOMERS = CUSTOMERS[:40]  # Mule accounts

DEVICES = [f"DEV_{i:05d}" for i in range(100)]
HIGH_RISK_DEVICES = DEVICES[:10]  # Tainted hardware assets

MERCHANTS = [f"MER_{i:03d}" for i in range(30)]
HIGH_RISK_MERCHANTS = MERCHANTS[:3]

BENEFICIARIES = [f"BEN__{20000 + i}" for i in range(200)]
HIGH_RISK_BENEFICIARIES = BENEFICIARIES[:15]  # Flagged receiver accounts

COUNTRIES = ["IN", "US", "AE", "GB", "SG", "MY", "CH"]
RISK_CATEGORIES = ["LOW", "MEDIUM", "HIGH"]
PAYMENT_METHODS = ["UPI", "CREDIT_CARD", "NET_BANKING", "WALLET"]
TRANSACTION_STATUSES = [
    "SUCCESS",
    "FAILED",
    "PENDING",
    "REVERSED",
]

print("[*] Initialized Advanced Relational Models. Pumping live events to Kafka...")

try:
    while True:
        # --- 2. RELATIONAL ENTITY SELECTION ---
        customer = random.choice(CUSTOMERS)
        device = random.choice(DEVICES)
        merchant = random.choice(MERCHANTS)
        beneficiary = random.choice(BENEFICIARIES)
        tx_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"

        # --- 3. INJECTED FRAUD HEURISTIC LOGIC (PROFILES) ---
        is_fraud = False
        fraud_profile = "NONE"

        if customer in FRAUD_RING_CUSTOMERS:
            is_fraud = True
            fraud_profile = "FRAUD_RING"
        elif device in HIGH_RISK_DEVICES and random.random() < 0.6:
            is_fraud = True
            fraud_profile = "DEVICE_TAKEOVER"
        elif merchant in HIGH_RISK_MERCHANTS and random.random() < 0.5:
            is_fraud = True
            fraud_profile = "SCAM_MERCHANT"
        elif beneficiary in HIGH_RISK_BENEFICIARIES and random.random() < 0.7:
            is_fraud = True
            fraud_profile = "ACCOUNT_TAKEOVER"

        # --- 4. CORRELATED TIMING & FINANCIAL ENGINE ---
        # Fraud vectors often strike during abnormal, low-monitoring hours
        if is_fraud and random.random() < 0.7:
            hour_of_day = random.choice([23, 0, 1, 2, 3, 4, 5])
        else:
            hour_of_day = random.randint(0, 23)

        if is_fraud:
            amount = round(
                float(np.random.lognormal(9.5, 0.5)), 2
            )  # High transaction amount
            # Historical 7-day average for a fraud victim/mule is typically much lower than the burst amount
            avg_transaction_amount_7d = round(float(np.random.lognormal(6.8, 0.4)), 2)
            risk_cat = "HIGH"
            fraud_prob = round(random.uniform(75.0, 99.9), 2)
            decision = random.choice(["BLOCKED", "REVIEW_REQUIRED"])
            transaction_status = (
                "FAILED"
                if decision == "BLOCKED"
                else random.choice(["PENDING", "FAILED", "REVERSED"])
            )
        else:
            amount = round(float(np.random.lognormal(6.5, 0.7)), 2)  # Standard amount
            # Normal user behavior: current amount is close to their 7-day rolling average
            avg_transaction_amount_7d = round(amount * random.uniform(0.75, 1.3), 2)
            risk_cat = "LOW" if random.random() < 0.85 else "MEDIUM"
            fraud_prob = round(random.uniform(0.1, 45.0), 2)
            decision = "APPROVED" if risk_cat == "LOW" else "REVIEW_REQUIRED"
            transaction_status = (
                "SUCCESS"
                if decision == "APPROVED"
                else random.choice(["PENDING", "SUCCESS"])
            )

        # --- 5. NETWORK & TELEMETRY ANOMALIES ---
        origin_country = "IN" if not is_fraud else random.choice(COUNTRIES)
        dest_country = (
            random.choice(COUNTRIES) if (is_fraud and random.random() < 0.3) else "IN"
        )

        ip_address = (
            f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
            if not is_fraud
            else f"{random.randint(40,220)}.{random.randint(10,250)}.{random.randint(0,255)}.{random.randint(1,254)}"
        )

        # --- 5b. PROFILE-DRIVEN TELEMETRY CORRELATION MATRIX ---
        account_age_days = random.randint(10, 1500)
        unusual_amount_flag = amount > (avg_transaction_amount_7d * 2.2)
        unusual_location_flag = origin_country != "IN"

        if fraud_profile == "FRAUD_RING":
            attack_vector_type = "MULE_DISPERSAL"
            transaction_frequency_24h = random.randint(25, 70)
            failed_transaction_count_24h = (
                random.randint(1, 4) if random.random() < 0.4 else 0
            )
            session_duration_minutes = random.randint(4, 15)
            device_risk_score = round(random.uniform(45.0, 75.0), 2)
            typing_speed_flag = random.random() < 0.3
            biometric_anomaly_detected = random.random() < 0.5
            automation_script_suspected = random.random() < 0.2
            shared_device_mule_count = random.randint(6, 20)
            known_fraud_ring_edge = True

        elif fraud_profile == "DEVICE_TAKEOVER":
            attack_vector_type = random.choice(["AUTOMATED_BOT", "CREDENTIAL_STUFFING"])
            transaction_frequency_24h = random.randint(40, 110)
            failed_transaction_count_24h = random.randint(5, 18)
            session_duration_minutes = random.randint(1, 3)  # Fast script executions
            device_risk_score = round(random.uniform(85.0, 100.0), 2)
            typing_speed_flag = True  # Superhuman typing speeds
            biometric_anomaly_detected = True  # No organic sensor tilt/micro-tremors
            automation_script_suspected = True
            shared_device_mule_count = random.randint(2, 5)
            known_fraud_ring_edge = random.random() < 0.4

        elif fraud_profile in ["SCAM_MERCHANT", "ACCOUNT_TAKEOVER"]:
            attack_vector_type = random.choice(["PHISHING", "SIM_SWAP"])
            transaction_frequency_24h = random.randint(3, 12)
            failed_transaction_count_24h = random.randint(1, 6)
            session_duration_minutes = random.randint(
                12, 45
            )  # Long sessions due to user hesitation/scam guidance
            device_risk_score = round(random.uniform(20.0, 60.0), 2)
            typing_speed_flag = False  # Human typing
            biometric_anomaly_detected = (
                random.random() < 0.65
            )  # High anxiety/hesitation biometric profiles
            automation_script_suspected = False
            shared_device_mule_count = 1
            known_fraud_ring_edge = random.random() < 0.3

        else:
            # Legitimate User Baseline Data
            attack_vector_type = "NONE"
            transaction_frequency_24h = random.randint(1, 5)
            failed_transaction_count_24h = (
                random.randint(1, 2) if random.random() < 0.05 else 0
            )
            session_duration_minutes = random.randint(2, 12)
            device_risk_score = (
                round(random.uniform(70.0, 100.0), 2)
                if device in HIGH_RISK_DEVICES
                else round(random.uniform(0.0, 25.0), 2)
            )
            typing_speed_flag = False
            biometric_anomaly_detected = False
            automation_script_suspected = False
            shared_device_mule_count = 1
            known_fraud_ring_edge = False

        # --- 6. SYNTHESIZING COMPREHENSIVE STREAM PAYLOAD ---
        event_payload = {
            "transaction_id": tx_id,
            "customer_id": customer,
            "beneficiary_id": beneficiary,
            "merchant_id": merchant,
            "device_id": device,
            "transaction_timestamp": datetime.utcnow().isoformat() + "Z",
            "transaction_type": random.choice(["TRANSFER", "PAYMENT", "WITHDRAWAL"]),
            "transaction_amount": amount,
            "currency": "INR",
            "payment_method": random.choice(PAYMENT_METHODS),
            "ip_address": ip_address,
            "origin_country": origin_country,
            "destination_country": dest_country,
            "transaction_status": transaction_status,
            "is_international": origin_country != dest_country,
            # --- Root Features ---
            "hour_of_day": hour_of_day,
            "account_age_days": account_age_days,
            "transaction_frequency_24h": transaction_frequency_24h,
            "failed_transaction_count_24h": failed_transaction_count_24h,
            "avg_transaction_amount_7d": avg_transaction_amount_7d,
            "session_duration_minutes": session_duration_minutes,
            "device_risk_score": device_risk_score,
            "unusual_amount_flag": unusual_amount_flag,
            "unusual_location_flag": unusual_location_flag,
            "typing_speed_flag": typing_speed_flag,
            "shared_device_mule_count": shared_device_mule_count,
            "known_fraud_ring_edge": known_fraud_ring_edge,
            "biometric_anomaly_detected": biometric_anomaly_detected,
            "automation_script_suspected": automation_script_suspected,
            "attack_vector_type": attack_vector_type,
            # Classifier Structure
            "features_for_classifier": {
                "account_age_days": account_age_days,
                "transaction_frequency_24h": transaction_frequency_24h,
                "failed_transaction_count_24h": failed_transaction_count_24h,
                "avg_transaction_amount_7d": avg_transaction_amount_7d,
                "session_duration_minutes": session_duration_minutes,
                "device_risk_score": device_risk_score,
                "unusual_amount_flag": unusual_amount_flag,
                "unusual_location_flag": unusual_location_flag,
                "typing_speed_flag": typing_speed_flag,
            },
            # LangGraph / Agentic Engineering Telemetry
            "agent_pipelines_telemetry": {
                "initial_llm_probability": fraud_prob,
                "initial_risk_category": risk_cat,
                "orchestrator_decision": decision,
                "behavioral_agent_context": {
                    "biometric_anomaly_detected": biometric_anomaly_detected,
                    "automation_script_suspected": automation_script_suspected,
                },
                "graph_agent_context": {
                    "shared_device_mule_count": shared_device_mule_count,
                    "known_fraud_ring_edge": known_fraud_ring_edge,
                },
                "risk_agent_context": {
                    "sanction_list_match": is_fraud and random.random() < 0.15,
                    "pep_flag": random.random() < 0.02,
                    "beneficiary_risk_rating": (
                        "HIGH" if beneficiary in HIGH_RISK_BENEFICIARIES else "LOW"
                    ),
                },
            },
        }

        # --- 7. EMIT TO KAFKA BROKER ---
        producer.produce(
            topic=TOPIC_NAME,
            key=customer,
            value=json.dumps(event_payload).encode("utf-8"),
            callback=delivery_report,
        )

        producer.poll(0)
        time.sleep(1.0)

except KeyboardInterrupt:
    print("\n[*] Gracefully stopping the stream producer engine.")
finally:
    producer.flush()
