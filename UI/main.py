from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
import datetime
import json
from database import get_db, TransactionAnalysisLog, Transaction

app = FastAPI(title="BankDB Anti-Fraud Engine Dashboard API")


def safe_parse_json(payload) -> dict:
    """Helper tool to handle json loads variations from bulk loader storage maps."""
    if not payload:
        return {}
    if isinstance(payload, dict):
        return payload
    try:
        return json.loads(payload)
    except Exception:
        return {"raw_data": str(payload)}


def format_joined_record(log: TransactionAnalysisLog, tx: Transaction) -> dict:
    return {
        "analysis_id": log.transaction_analysis_id,
        "transaction_id": log.transaction_id,
        "customer_id": log.customer_id,
        "timestamp": (
            log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None
        ),
        "amount": float(tx.transaction_amount) if tx and tx.transaction_amount else 0.0,
        "currency": tx.currency if tx else "USD",
        "payment_method": tx.payment_method if tx else "Debit Card",
        "fraud_probability": (
            float(log.fraud_probability) * 100.0 if log.fraud_probability else 0.0
        ),
        "overall_risk_score": (
            float(log.overall_risk_score) if log.overall_risk_score else 0.0
        ),
        "risk_category": log.risk_category.strip() if log.risk_category else None,
        "decision": log.decision.strip() if log.decision else None,
        "investigation_status": log.investigation_status,
        "recommended_action": log.recommended_action,
        "agent_payloads": {
            "anomaly_engine": safe_parse_json(log.agent1_output),
            "behavioral_engine": safe_parse_json(log.agent2_output),
            "network_graph_engine": safe_parse_json(log.agent3_output),
            "compliance_engine": safe_parse_json(log.agent4_output),
            "reasoning_engine": safe_parse_json(log.agent5_output),
        },
    }


@app.get("/api/transactions/latest")
def get_latest_transactions(db: Session = Depends(get_db)):
    results = (
        db.query(TransactionAnalysisLog, Transaction)
        .join(
            Transaction,
            TransactionAnalysisLog.transaction_id == Transaction.transaction_id,
        )
        .order_by(desc(TransactionAnalysisLog.created_at))
        .limit(15)
        .all()
    )
    return [format_joined_record(log, tx) for log, tx in results]


@app.get("/api/metrics/today")
def get_todays_kpis(db: Session = Depends(get_db)):
    """Computes exact categorical KPI decision counters since midnight."""
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    # Aggregate absolute distinct status matches safely using database-side trimming
    metrics = (
        db.query(
            func.count(TransactionAnalysisLog.transaction_analysis_id).label("total_tx"),
            func.count(TransactionAnalysisLog.transaction_analysis_id)
            .filter(func.trim(func.lower(TransactionAnalysisLog.decision)) == "approve")
            .label("accepted_count"),
            func.count(TransactionAnalysisLog.transaction_analysis_id)
            .filter(func.trim(func.lower(TransactionAnalysisLog.decision)) == "review")
            .label("review_count"),
            func.count(TransactionAnalysisLog.transaction_analysis_id)
            .filter(func.trim(func.lower(TransactionAnalysisLog.decision)) == "block")
            .label("blocked_count"),
        )
        .filter(TransactionAnalysisLog.created_at >= today_start)
        .first()
    )

    return {
        "total_transactions": metrics.total_tx or 0,
        "accepted": metrics.accepted_count or 0,
        "review_required": metrics.review_count or 0,
        "blocked": metrics.blocked_count or 0,
    }


@app.get("/api/transactions/search")
def search_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    customer_id: Optional[str] = None,
    risk_category: Optional[str] = None,
    decision: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TransactionAnalysisLog, Transaction).join(
        Transaction, TransactionAnalysisLog.transaction_id == Transaction.transaction_id
    )

    if customer_id and customer_id.strip():
        query = query.filter(
            TransactionAnalysisLog.customer_id.ilike(f"%{customer_id.strip()}%")
        )

    # Wrapped with structural database-side func.trim to prevent spacing issues
    if risk_category and risk_category.strip() and risk_category != "All":
        query = query.filter(
            func.trim(func.upper(TransactionAnalysisLog.risk_category))
            == risk_category.strip().upper()
        )

    if decision and decision.strip() and decision != "All":
        query = query.filter(
            func.trim(func.upper(TransactionAnalysisLog.decision))
            == decision.strip().upper()
        )

    total_records = query.count()
    offset = (page - 1) * page_size

    results = (
        query.order_by(desc(TransactionAnalysisLog.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "total": total_records,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total_records + page_size - 1) // page_size),
        "data": [format_joined_record(log, tx) for log, tx in results],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
