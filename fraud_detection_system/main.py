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


def generate_raw_transaction() -> dict:
    customer = random.choice(CUSTOMERS)
    device = random.choice(DEVICES)
    merchant = random.choice(MERCHANTS)
    beneficiary = random.choice(BENEFICIARIES)

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

    if is_fraud and random.random() < 0.7:
        hour_of_day = random.choice([23, 0, 1, 2, 3, 4, 5])
    else:
        hour_of_day = random.randint(0, 23)

    if is_fraud:
        amount = round(float(np.random.lognormal(9.5, 0.5)), 2)
        avg_transaction_amount_7d = round(float(np.random.lognormal(6.8, 0.4)), 2)
    else:
        amount = round(float(np.random.lognormal(6.5, 0.7)), 2)
        avg_transaction_amount_7d = round(amount * random.uniform(0.75, 1.3), 2)

    origin_country = "IN" if not is_fraud else random.choice(COUNTRIES)
    dest_country = (
        random.choice(COUNTRIES) if (is_fraud and random.random() < 0.3) else "IN"
    )
    ip_address = (
        f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
        if not is_fraud
        else f"{random.randint(40,220)}.{random.randint(10,250)}.{random.randint(0,255)}.{random.randint(1,254)}"
    )

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
        session_duration_minutes = random.randint(1, 3)
        device_risk_score = round(random.uniform(85.0, 100.0), 2)
        typing_speed_flag = True
        biometric_anomaly_detected = True
        automation_script_suspected = True
        shared_device_mule_count = random.randint(2, 5)
        known_fraud_ring_edge = random.random() < 0.4
    else:
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

    initial_llm_probability = (
        round(random.uniform(75.0, 99.5), 2)
        if is_fraud
        else round(random.uniform(0.1, 4.5), 2)
    )
    initial_risk_category = "HIGH" if is_fraud else "LOW"
    orchestrator_decision = "REJECT" if is_fraud else "APPROVED"

    sanction_list_match = is_fraud and random.random() < 0.25
    pep_flag = is_fraud and random.random() < 0.1
    beneficiary_risk_rating = (
        "HIGH" if beneficiary in HIGH_RISK_BENEFICIARIES else "LOW"
    )

    return {
        "transaction_id": f"TX_{uuid.uuid4().hex}",
        "customer_id": customer,
        "beneficiary_id": beneficiary,
        "merchant_id": merchant if merchant not in ["None", None] else None,
        "device_id": device,
        "transaction_timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_type": random.choice(["TRANSFER", "PAYMENT"]),
        "transaction_amount": amount,
        "currency": "INR",
        "payment_method": random.choice(PAYMENT_METHODS),
        "ip_address": ip_address,
        "origin_country": origin_country,
        "destination_country": dest_country,
        "transaction_status": "PENDING" if is_fraud else "SUCCESS",
        "is_international": origin_country != dest_country,
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
        "agent_pipelines_telemetry": {
            "initial_llm_probability": initial_llm_probability,
            "initial_risk_category": initial_risk_category,
            "orchestrator_decision": orchestrator_decision,
            "behavioral_agent_context": {
                "biometric_anomaly_detected": biometric_anomaly_detected,
                "automation_script_suspected": automation_script_suspected,
            },
            "graph_agent_context": {
                "shared_device_mule_count": shared_device_mule_count,
                "known_fraud_ring_edge": known_fraud_ring_edge,
            },
            "risk_agent_context": {
                "sanction_list_match": sanction_list_match,
                "pep_flag": pep_flag,
                "beneficiary_risk_rating": beneficiary_risk_rating,
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
