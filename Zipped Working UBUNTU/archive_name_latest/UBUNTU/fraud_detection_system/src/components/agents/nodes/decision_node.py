import json

def guardrail_check(parsed_report):
    """Evaluates systemic conditions to check authorization status."""
    risk_level = parsed_report.get("risk", "MEDIUM")
    confidence = parsed_report.get("confidence", 0.0)
    
    # Block transactions that hit high-risk categories with definitive certainty
    if risk_level in ["HIGH", "CRITICAL"] and confidence > 0.80:
        return {"approved": False, "action": "BLOCK_TRANSACTION"}
        
    return {"approved": True, "action": "ALLOW_TRANSACTION"}

def decision_node(state):
    raw_report = state["reasoning_result"]
    
    try:
        parsed_report = json.loads(raw_report)
    except Exception:
        parsed_report = {"risk": "HIGH", "confidence": 0.90, "summary": raw_report}
        
    validation = guardrail_check(parsed_report)
    
    return {
        "decision_result": {
            "approved": validation["approved"],
            "system_action": validation["action"],
            "report": raw_report
        }
    }