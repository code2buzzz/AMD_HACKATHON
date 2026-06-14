import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BankDB Intelligence Center", layout="wide")
st.title("🛡️ BankDB Anti-Fraud Engine Control Center")

FASTAPI_URL = "http://127.0.0.1:8000/api"

active_tab = st.radio(
    "Navigation Window Selection",
    ["🔴 Live Security Matrix Dashboard", "🔍 Historical Logs Deep Investigation"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("---")

# ==========================================
# WINDOW 1: LIVE SECURITY DASHBOARD
# ==========================================
if active_tab == "🔴 Live Security Matrix Dashboard":
    st.header("Real-Time Automated Evaluation Matrix")
    st.caption("Screen updates automatically every 30s.")

    st_autorefresh(interval=30000, key="live_matrix_refresh")

    try:
        tx_response = requests.get(f"{FASTAPI_URL}/transactions/latest")
        kpi_response = requests.get(f"{FASTAPI_URL}/metrics/today")

        if tx_response.status_code == 200 and kpi_response.status_code == 200:
            tx_data = tx_response.json()
            kpis = kpi_response.json()

            st.markdown("### 📊 Today's Cumulative Performance Summary")
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

            kpi_col1.metric("Today's Total Runs", f"{kpis['total_evaluations']:,}")
            kpi_col2.metric(
                "Today's Alerts (Review/Block)", f"{kpis['flagged_or_blocked_count']:,}"
            )
            kpi_col3.metric(
                "Peak Threat Level Today",
                f"{kpis['highest_fraud_probability']:.1f}% Prob",
            )
            kpi_col4.metric(
                "Total Monitored Vol (Today)",
                f"${kpis['total_transacted_volume']:,.2f}",
            )

            st.markdown("---")
            st.markdown("### 📜 Newest Submissions Feed (Top 15 Rows)")

            if tx_data:
                display_df = pd.DataFrame(tx_data).drop(columns=["agent_payloads"])
                st.dataframe(
                    display_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "timestamp": "Evaluation Time",
                        "amount": st.column_config.NumberColumn(
                            "Amount", format="$%.2f"
                        ),
                        "fraud_probability": st.column_config.ProgressColumn(
                            "Fraud Prob", min_value=0, max_value=100, format="%.1f%%"
                        ),
                    },
                    column_order=[
                        "timestamp",
                        "transaction_id",
                        "customer_id",
                        "amount",
                        "currency",
                        "payment_method",
                        "fraud_probability",
                        "overall_risk_score",
                        "risk_category",
                        "decision",
                        "investigation_status",
                    ],
                )
            else:
                st.info("Awaiting transactional evaluations from stream source...")
        else:
            st.error("Engine Core API Connection Interrupted.")
    except requests.exceptions.ConnectionError:
        st.error("Connection Refused. Start your backend services pipeline.")

# ==========================================
# WINDOW 2: HISTORY LOOKUP & DEEP COMPLIANCE INSPECTION
# ==========================================
else:
    st.header("Audit & Search Log Ledger")
    st.caption(
        "Static processing environment. Layout configurations are safe from automated refresh loops."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_cust = st.text_input("Customer ID Match", value="")
    with col2:
        search_risk = st.selectbox(
            "Risk Level Category", options=["All", "Low", "Medium", "High"]
        )
    with col3:
        search_decision = st.selectbox(
            "Pipeline Final Decision", options=["All", "Approve", "Review", "Block"]
        )
    with col4:
        page_size = st.selectbox("Page Size Allocation", options=[10, 25, 50], index=0)

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    active_filters = {
        "cust": search_cust,
        "risk": search_risk,
        "decision": search_decision,
        "size": page_size,
    }

    # Intercept changes and run immediate explicit state resets
    reset_required = False
    for key, current_value in active_filters.items():
        session_key = f"prev_{key}"
        if session_key not in st.session_state:
            st.session_state[session_key] = current_value
        elif st.session_state[session_key] != current_value:
            reset_required = True
            st.session_state[session_key] = current_value

    if reset_required:
        st.session_state.current_page = 1
        st.rerun()  # Instantly re-evaluates the view layout

    params = {
        "page": st.session_state.current_page,
        "page_size": page_size,
        "customer_id": search_cust,
        "risk_category": search_risk,
        "decision": search_decision,
    }

    try:
        search_res = requests.get(f"{FASTAPI_URL}/transactions/search", params=params)
        if search_res.status_code == 200:
            payload = search_res.json()
            total_pages = payload.get("total_pages", 1)
            total_records = payload.get("total", 0)
            table_data = payload.get("data", [])

            st.markdown(
                f"Query returned **{total_records}** records matched across centralized ledger index lines."
            )

            if table_data:
                df_search = pd.DataFrame(table_data)
                st.dataframe(
                    df_search.drop(columns=["agent_payloads"]),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "timestamp": "Evaluation Time",
                        "amount": st.column_config.NumberColumn(
                            "Amount", format="$%.2f"
                        ),
                        "fraud_probability": st.column_config.ProgressColumn(
                            "Fraud Prob", min_value=0, max_value=100, format="%.1f%%"
                        ),
                    },
                )

                st.markdown("### 🔬 Multi-Agent Telemetry Explorer")
                target_tx = st.selectbox(
                    "Select unique transaction record to trace evaluation paths:",
                    options=df_search["transaction_id"].unique(),
                )

                if target_tx:
                    selected_rows = df_search[df_search["transaction_id"] == target_tx]
                    if not selected_rows.empty:
                        selected_row = selected_rows.iloc[0]
                        payload_map = selected_row.get("agent_payloads", {})

                        agent_cols = st.columns(5)
                        with agent_cols[0]:
                            with st.expander("Anomaly Agent Output"):
                                st.json(payload_map.get("anomaly_engine") or {})
                        with agent_cols[1]:
                            with st.expander("Behavioral Agent Output"):
                                st.json(payload_map.get("behavioral_engine") or {})
                        with agent_cols[2]:
                            with st.expander("Network Graph Output"):
                                st.json(payload_map.get("network_graph_engine") or {})
                        with agent_cols[3]:
                            with st.expander("Compliance Agent Output"):
                                st.json(payload_map.get("compliance_engine") or {})
                        with agent_cols[4]:
                            with st.expander("Reasoning Agent Output"):
                                st.json(payload_map.get("reasoning_engine") or {})
            else:
                st.warning("No records found matching the current filters.")

            st.markdown("---")
            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])

            with p_col1:
                if st.button("⬅️ Previous Page") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()

            with p_col2:
                st.markdown(
                    f"<p style='text-align: center;'>Viewing page <b>{st.session_state.current_page}</b> of <b>{total_pages}</b></p>",
                    unsafe_allow_html=True,
                )

            with p_col3:
                if (
                    st.button("Next Page ➡️")
                    and st.session_state.current_page < total_pages
                ):
                    st.session_state.current_page += 1
                    st.rerun()
        else:
            st.error("Query Execution Fault processing server-side analytics filters.")
    except requests.exceptions.ConnectionError:
        st.error("Engine telemetry service pipeline offline.")
