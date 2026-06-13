from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.components.agents.llms.llm_factory import LLMFactory
from src.components.agents.tools.tools_registery import network_tools
from config.settings import NETWORK_TYPOLOGIES
from src.components.agents.rag.rag_manager import RAG_Manager

# RAG Retriever
retriever = RAG_Manager()

# ----------------------------
# 1. LLM Configuration & Tool Binding
# ----------------------------
llm = LLMFactory.graph_llm()
llm_with_tools = llm.bind_tools(network_tools)


# ----------------------------
# 2. System Prompt & Multi-Step Reasoning Guardrails
# ----------------------------
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
        You are an expert forensic network analyst and graph reasoning agent. Your job is to uncover structural fraud patterns, hidden rings, connection anomalies, and entity exposures.

        You MUST use the provided RAG context as structural domain reference data.

        CRITICAL WORKFLOW RULES FOR INVESTIGATION:
        1. Always analyze the outputs of your previous tool calls before formulating the next step.
        2. Your graph database tool is completely STATELESS. It does not remember past turns.
        3. Therefore, your tool questions MUST be explicit, standalone queries.
        4. NEVER pass pronouns or relative descriptions to the tool (e.g., 'this customer', 'their transaction', 'the device from earlier').
        5. ALWAYS extract precise ID strings or hashes from past steps and embed them explicitly (e.g., query_graph_database(question="Find transactions for customer_id 'C1002'")).
        6. Keep investigating iteratively until you have completely resolved all analytical blind spots.

        Output format:
        - network_risk_score (0 to 1)
        - mapped_connections_summary (entities and links discovered)
        - forensic_reasoning
        - confidence_level
        """,
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


# ----------------------------
# 3. Agent Execution Engine
# ----------------------------
agent = create_tool_calling_agent(llm_with_tools, network_tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=network_tools,
    verbose=True,
    max_iterations=10,  # Safe loop limit for nested investigations [make it 5 in prod]
    early_stopping_method="force",  # Ensures stability within your state graph runtime
)


# ----------------------------
# 4. Graph State Node Function
# ----------------------------
def network_node(state):
    tx = state["transaction"]

    # 1. Execute RAG step to fetch topology hints or typologies
    rag_context = retriever.search(str(tx), NETWORK_TYPOLOGIES)

    # 2. Execute the iterative tool-calling investigation loop
    result = agent_executor.invoke({"input": f"""
        Analyze network and relationship fraud indicators for this transaction.

        Transaction under Investigation:
        {tx}

        RAG CONTEXT (must use this as network history and topology guidelines):
        {rag_context}

        Use your graph database query tool to deep-dive into shared entities, 
        sanction linkages, or multi-hop connection paths if necessary.
        """})

    # 3. Return the payload cleanly formatted for your network state channel
    return {"network_result": {"analysis": result["output"]}}
