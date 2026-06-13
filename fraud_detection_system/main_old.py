from src.components.agents.graph import graph
from src.components.data_gen.generator import generate_data
from src.components.database.neo4j_ingest import Neo4jIngestor
from src.components.database.postgres_ingest import PostgresIngestor
from config.settings import TABLE_CREATION_SCHEMA_PATH, SYNTHETIC_DATA_DIR, BATCH_SIZE
from src.components.agents.rag.rag_manager import RAG_Manager
from config.settings import MODEL_CONFIG, ROOT_DIR

SQL_INGESTION = False


sample_transaction_good = {
    "transaction_id": "TX_a5f210b396c24be8910fdc772a441e8d",  # Always completely unique
    "customer_id": "CUST_00150",  # Established client outside fraud ring range
    "beneficiary_id": "BENE_00340",
    "merchant_id": None,  # P2P Transfer scenario
    "device_id": "DEV_00450",  # Safe user device hardware index
    "transaction_timestamp": "2026-06-13T10:15:30Z",
    "transaction_type": "TRANSFER",
    "transaction_amount": 1250.00,  # Within typical consumer spending habits
    "currency": "INR",
    "payment_method": "UPI",
    "ip_address": "192.168.1.45",  # Clean domestic router IP space
    "origin_country": "IN",
    "destination_country": "IN",
    "transaction_status": "SUCCESS",
    "is_international": False,
    # --- Root Features (Engine Predictor Alignment) ---
    "hour_of_day": 10,  # Standard active business window
    "account_age_days": 820,  # Vintage trusted ledger age
    "transaction_frequency_24h": 2,
    "failed_transaction_count_24h": 0,
    "avg_transaction_amount_7d": 1180.50,  # Current amount lines up tightly with history
    "session_duration_minutes": 4,  # Normal human pacing
    "device_risk_score": 12.50,  # Very low threat indicators
    "unusual_amount_flag": False,
    "unusual_location_flag": False,
    "typing_speed_flag": False,
    "shared_device_mule_count": 1,
    "known_fraud_ring_edge": False,
    "biometric_anomaly_detected": False,
    "automation_script_suspected": False,
    "attack_vector_type": "NONE",
    # --- Classifier Sub-Structure ---
    "features_for_classifier": {
        "account_age_days": 820,
        "transaction_frequency_24h": 2,
        "failed_transaction_count_24h": 0,
        "avg_transaction_amount_7d": 1180.50,
        "session_duration_minutes": 4,
        "device_risk_score": 12.50,
        "unusual_amount_flag": False,
        "unusual_location_flag": False,
        "typing_speed_flag": False,
    },
    # --- LangGraph Telemetry Engine Metadata ---
    "agent_pipelines_telemetry": {
        "initial_llm_probability": 2.15,
        "initial_risk_category": "LOW",
        "orchestrator_decision": "APPROVED",
        "behavioral_agent_context": {
            "biometric_anomaly_detected": False,
            "automation_script_suspected": False,
        },
        "graph_agent_context": {
            "shared_device_mule_count": 1,
            "known_fraud_ring_edge": False,
        },
        "risk_agent_context": {
            "sanction_list_match": False,
            "pep_flag": False,
            "beneficiary_risk_rating": "LOW",
        },
    },
}


def rungraph():

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
    # generate_data()

    # Ingest into PostgreSQL
    if SQL_INGESTION:
        postgres_ingestor = PostgresIngestor(
            SYNTHETIC_DATA_DIR, TABLE_CREATION_SCHEMA_PATH
        )
        postgres_ingestor.setup_database()
        SQL_INGESTION = False

    # Ingest into Neo4j
    # neo4j_ingestor = Neo4jIngestor(SYNTHETIC_DATA_DIR, BATCH_SIZE)
    # neo4j_ingestor.ingest_data()

    # # # RAG Data Ingestion
    # rag_manager = RAG_Manager()
    # folders = ["behavioral_anomalies", "network_typologies", "legal_compliance"]
    # rag_manager.ingest_folders(folders)

    rungraph()
