from src.components.agents.graph import graph
from src.components.data_gen.generator import generate_data
from src.components.database.neo4j_ingest import Neo4jIngestor
from src.components.database.postgres_ingest import PostgresIngestor
from config.settings import TABLE_CREATION_SCHEMA_PATH, SYNTHETIC_DATA_DIR, BATCH_SIZE
from src.components.agents.rag.rag_manager import RAG_Manager
from config.settings import MODEL_CONFIG, ROOT_DIR

sample_transaction_fraud = {
    "transaction_id": "TXN330291",
    "customer_id": "CUST711",
    "beneficiary_id": "BEN409",
    "merchant_id": "MER881",
    "device_id": "DEV104",
    "transaction_timestamp": "2026-06-12T14:45:00Z",
    "transaction_type": "PAYMENT",
    "transaction_amount": 1450000,
    "currency": "INR",
    "payment_method": "NET_BANKING",
    "ip_address": "103.44.12.19",
    "origin_country": "IN",
    "destination_country": "KY",
    "transaction_status": "PENDING",
    "is_international": True,
    # --- Root Features (Crucial for your Predictor dataframe) ---
    "hour_of_day": 14,
    "account_age_days": 2,
    "transaction_frequency_24h": 18,
    "failed_transaction_count_24h": 0,
    "avg_transaction_amount_7d": 0,
    "session_duration_minutes": 5.4,
    "device_risk_score": 62.1,
    "unusual_amount_flag": True,
    "unusual_location_flag": True,
    "typing_speed_flag": False,
    "shared_device_mule_count": 14,
    "known_fraud_ring_edge": True,
    "biometric_anomaly_detected": False,
    "automation_script_suspected": False,
    "attack_vector_type": "MONEY_LAUNDERING",
    # --- Classifier Sub-Structure ---
    "features_for_classifier": {
        "account_age_days": 2,
        "transaction_frequency_24h": 18,
        "failed_transaction_count_24h": 0,
        "avg_transaction_amount_7d": 0,
        "session_duration_minutes": 5.4,
        "device_risk_score": 62.1,
        "unusual_amount_flag": True,
        "unusual_location_flag": True,
        "typing_speed_flag": False,
    },
    # --- LangGraph / Agentic Engineering Telemetry ---
    "agent_pipelines_telemetry": {
        "initial_llm_probability": 0.97,
        "initial_risk_category": "CRITICAL",
        "orchestrator_decision": "BLOCK",
        "behavioral_agent_context": {
            "biometric_anomaly_detected": False,
            "automation_script_suspected": False,
        },
        "graph_agent_context": {
            "shared_device_mule_count": 14,
            "known_fraud_ring_edge": True,
        },
        "risk_agent_context": {
            "sanction_list_match": True,
            "pep_flag": False,
            "beneficiary_risk_rating": "HIGH",
        },
    },
}


sample_transaction_good = {
    "transaction_id": "TXN100021",
    "customer_id": "CUST102",
    "beneficiary_id": "BEN001",
    "merchant_id": "MER551",
    "device_id": "DEV001",
    "transaction_timestamp": "2026-06-12T12:30:00Z",
    "transaction_type": "PAYMENT",
    "transaction_amount": 3500,  # Standard everyday amount
    "currency": "INR",
    "payment_method": "UPI",
    "ip_address": "122.161.44.12",  # Standard domestic ISP range
    "origin_country": "IN",
    "destination_country": "IN",
    "transaction_status": "SUCCESS",
    "is_international": False,
    # --- Root Features (Crucial for your Predictor dataframe) ---
    "hour_of_day": 12,  # Middle of the day, low-risk timing
    "account_age_days": 1150,  # Vintage, deeply trusted user account
    "transaction_frequency_24h": 2,
    "failed_transaction_count_24h": 0,
    "avg_transaction_amount_7d": 4200,
    "session_duration_minutes": 2.1,  # Natural human typing and navigation flow
    "device_risk_score": 4.5,  # Completely safe device footprint
    "unusual_amount_flag": False,
    "unusual_location_flag": False,
    "typing_speed_flag": False,
    "shared_device_mule_count": 0,
    "known_fraud_ring_edge": False,
    "biometric_anomaly_detected": False,
    "automation_script_suspected": False,
    "attack_vector_type": "NONE",
    # --- Classifier Sub-Structure ---
    "features_for_classifier": {
        "account_age_days": 1150,
        "transaction_frequency_24h": 2,
        "failed_transaction_count_24h": 0,
        "avg_transaction_amount_7d": 4200,
        "session_duration_minutes": 2.1,
        "device_risk_score": 4.5,
        "unusual_amount_flag": False,
        "unusual_location_flag": False,
        "typing_speed_flag": False,
    },
    # --- LangGraph / Agentic Engineering Telemetry ---
    "agent_pipelines_telemetry": {
        "initial_llm_probability": 0.01,
        "initial_risk_category": "LOW",
        "orchestrator_decision": "APPROVE",
        "behavioral_agent_context": {
            "biometric_anomaly_detected": False,
            "automation_script_suspected": False,
        },
        "graph_agent_context": {
            "shared_device_mule_count": 0,
            "known_fraud_ring_edge": False,
        },
        "risk_agent_context": {
            "sanction_list_match": False,
            "pep_flag": False,
            "beneficiary_risk_rating": "LOW",
        },
    },
}


def main():

    state = {
        "transaction": sample_transaction_good,
        "iteration_count": 0,
        "confidence_score": 0,
        "messages": [],
    }

    result = graph.invoke(state)

    print(result)


if __name__ == "__main__":
    # Generate synthetic data
    generate_data()

    # Ingest into PostgreSQL
    # postgres_ingestor = PostgresIngestor(SYNTHETIC_DATA_DIR, TABLE_CREATION_SCHEMA_PATH)
    # postgres_ingestor.setup_database()

    # Ingest into Neo4j
    neo4j_ingestor = Neo4jIngestor(SYNTHETIC_DATA_DIR, BATCH_SIZE)
    neo4j_ingestor.ingest_data()

    # # RAG Data Ingestion
    rag_manager = RAG_Manager()
    folders = ["behavioral_anomalies", "network_typologies", "legal_compliance"]
    rag_manager.ingest_folders(folders)

    main()
