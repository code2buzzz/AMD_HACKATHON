from typing import TypedDict, Dict, Any, List, Optional


class InvestigationState(TypedDict):
    transaction: Dict[str, Any]
    anomaly_result: Dict[str, Any]
    behavioral_result: Dict[str, Any]
    network_result: Dict[str, Any]
    compliance_result: Dict[str, Any]
    reasoning_result: Dict[str, Any]
    decision_result: Dict[str, Any]
    report_path: Optional[str]
    iteration_count: int
    confidence_score: float
    messages: List[str]
