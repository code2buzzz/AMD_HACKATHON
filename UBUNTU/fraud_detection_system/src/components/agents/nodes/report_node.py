from pathlib import Path
from datetime import datetime

REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(exist_ok=True)


def report_node(state):

    tx_id = state["transaction"]["transaction_id"]

    file_name = REPORT_DIR / f"{tx_id}.txt"

    content = f"""
    FRAUD INVESTIGATION REPORT

    Transaction:
    {state['transaction']}

    Behavioral:
    {state['behavioral_result']}

    Network:
    {state['network_result']}

    Compliance:
    {state['compliance_result']}

    Decision:
    {state['decision_result']}
    """

    file_name.write_text(content, encoding="utf-8")

    return {"report_result": {"report_path": str(file_name)}}
