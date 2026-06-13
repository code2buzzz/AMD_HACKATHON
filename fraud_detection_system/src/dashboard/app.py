import streamlit as st
import pandas as pd
import random
from collections import deque
from streamlit_autorefresh import st_autorefresh

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Fraud Investigation Dashboard",
    page_icon="🚨",
    layout="wide",
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown(
    """
<style>

.block-container {
    padding-top: 1.5rem;
}

[data-testid="stMetric"] {
    border: 1px solid rgba(255,255,255,0.08);
    padding: 12px;
    border-radius: 12px;
}

.info-card {
    background: linear-gradient(
        145deg,
        rgba(17,24,39,0.95),
        rgba(31,41,55,0.95)
    );
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 14px;
}

.kv-row {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:8px 0;
    border-bottom:1px solid rgba(255,255,255,0.05);
}

.kv-row:last-child {
    border-bottom:none;
}

.kv-key {
    color:#9CA3AF;
}

.kv-value {
    font-weight:600;
}

.decision-approved {
    color:#22c55e;
    font-weight:700;
}

.decision-review {
    color:#f59e0b;
    font-weight:700;
}

.decision-blocked {
    color:#ef4444;
    font-weight:700;
}

</style>
""",
    unsafe_allow_html=True,
)

# =====================================================
# CONFIG
# =====================================================

MAX_ROWS = 10

# =====================================================
# SESSION STATE
# =====================================================

if "transactions" not in st.session_state:
    st.session_state.transactions = deque(maxlen=MAX_ROWS)

if "transaction_counter" not in st.session_state:
    st.session_state.transaction_counter = 1000

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
# AUTO REFRESH
# =====================================================

refresh_count = st_autorefresh(interval=30000, key="fraud-refresh")


# =====================================================
# FAKE STATE GENERATOR
# =====================================================
def card(title, values):

    with st.container(border=True):

        st.subheader(title)

        for key, value in values.items():

            left, right = st.columns([1, 2])

            left.markdown(
                f"<span style='color:#9CA3AF'>{key}</span>",
                unsafe_allow_html=True,
            )

            right.markdown(f"**{value}**")


def generate_state():

    st.session_state.transaction_counter += 1
    st.session_state.total_processed += 1

    tx_id = f"TXN{st.session_state.transaction_counter}"

    risk_score = round(random.uniform(0, 1), 2)

    if risk_score > 0.75:
        decision = "BLOCKED"
        risk_cat = "HIGH"
        st.session_state.blocked_count += 1

    elif risk_score > 0.40:
        decision = "REVIEW_REQUIRED"
        risk_cat = "MEDIUM"
        st.session_state.review_count += 1

    else:
        decision = "APPROVED"
        risk_cat = "LOW"
        st.session_state.approved_count += 1

    state = {
        "transaction": {
            "transaction_id": tx_id,
            "customer_id": f"CUST{random.randint(100,999)}",
            "beneficiary_id": f"BEN{random.randint(1,50)}",
            "merchant_id": f"MER{random.randint(100,999)}",
            "device_id": f"DEV{random.randint(1,20)}",
            "transaction_amount": random.randint(1000, 50000),
            "currency": "INR",
            "transaction_type": "PAYMENT",
        },
        "anomaly_result": {"anomaly_score": round(random.uniform(0, 1), 2)},
        "behavioral_result": {"behavior_score": round(random.uniform(0, 1), 2)},
        "network_result": {
            "network_score": round(random.uniform(0, 1), 2),
            "fraud_ring_detected": random.choice([True, False]),
        },
        "compliance_result": {
            "sanction_match": False,
            "pep_match": False,
        },
        "reasoning_result": {"summary": "Transaction evaluated by agent pipeline."},
        "decision_result": {
            "decision": decision,
            "risk_category": risk_cat,
        },
        "report_path": None,
        "iteration_count": 1,
        "confidence_score": risk_score,
        "messages": [
            "Anomaly Agent Completed",
            "Behavior Agent Completed",
            "Network Agent Completed",
        ],
    }

    return state


# =====================================================
# ADD NEW TRANSACTION ONLY ON TIMER REFRESH
# =====================================================

