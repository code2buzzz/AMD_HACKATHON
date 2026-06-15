# Change your top import line to include Text
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/BankDB"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), nullable=False)
    beneficiary_id = Column(String(50))
    merchant_id = Column(String(50))
    device_id = Column(String(100))
    transaction_timestamp = Column(DateTime, nullable=False)
    transaction_type = Column(String(50))
    transaction_amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    payment_method = Column(String(50))
    transaction_status = Column(String(20))
    ip_address = Column(String(100))
    origin_country = Column(String(100))
    destination_country = Column(String(100))
    is_international = Column(Boolean)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relational link back to telemetry logs
    analysis_log = relationship(
        "TransactionAnalysisLog", uselist=False, back_populates="transaction_rel"
    )


class TransactionAnalysisLog(Base):
    __tablename__ = "transaction_analysis_logs"

    transaction_analysis_id = Column(String(50), primary_key=True)
    transaction_id = Column(
        String(50),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    customer_id = Column(String(50), nullable=False)
    fraud_probability = Column(Numeric(5, 2))
    behavior_score = Column(Numeric(5, 2))
    graph_score = Column(Numeric(5, 2))
    sanction_score = Column(Numeric(5, 2))
    overall_risk_score = Column(Numeric(5, 2))
    risk_category = Column(String(20))
    decision = Column(String(50))

    # LangGraph Telemetry Storage Mapping
    agent1_output = Column(JSONB)  # maps to anomaly_result
    agent2_output = Column(JSONB)  # maps to behavioral_result
    agent3_output = Column(JSONB)  # maps to network_result
    agent4_output = Column(JSONB)  # maps to compliance_result
    agent5_output = Column(JSONB)  # maps to reasoning_result

    recommended_action = Column(Text)
    investigation_status = Column(String(50))
    report = Column(BYTEA)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    transaction_rel = relationship("Transaction", back_populates="analysis_log")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
