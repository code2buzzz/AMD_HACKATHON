from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.components.agents.llms.llm_factory import LLMFactory
from src.components.agents.tools.tools_registery import behavioral_tools
from config.settings import BEHAVIORAL_ANOMALIES
from src.components.agents.rag.rag_manager import RAG_Manager

retriever = RAG_Manager()
llm = LLMFactory.behavioral_llm()
llm_with_tools = llm.bind_tools(behavioral_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a cold, analytical Fraud Detection Behavioral Agent specializing in session telemetry, velocity metrics, and human-interaction profiles.

    Your task is to analyze the transaction profile against the provided historical baseline context.
    
    ### CRITICAL ANALYSIS CRITERIA:
    1. Compare session navigation duration, typing flags, and biometric telemetry.
    2. Review velocity risk (e.g., failed transaction counts over 24h, spikes against 7-day transaction averages).
    3. Cross-reference anomalies with the historical indicators provided in the RAG Context.

    ### OUTPUT FORMAT SCHEMA (Strictly adhere to this plain markdown format):
    - score: [Insert calculated float value between 0.00 and 1.00 where 1.00 is highest fraud risk]
    - reasoning: [Provide a precise paragraph summarizing findings and context matching]
    - confidence: [Insert float evaluation confidence between 0.00 and 1.00]
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm_with_tools, behavioral_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=behavioral_tools, verbose=True)

def behavioral_node(state):
    tx = state["transaction"]
    retries = state.get("graph_retry_count", 0)
    
    rag_context = retriever.search(str(tx), BEHAVIORAL_ANOMALIES)

    # Inform the agent if it is executing a self-correction retry loop
    retry_context_alert = ""
    if retries > 0:
        retry_context_alert = f"\n⚠️ SELF-CORRECTION ALERT: This is loop retry pass #{retries}. Your previous confidence score was rejected by the reasoning node. Deepen your tool analysis and find hidden discrepancies."

    agent_input = f"""
    Analyze behavioral fraud indicators.{retry_context_alert}

    Transaction Data:
    {tx}

    Authoritative Historical Behavioral RAG Context:
    {rag_context}

    Utilize execution tools if additional behavioral validation or verification is required.
    """

    result = agent_executor.invoke({"input": agent_input})
    return {"behavioral_result": {"analysis": result["output"]}}