if refresh_count != st.session_state.last_refresh_count:

    st.session_state.last_refresh_count = refresh_count

    new_state = generate_state()

    st.session_state.transactions.appendleft(new_state)

# =====================================================
# MODAL
# =====================================================


@st.dialog("🔍 Fraud Investigation", width="large")
def show_modal(state):

    tx = state["transaction"]

    decision = state["decision_result"]["decision"]
    risk_category = state["decision_result"]["risk_category"]

    if decision == "BLOCKED":
        decision_html = '<span class="decision-blocked">🔴 BLOCKED</span>'
    elif decision == "REVIEW_REQUIRED":
        decision_html = '<span class="decision-review">🟡 REVIEW REQUIRED</span>'
    else:
        decision_html = '<span class="decision-approved">🟢 APPROVED</span>'

    st.markdown(
        f"""
        <h2>
            Investigation Summary
            &nbsp;&nbsp;
            {decision_html}
        </h2>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # ====================================
    # LEFT COLUMN
    # ====================================

    with col1:

        card(
            "💳 Transaction Overview",
            {
                "Transaction ID": tx["transaction_id"],
                "Customer ID": tx["customer_id"],
                "Beneficiary": tx["beneficiary_id"],
                "Merchant": tx["merchant_id"],
                "Device": tx["device_id"],
                "Amount": f"₹{tx['transaction_amount']:,}",
                "Currency": tx["currency"],
                "Type": tx["transaction_type"],
            },
        )

        card(
            "🛡 Compliance Analysis",
            {
                "Sanction Match": state["compliance_result"]["sanction_match"],
                "PEP Match": state["compliance_result"]["pep_match"],
            },
        )

    # ====================================
    # RIGHT COLUMN
    # ====================================

    with col2:

        card(
            "📊 Risk Assessment",
            {
                "Decision": decision,
                "Risk Category": risk_category,
                "Confidence Score": state["confidence_score"],
                "Iterations": state["iteration_count"],
            },
        )

        card(
            "🤖 Agent Analysis",
            {
                "Anomaly Score": state["anomaly_result"]["anomaly_score"],
                "Behavior Score": state["behavioral_result"]["behavior_score"],
                "Network Score": state["network_result"]["network_score"],
                "Fraud Ring": state["network_result"]["fraud_ring_detected"],
            },
        )

    st.divider()

    card(
        "🧠 Investigation Reasoning",
        {"Summary": state["reasoning_result"]["summary"]},
    )

    # with st.expander("🔧 Raw Investigation State"):
    #     st.json(state)


# =====================================================
# HEADER
# =====================================================

st.title("🚨 Real-Time Fraud Investigation Dashboard")

st.caption("Simulated Kafka Stream → LangGraph Processing → Live Investigation Feed")

# =====================================================
# BUILD TABLE
# =====================================================

rows = []

for state in st.session_state.transactions:

    tx = state["transaction"]

    rows.append(
        {
            "Transaction ID": tx["transaction_id"],
            "Customer": tx["customer_id"],
            "Amount": f"₹{tx['transaction_amount']:,}",
            "Risk Score": state["confidence_score"],
            "Anomaly": state["anomaly_result"]["anomaly_score"],
            "Behavior": state["behavioral_result"]["behavior_score"],
            "Network": state["network_result"]["network_score"],
            "Decision": state["decision_result"]["decision"],
        }
    )

df = pd.DataFrame(rows)

# =====================================================
# KPI ROW
# =====================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("Visible Transactions", len(st.session_state.transactions))

with c2:
    st.metric("Total Processed", st.session_state.total_processed)

with c3:
    st.metric("Blocked", st.session_state.blocked_count)

with c4:
    st.metric("Review", st.session_state.review_count)

with c5:
    st.metric("Approved", st.session_state.approved_count)

st.divider()

# =====================================================
# TABLE
# =====================================================

st.subheader("📊 Live Investigation Feed")

event = st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

# =====================================================
# OPEN MODAL
# =====================================================

if event.selection.rows:

    idx = event.selection.rows[0]

    selected_state = list(st.session_state.transactions)[idx]

    show_modal(selected_state)

# =====================================================
# FOOTER
# =====================================================

st.caption(
    f"Showing latest {MAX_ROWS} investigations. "
    f"Total processed: {st.session_state.total_processed}"
)
