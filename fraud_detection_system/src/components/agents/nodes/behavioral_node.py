from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.components.agents.llms.llm_factory import LLMFactory
from src.components.agents.tools.tools_registery import behavioral_tools
from config.settings import BEHAVIORAL_ANOMALIES
from src.components.agents.rag.rag_manager import RAG_Manager

# RAG Retriever
retriever = RAG_Manager()


# ----------------------------
# LLM (tool enabled)
# ----------------------------
llm = LLMFactory.behavioral_llm()
llm_with_tools = llm.bind_tools(behavioral_tools)


# ----------------------------
# Prompt
# ----------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
        You are a fraud detection reasoning agent.

        You MUST use the provided RAG context as factual behavioral history.

        You may also use tools for additional investigation.

        Output format:
        - score (0 to 1)
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
agent = create_tool_calling_agent(llm_with_tools, behavioral_tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=behavioral_tools, verbose=True)


# ----------------------------
# NODE FUNCTION
# ----------------------------
def behavioral_node(state):
    tx = state["transaction"]

    # RAG step (mandatory)
    rag_context = retriever.search(str(tx), BEHAVIORAL_ANOMALIES)

    result = agent_executor.invoke({"input": f"""
        Analyze behavioral fraud indicators.

        Transaction:
        {tx}

        RAG CONTEXT (must use this as behavioral history):
        {rag_context}

        Use tools if additional behavioral investigation is required.
        """})

    return {"behavioral_result": {"analysis": result["output"]}}
