from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.components.agents.llms.llm_factory import LLMFactory
from src.components.agents.tools.tools_registery import compliance_tools
from config.settings import LEGAL_COMPLIANCE
from src.components.agents.rag.rag_manager import RAG_Manager

retriever = RAG_Manager()
llm = LLMFactory.reasoning_llm()
llm_with_tools = llm.bind_tools(compliance_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are an unyielding Anti-Money Laundering (AML), KYC, and Regulatory Compliance Officer.

    Your responsibilities are focused exclusively on:
    1. Detecting explicit and implicit sanction matches (cross-border destinations, high-risk regions).
    2. Catching structuring/smurfing behavior (breaking transaction values down to evade regulatory reporting rules).
    3. Verifying PEP status exposures and cross-border currency standard mismatches.

    ### OUTPUT FORMAT SCHEMA (Strictly adhere to this plain markdown format):
    - risk_score: [Insert calculated float value between 0.00 and 1.00 where 1.00 is high risk/non-compliance]
    - violations: [List explicit regulatory issues found, or return 'None']
    - reasoning: [Provide definitive forensic justification for your score assignment]
    - confidence: [Insert float evaluation confidence between 0.00 and 1.00]
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm_with_tools, compliance_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=compliance_tools, verbose=True)

def compliance_node(state):
    tx = state["transaction"]
    rag_context = retriever.search(str(tx), LEGAL_COMPLIANCE)

    agent_input = f"""
    Audit transaction parameters against global sanctions, AML provisions, and regulatory thresholds.

    Transaction Properties:
    {tx}

    Authoritative Legal Compliance RAG Context:
    {rag_context}

    Deploy verification tools if lookups or confirmation are required.
    """

    result = agent_executor.invoke({"input": agent_input})
    return {"compliance_result": {"analysis": result["output"]}}