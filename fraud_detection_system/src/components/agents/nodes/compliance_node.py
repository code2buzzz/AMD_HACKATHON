from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.components.agents.llms.llm_factory import LLMFactory
from src.components.agents.tools.tools_registery import compliance_tools
from config.settings import LEGAL_COMPLIANCE
from src.components.agents.rag.rag_manager import RAG_Manager

# RAG Retriever
retriever = RAG_Manager()

# ----------------------------
# LLM (tool-enabled)
# ----------------------------
llm = LLMFactory.reasoning_llm()
llm_with_tools = llm.bind_tools(compliance_tools)


# ----------------------------
# Prompt
# ----------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
        You are a compliance and AML investigation agent.

        Your responsibilities:
        - Detect sanctions risks
        - Identify AML violations
        - Check regulatory compliance issues

        You MUST use the provided RAG context as authoritative compliance knowledge.
        You may also use tools for additional verification.

        Output format:
        - risk_score (0-1)
        - violations
        - reasoning
        - confidence
        """,
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


# ----------------------------
# Agent
# ----------------------------
agent = create_tool_calling_agent(llm_with_tools, compliance_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=compliance_tools, verbose=True)


# ----------------------------
# NODE FUNCTION
# ----------------------------
def compliance_node(state):
    tx = state["transaction"]

    rag_context = retriever.search(str(tx), LEGAL_COMPLIANCE)

    result = agent_executor.invoke({"input": f"""
        Check sanctions, AML, and regulatory concerns.

        Transaction:
        {tx}

        RAG CONTEXT (authoritative compliance knowledge):
        {rag_context}

        Use tools if additional compliance verification is required.
        """})

    return {"compliance_result": {"analysis": result["output"]}}
