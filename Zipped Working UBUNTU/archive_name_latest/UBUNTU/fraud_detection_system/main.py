import streamlit as st
import pandas as pd
import random
import json
import uuid
from datetime import datetime
import numpy as np
from collections import deque
from streamlit_autorefresh import st_autorefresh

# --- LANGGRAPH CORE IMPORTS ---
try:
    from src.components.agents.graph import model_orchestration
except ImportError:
    st.error("Failed to import model_orchestration from your graph source.")
    model_orchestration = None

try:
    from config.settings import COUNTS
except ImportError:
    COUNTS = {"customers": 500, "devices": 200, "merchants": 100, "beneficiaries": 150}

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Fraud Agent Graph Matrix",
    page_icon="🚨",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container { padding-top: 1.5rem; }
[data-testid="stMetric"] {
    border: 1px solid rgba(255,255,255,0.08);
    padding: 12px;
    border-radius: 12px;
}
.decision-approved { color:#22c55e; font-weight:700; }
.decision-review { color:#f59e0b; font-weight:700; }
.decision-blocked { color:#ef4444; font-weight:700; }
</style>
""",
    unsafe_allow_html=True,
)

# =====================================================
# SEED ARRAY CONFIGURATIONS & GENERATOR
# =====================================================
CUSTOMERS = [f"CUST_{i+1:05d}" for i in range(COUNTS["customers"])]
FRAUD_RING_CUSTOMERS = CUSTOMERS[:45]
DEVICES = [f"DEV_{i+1:05d}" for i in range(COUNTS["devices"])]
HIGH_RISK_DEVICES = DEVICES[:10]
MERCHANTS = [f"MERCH_{i+1:05d}" for i in range(COUNTS["merchants"])]
HIGH_RISK_MERCHANTS = MERCHANTS[:3]
BENEFICIARIES = [f"BENE_{i+1:05d}" for i in range(COUNTS["beneficiaries"])]
HIGH_RISK_BENEFICIARIES = BENEFICIARIES[:15]
COUNTRIES = ["IN", "US", "AE", "GB", "SG", "MY", "CH"]
PAYMENT_METHODS = ["UPI", "CREDIT_CARD", "NET_BANKING", "WALLET"]


def generate_live_transaction() -> dict:
    """
    Dynamically generates transaction payloads alternating between normal 
    and anomalous features while strictly preserving data schema structures.
    """
    is_fraud = random.random() < 0.20  # 20% simulated fraud distribution
    
    # STANDARDIZED: Uniform full-length 32-character Hex UUID string
    tx_id = f"TX_{uuid.uuid4().hex.upper()}"
    
    customer_id = f"CUST_{random.randint(1, 1000):05d}"
    device_id = f"DEV_{random.randint(1, 200):05d}"
    
    if random.random() > 0.4:
        beneficiary_id = f"BENE_{random.randint(1, 300):05d}"
        merchant_id = None
        tx_type = random.choice(["INSTANT_TRANSFER", "WIRE", "ACH"])
    else:
        beneficiary_id = None
        merchant_id = f"MERCH_{random.randint(1, 150):05d}"
        tx_type = random.choice(["POS", "E_COMMERCE"])

    now = datetime.utcnow()
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    hour_of_day = now.hour

    # STANDARDIZED: Unified currency pool across stacks
    currency_pool = ["INR", "USD", "EUR", "GBP", "CAD"]

    if is_fraud:
        amount = round(random.uniform(150000, 2500000), 2)
        account_age = random.randint(1, 15)
        freq_24h = random.randint(12, 45)
        failed_tx = random.randint(3, 10)
        device_risk = round(random.uniform(65.0, 99.5), 2)
        session_duration = round(random.uniform(5.0, 25.0), 1)
        
        return {
            "transaction_id": tx_id,
            "customer_id": customer_id,
            "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "transaction_timestamp": timestamp_str,
            "transaction_type": tx_type,
            "transaction_amount": amount,
            "currency": random.choice(currency_pool),
            "payment_method": random.choice(["NET_BANKING", "CREDIT_CARD"]),
            "ip_address": f"103.{random.randint(10,99)}.{random.randint(0,255)}.{random.randint(0,255)}",
            "origin_country": "IN",
            "destination_country": random.choice(["KY", "RU", "KP"]),
            "transaction_status": "PENDING",
            "is_international": True,
            "hour_of_day": hour_of_day,
            "account_age_days": account_age,
            "transaction_frequency_24h": freq_24h,
            "failed_transaction_count_24h": failed_tx,
            "avg_transaction_amount_7d": round(random.uniform(10000, 80000), 2),
            "session_duration_minutes": session_duration,
            "device_risk_score": device_risk,
            "unusual_amount_flag": True,
            "unusual_location_flag": True,
            "typing_speed_flag": random.choice([True, False]),
            "shared_device_mule_count": random.randint(5, 25),
            "known_fraud_ring_edge": True,
            "biometric_anomaly_detected": random.choice([True, False]),
            "automation_script_suspected": random.choice([True, False]),
            "attack_vector_type": random.choice(["MONEY_LAUNDERING", "ACCOUNT_TAKEOVER"]),
            "features_for_classifier": {
                "account_age_days": account_age,
                "transaction_frequency_24h": freq_24h,
                "failed_transaction_count_24h": failed_tx,
                "avg_transaction_amount_7d": round(random.uniform(10000, 80000), 2),
                "session_duration_minutes": session_duration,
                "device_risk_score": device_risk,
                "unusual_amount_flag": True,
                "unusual_location_flag": True,
                "typing_speed_flag": random.choice([True, False]),
            },
            "agent_pipelines_telemetry": {
                "initial_llm_probability": round(random.uniform(0.85, 0.99), 2),
                "initial_risk_category": "CRITICAL",
                "orchestrator_decision": "TERMINATE_TRANSACTION",
                "behavioral_agent_context": {
                    "biometric_anomaly_detected": False,
                    "automation_script_suspected": False,
                },
                "graph_agent_context": {
                    "shared_device_mule_count": random.randint(5, 25),
                    "known_fraud_ring_edge": True,
                },
                "risk_agent_context": {
                    "sanction_list_match": random.choice([True, False]),
                    "pep_flag": False,
                    "beneficiary_risk_rating": "HIGH",
                },
            },
        }
    else:
        amount = round(random.uniform(100, 6000), 2)
        account_age = random.randint(120, 1800)
        freq_24h = random.randint(1, 4)
        failed_tx = 0
        device_risk = round(random.uniform(1.0, 12.0), 2)
        session_duration = round(random.uniform(1.0, 4.0), 1)
        
        return {
            "transaction_id": tx_id,
            "customer_id": customer_id,
            "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "transaction_timestamp": timestamp_str,
            "transaction_type": tx_type,
            "transaction_amount": amount,
            "currency": random.choice(currency_pool),
            "payment_method": random.choice(["UPI", "DEBIT_CARD"]),
            "ip_address": f"122.161.{random.randint(10,99)}.{random.randint(0,255)}",
            "origin_country": "IN",
            "destination_country": "IN",
            "transaction_status": "SUCCESS",
            "is_international": False,
            "hour_of_day": hour_of_day,
            "account_age_days": account_age,
            "transaction_frequency_24h": freq_24h,
            "failed_transaction_count_24h": failed_tx,
            "avg_transaction_amount_7d": round(random.uniform(2000, 7000), 2),
            "session_duration_minutes": session_duration,
            "device_risk_score": device_risk,
            "unusual_amount_flag": False,
            "unusual_location_flag": False,
            "typing_speed_flag": False,
            "shared_device_mule_count": 0,
            "known_fraud_ring_edge": False,
            "biometric_anomaly_detected": False,
            "automation_script_suspected": False,
            "attack_vector_type": "NONE",
            "features_for_classifier": {
                "account_age_days": account_age,
                "transaction_frequency_24h": freq_24h,
                "failed_transaction_count_24h": failed_tx,
                "avg_transaction_amount_7d": round(random.uniform(2000, 7000), 2),
                "session_duration_minutes": session_duration,
                "device_risk_score": device_risk,
                "unusual_amount_flag": False,
                "unusual_location_flag": False,
                "typing_speed_flag": False,
            },
            "agent_pipelines_telemetry": {
                "initial_llm_probability": round(random.uniform(0.0, 0.04), 2),
                "initial_risk_category": "LOW",
                "orchestrator_decision": "ALLOW_TRANSACTION",
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


# =====================================================
# GLOBAL SESSION STATES Initialization
# =====================================================
MAX_ROWS = 10

if "transactions" not in st.session_state:
    st.session_state.transactions = deque(maxlen=MAX_ROWS)
if "total_processed" not in st.session_state:
    st.session_state.total_processed = 0
if "approved_count" not in st.session_state:
    st.session_state.approved_count = 0
if "review_count" not in st.session_state:
    st.session_state.review_count = 0
if "blocked_count" not in st.session_state:
    st.session_state.blocked_count = 0
if "last_refresh_count" not in st.session_state:
    st.session_state.last_refresh_count = -1


# =====================================================
# PIPELINE EXECUTION FUNCTION
# =====================================================
def run_live_graph_pipeline():
    if model_orchestration is None:
        return

    raw_tx = generate_raw_transaction()
    state_input = {
        "transaction": raw_tx,
        "anomaly_result": {},
        "behavioral_result": {},
        "network_result": {},
        "compliance_result": {},
        "reasoning_result": {},
        "decision_result": {},
        "report_path": None,
        "iteration_count": 0,
        "confidence_score": 0.0,
        "messages": [],
    }

    try:
        # Wrap in a spinner to give UI feedback if it runs a bit slow
        with st.spinner("Invoking LangGraph Orchestration..."):
            final_output_state = model_orchestration.invoke(state_input)

        decision_map = final_output_state.get("decision_result", {})
        decision = decision_map.get("decision", "APPROVED")

        st.session_state.total_processed += 1
        if decision == "BLOCKED":
            st.session_state.blocked_count += 1
        elif decision == "REVIEW_REQUIRED":
            st.session_state.review_count += 1
        else:
            st.session_state.approved_count += 1

        st.session_state.transactions.appendleft(final_output_state)
    except Exception as e:
        st.error(f"Error executing LangGraph Orchestration: {e}")


# =====================================================
# CARD RENDERING ASSISTANTS & MODALS
# =====================================================
def render_ui_card(title, parameters):
    with st.container(border=True):
        st.markdown(f"##### {title}")
        for key, val in parameters.items():
            l_col, r_col = st.columns([1, 1])
            l_col.markdown(
                f"<span style='color:#9CA3AF'>{key}</span>", unsafe_allow_html=True
            )
            if isinstance(val, bool):
                r_col.markdown("🚨 **True**" if val else "✅ **False**")
            else:
                r_col.markdown(f"**{val}**")


@st.dialog("🔍 State Context Investigation", width="large")
def render_investigation_modal(state):
    tx = state["transaction"]
    anomaly = state.get("anomaly_result", {})
    behavioral = state.get("behavioral_result", {})
    network = state.get("network_result", {})
    compliance = state.get("compliance_result", {})
    reasoning = state.get("reasoning_result", {})
    decision_res = state.get("decision_result", {})

    decision = decision_res.get("decision", "APPROVED")
    risk_cat = decision_res.get("risk_category", "LOW")

    if decision == "BLOCKED":
        decision_html = '<span class="decision-blocked">🔴 BLOCKED</span>'
    elif decision == "REVIEW_REQUIRED":
        decision_html = '<span class="decision-review">🟡 REVIEW REQUIRED</span>'
    else:
        decision_html = '<span class="decision-approved">🟢 APPROVED</span>'

    st.markdown(
        f"### Flow Matrix Status &nbsp;&nbsp; {decision_html}", unsafe_allow_html=True
    )
    st.caption(f"Trace ID: {tx['transaction_id']} | State Managed Framework Instance")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        render_ui_card(
            "💳 Transaction Properties",
            {
                "Transaction ID": tx["transaction_id"],
                "Customer ID": tx["customer_id"],
                "Beneficiary ID": tx["beneficiary_id"],
                "Merchant Reference": (
                    tx["merchant_id"] if tx["merchant_id"] else "None (P2P)"
                ),
                "Device Identifier": tx["device_id"],
                "Amount Metric": f"₹{tx['transaction_amount']:,}",
                "Payment Processing": tx["payment_method"],
                "Geographic Flow": f"{tx['origin_country']} ➡️ {tx['destination_country']}",
            },
        )
        render_ui_card(
            "🛡️ Compliance & Core Network Evaluation",
            {
                "Sanction Registry Match": compliance.get("sanction_match", False),
                "PEP Rule Flag": compliance.get("pep_match", False),
                "Network Node Score": network.get("network_score", 0.0),
                "Cohesive Fraud Ring Flag": network.get("fraud_ring_detected", False),
            },
        )

    with col2:
        render_ui_card(
            "📊 Graph Trajectory Metrics",
            {
                "Finalized State Decision": decision,
                "Threat Assessment Class": risk_cat,
                "State Confidence Rating": f"{state.get('confidence_score', 0.0)}",
                "Node Step Iterations": state.get("iteration_count", 0),
                "Report Reference Path": (
                    state.get("report_path")
                    if state.get("report_path")
                    else "Pending Generate"
                ),
            },
        )
        render_ui_card(
            "🤖 Signal Model Scores",
            {
                "Anomaly Engine Weight": anomaly.get("anomaly_score", 0.0),
                "Behavioral Tracking Score": behavioral.get("behavior_score", 0.0),
                "Velocity Context Flag": tx.get("typing_speed_flag", False),
                "Script Execution Flag": tx.get("automation_script_suspected", False),
            },
        )

    st.divider()
    with st.container(border=True):
        st.markdown("##### 🧠 AI Agent Reasoning Context")
        st.write(
            reasoning.get(
                "summary", "No textual reasoning trace attached by evaluation nodes."
            )
        )

    with st.expander("🔧 Inspect Raw InvestigationState Schema Payload"):
        st.json(state)


# =====================================================
# CORE UI LAYOUT (RENDER FIRST!)
# =====================================================
st.title("🚨 Live LangGraph Fraud Investigation Hub")
st.caption("Active Loop Pipeline Model Engine Processing Live Event Payloads")

# Sidebar Controls for streaming
st.sidebar.header("Pipeline Engine Settings")
is_streaming_enabled = st.sidebar.toggle("Enable Live Stream Simulation", value=False)
refresh_speed = st.sidebar.slider(
    "Refresh Interval (seconds)", min_value=5, max_value=30, value=10
)

# Metric counters layout
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Buffer Capacity Status", len(st.session_state.transactions))
with c2:
    st.metric("Total Executed States", st.session_state.total_processed)
with c3:
    st.metric("System Blocked Status", st.session_state.blocked_count)
with c4:
    st.metric("Review Actions Required", st.session_state.review_count)
with c5:
    st.metric("Auto-Approved Clear", st.session_state.approved_count)

st.divider()

st.subheader("📊 Live State Frame Stream")

ledger_data = []
for state in st.session_state.transactions:
    tx = state["transaction"]
    anomaly = state.get("anomaly_result", {})
    behavioral = state.get("behavioral_result", {})
    network = state.get("network_result", {})
    decision_res = state.get("decision_result", {})

    ledger_data.append(
        {
            "Transaction ID": tx["transaction_id"],
            "Customer ID": tx["customer_id"],
            "Transaction Amount": f"₹{tx['transaction_amount']:,}",
            "Graph Score": state.get("confidence_score", 0.0),
            "Anomaly Node": anomaly.get("anomaly_score", 0.0),
            "Behavior Node": behavioral.get("behavior_score", 0.0),
            "Network Node": network.get("network_score", 0.0),
            "State Outcome": decision_res.get("decision", "APPROVED"),
        }
    )

if ledger_data:
    view_dataframe = pd.DataFrame(ledger_data)
    grid_events = st.dataframe(
        view_dataframe,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if grid_events.selection.rows:
        target_index = grid_events.selection.rows[0]
        selected_graph_state = list(st.session_state.transactions)[target_index]
        render_investigation_modal(selected_graph_state)
else:
    st.info(
        "Awaiting state loop invocation... Toggle 'Enable Live Stream Simulation' to begin processing."
    )

# =====================================================
# RUNTIME TICKER LOOP (EVALUATED LAST)
# =====================================================
if is_streaming_enabled:
    refresh_count = st_autorefresh(
        interval=refresh_speed * 1000, key="investigation-state-refresh"
    )

    if refresh_count != st.session_state.last_refresh_count:
        st.session_state.last_refresh_count = refresh_count
        run_live_graph_pipeline()
        st.rerun()