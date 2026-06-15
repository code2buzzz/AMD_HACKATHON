from ..llms.llm_factory import LLMFactory

llm = LLMFactory.reasoning_llm()


def reasoning_node(state):

    prompt = f"""
    Combine findings.

    Anomaly:
    {state['anomaly_result']}

    Behavioral:
    {state['behavioral_result']}

    Network:
    {state['network_result']}

    Compliance:
    {state['compliance_result']}

    Return JSON:

    {{
        "risk":"HIGH",
        "confidence":0.91,
        "summary":"..."
    }}
    """

    result = llm.invoke(prompt)

    return {
        "reasoning_result": result.content,
        "confidence_score": 0.91,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
