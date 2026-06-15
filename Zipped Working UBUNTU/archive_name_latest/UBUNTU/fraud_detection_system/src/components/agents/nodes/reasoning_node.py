import json
import re
from src.components.agents.llms.llm_factory import LLMFactory

llm = LLMFactory.reasoning_llm()

def reasoning_node(state):
    # Fetch and extract raw strings cleanly
    anomaly = state.get('anomaly_result', {})
    behavioral = state.get('behavioral_result', {}).get('analysis', '')
    network = state.get('network_result', {}).get('analysis', '')
    compliance = state.get('compliance_result', {}).get('analysis', '')
    
    current_retries = state.get("graph_retry_count", 0)

    prompt = f"""
    You are the Judge Orchestrator. Synthesize the findings of four sub-specialists and generate a unified risk verdict.

    ### DATA INPUT CHANNELS:
    1. Anomaly Model Matrix: {anomaly}
    2. Behavioral Report: {behavioral}
    3. Network Graph Report: {network}
    4. Compliance Report: {compliance}

    ### INSTRUCTIONS:
    - Assess consensus or conflicts between the modules.
    - Calculate a comprehensive global `confidence` rating (0.00 - 1.00) based on how clearly the findings align. If the agents conflict wildly, reduce your confidence to force a loop retry.
    - Provide a definitive synthesis summary.

    ### OUTPUT COMPLIANCE FORMAT:
    Return ONLY a raw, valid JSON object matching the template below. 
    Do NOT include any introduction, conversational filler, or triple backtick markdown wrappers (```json).

    {{
        "risk": "CRITICAL" / "HIGH" / "MEDIUM" / "LOW",
        "confidence": [Float value between 0.00 and 1.00],
        "summary": "[Your finalized forensic synthesis analysis text]"
    }}
    """

    result = llm.invoke(prompt)
    clean_content = result.content.strip().replace("```json", "").replace("```", "").strip()

    # Dynamic fallback parser to protect your state keys against LLM deviations
    try:
        parsed_json = json.loads(clean_content)
        confidence_score = float(parsed_json.get("confidence", 0.75))
    except Exception:
        # Fallback regex extractor if the model accidentally included text wraps
        print("⚠️ Warning: JSON formatting error encountered in reasoning node. Activating fallback string parser.")
        conf_match = re.search(r'"confidence"\s*:\s*([\d\.]+)', clean_content)
        confidence_score = float(conf_match.group(1)) if conf_match else 0.50
        parsed_json = {
            "risk": "REVIEW",
            "confidence": confidence_score,
            "summary": clean_content
        }

    return {
        "reasoning_result": json.dumps(parsed_json),
        "confidence_score": confidence_score,
        "graph_retry_count": current_retries + 1  # Increment loops inside the graph state channel
    }