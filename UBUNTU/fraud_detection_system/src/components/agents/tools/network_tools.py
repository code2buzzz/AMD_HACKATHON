import os
import time
from langchain_neo4j import Neo4jGraph
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.components.agents.llms.llm_factory import LLMFactory
from config.settings import NEO4J_CONFIG
from src.components.agents.guardrails.cypher_guardrail import CypherGuardrail

# Initialize components from centralized factory and settings
llm = LLMFactory.graph_llm()

graph = Neo4jGraph(
    url=NEO4J_CONFIG["uri"],
    username=NEO4J_CONFIG["user"],
    password=NEO4J_CONFIG["password"],
)

# -----------------------------------------------------------
# 1. Comprehensive Few-Shot Forensic Examples (10 Patterns)
# -----------------------------------------------------------
few_shot_examples = [
    # -------------------------------------------------
    # BASIC NODE LOOKUPS
    # -------------------------------------------------
    {
        "question": "Find customer C1001.",
        "cypher": """
MATCH (c:Customer {customer_id:'C1001'})
RETURN c
LIMIT 1
""",
    },
    {
        "question": "Find transaction TXN5001.",
        "cypher": """
MATCH (t:Transaction {transaction_id:'TXN5001'})
RETURN t
LIMIT 1
""",
    },
    # -------------------------------------------------
    # CONNECTION COUNTS
    # -------------------------------------------------
    {
        "question": "Count all graph connections for customer C1001.",
        "cypher": """
MATCH (c:Customer {customer_id:'C1001'})
RETURN
    c.customer_id AS customer_id,
    COUNT { (c)--() } AS total_connections
""",
    },
    {
        "question": "Find customers with the highest number of graph connections.",
        "cypher": """
MATCH (c:Customer)
RETURN
    c.customer_id AS customer_id,
    COUNT { (c)--() } AS connection_count
ORDER BY connection_count DESC
LIMIT 10
""",
    },
    # -------------------------------------------------
    # RELATIONSHIP TYPES
    # -------------------------------------------------
    {
        "question": "Show relationship types between customer C1001 and beneficiaries.",
        "cypher": """
MATCH (c:Customer {customer_id:'C1001'})-[r]-(b:Beneficiary)
RETURN
    c.customer_id AS customer_id,
    COLLECT(DISTINCT TYPE(r)) AS relationship_types
""",
    },
    {
        "question": "Show all relationship types in the graph.",
        "cypher": """
MATCH ()-[r]-()
RETURN
    COLLECT(DISTINCT TYPE(r)) AS relationship_types
""",
    },
    {
        "question": "Find all beneficiaries connected to customer C1001 and show relationship types.",
        "cypher": """
MATCH (c:Customer {customer_id:'C1001'})-[r]-(b:Beneficiary)
RETURN
    b.receiver_name AS beneficiary_name,
    TYPE(r) AS relationship_type
""",
    },
    # -------------------------------------------------
    # SHARED DEVICES
    # -------------------------------------------------
    {
        "question": "Find customers sharing the same device as customer C1001.",
        "cypher": """
MATCH (c1:Customer {customer_id:'C1001'})
      -[:HAS_DEVICE]->
      (d:Device)
      <-[:HAS_DEVICE]-
      (c2:Customer)
WHERE c1 <> c2
RETURN
    d.device_id AS shared_device,
    COLLECT(DISTINCT c2.customer_id) AS linked_customers
""",
    },
    {
        "question": "Find devices shared by multiple customers.",
        "cypher": """
MATCH (c:Customer)-[:HAS_DEVICE]->(d:Device)

WITH
    d,
    COUNT(DISTINCT c) AS customer_count,
    COLLECT(DISTINCT c.customer_id) AS customers

WHERE customer_count > 1

RETURN
    d.device_id AS device_id,
    customer_count,
    customers
""",
    },
    # -------------------------------------------------
    # SHARED BENEFICIARIES
    # -------------------------------------------------
    {
        "question": "Find customers connected through shared beneficiaries.",
        "cypher": """
MATCH
(c1:Customer)-[:HAS_BENEFICIARY]->(b:Beneficiary)
<-[:HAS_BENEFICIARY]-
(c2:Customer)

WHERE c1.customer_id < c2.customer_id

RETURN
    c1.customer_id AS customer_1,
    c2.customer_id AS customer_2,
    b.receiver_name AS shared_beneficiary
""",
    },
    {
        "question": "Find beneficiaries shared by more than three customers.",
        "cypher": """
MATCH (c:Customer)-[:HAS_BENEFICIARY]->(b:Beneficiary)

WITH
    b,
    COUNT(DISTINCT c) AS customer_count

WHERE customer_count > 3

RETURN
    b.receiver_name AS beneficiary_name,
    customer_count
""",
    },
    # -------------------------------------------------
    # TRANSACTION PATHS
    # -------------------------------------------------
    {
        "question": "Find transaction path from customer C1001 to beneficiaries.",
        "cypher": """
MATCH p=
(c:Customer {customer_id:'C1001'})
-[:MADE_TRANSACTION]->
(t:Transaction)
-[:TO_BENEFICIARY]->
(b:Beneficiary)

RETURN p
LIMIT 20
""",
    },
    {
        "question": "Find paths between customer C1001 and sanction entities.",
        "cypher": """
MATCH p=
(c:Customer {customer_id:'C1001'})
-[:MADE_TRANSACTION]->
(t:Transaction)
-[:TO_BENEFICIARY]->
(b:Beneficiary)
-[:SANCTION_MATCH]->
(s:SanctionEntity)

RETURN p
LIMIT 20
""",
    },
    # -------------------------------------------------
    # OPTIONAL MATCH
    # -------------------------------------------------
    {
        "question": "Show customer C1001 and any linked sanction entities.",
        "cypher": """
MATCH (c:Customer {customer_id:'C1001'})

OPTIONAL MATCH
(c)-[:HAS_BENEFICIARY]->
(b:Beneficiary)
-[:SANCTION_MATCH]->
(s:SanctionEntity)

RETURN
    c.customer_id AS customer_id,
    COLLECT(DISTINCT s.entity_name) AS sanctions
""",
    },
    # -------------------------------------------------
    # SANCTIONS
    # -------------------------------------------------
    {
        "question": "Find customers linked to sanction entities.",
        "cypher": """
MATCH
(c:Customer)
-[:MADE_TRANSACTION]->
(t:Transaction)
-[:TO_BENEFICIARY]->
(b:Beneficiary)
-[:SANCTION_MATCH]->
(s:SanctionEntity)

RETURN
    c.customer_id AS customer_id,
    b.receiver_name AS beneficiary_name,
    s.entity_name AS sanction_entity
""",
    },
    # -------------------------------------------------
    # DEVICE RISK
    # -------------------------------------------------
    {
        "question": "Find transactions linked to blacklisted devices.",
        "cypher": """
MATCH
(t:Transaction)-[:VIA_DEVICE]->(d:Device)

WHERE d.is_blacklisted = true

RETURN
    t.transaction_id AS transaction_id,
    d.device_id AS device_id,
    t.transaction_amount AS amount
""",
    },
    # -------------------------------------------------
    # TOP RISK TRANSACTIONS
    # -------------------------------------------------
    {
        "question": "Find the highest risk transactions.",
        "cypher": """
MATCH (t:Transaction)

RETURN
    t.transaction_id AS transaction_id,
    t.overall_risk_score AS risk_score,
    t.transaction_amount AS amount

ORDER BY risk_score DESC
LIMIT 20
""",
    },
    # -------------------------------------------------
    # FRAUD RING
    # -------------------------------------------------
    {
        "question": "Identify customers linked through shared devices and beneficiaries.",
        "cypher": """
MATCH
(c1:Customer)-[:HAS_DEVICE]->(d:Device)<-[:HAS_DEVICE]-(c2:Customer)

MATCH
(c1)-[:HAS_BENEFICIARY]->(b:Beneficiary)<-[:HAS_BENEFICIARY]-(c2)

WHERE c1 <> c2

RETURN
    c1.customer_id AS customer_1,
    c2.customer_id AS customer_2,
    d.device_id AS shared_device,
    b.receiver_name AS shared_beneficiary
""",
    },
    # -------------------------------------------------
    # VARIABLE LENGTH PATHS
    # -------------------------------------------------
    {
        "question": "Find customers connected within three hops of customer C1001.",
        "cypher": """
MATCH p=
(c:Customer {customer_id:'C1001'})
-[*1..3]-
(other)

RETURN p
LIMIT 20
""",
    },
    # -------------------------------------------------
    # SUBGRAPH INVESTIGATION
    # -------------------------------------------------
    {
        "question": "Investigate all entities connected to customer C1001.",
        "cypher": """
MATCH
(c:Customer {customer_id:'C1001'})
--(n)

RETURN
    labels(n) AS node_labels,
    COUNT(n) AS connection_count
""",
    },
]

example_prompt = PromptTemplate(
    input_variables=["question", "cypher"],
    template="\nQuestion: {question}\nCypher Query: {cypher}\n",
)

# FIXED: Doubled curly braces around Cypher literal blocks {{ ... }}
prefix = """You are a Neo4j Cypher expert. Given an input question, your job is to write a valid, read-only Neo4j 5.x Cypher query.

Schema:
{schema}

Rules:
- Generate exactly ONE valid Neo4j 5.x Cypher query.
- Return ONLY the executable Cypher query string.
- Do not include markdown, backticks, explanations, comments, or conversational text.
- Never use CREATE, MERGE, DELETE, SET, CALL, APOC, or GDS procedures.
- Use COUNT {{ (n)--() }} instead of SIZE((n)--()).
- All RETURN expressions must be directly executable in Neo4j Browser.

Relationship Rules:
- TYPE() only accepts a relationship variable.

  Correct:
      MATCH (a)-[r]->(b)
      RETURN TYPE(r)

  Incorrect:
      TYPE((a)-[]->(b))

- If relationship information is needed, bind the relationship to a variable first.

  Correct:
      MATCH (a)-[r]->(b)

  Incorrect:
      MATCH (a)-[]->(b)

- Never place node patterns inside:
      TYPE()
      LABELS()
      KEYS()
      PROPERTIES()

- Do not generate anonymous relationships when relationship metadata is required.

Path Rules:
- Use OPTIONAL MATCH when related entities may not exist.
- Prefer LIMIT for path exploration and graph traversal queries.
- Prefer explicit relationship variables whenever relationships are referenced later.

Output Requirements:
- Generate syntactically valid Neo4j 5.x Cypher only.
- Every generated query must be executable without modification.


Common Invalid Patterns (NEVER GENERATE)

Invalid:
    TYPE((c)-[]-(b))

Valid:
    MATCH (c)-[r]-(b)
    RETURN TYPE(r)

Invalid:
    SIZE((c)--())

Valid:
    COUNT {{ (c)--() }}

Invalid:
    MATCH (c)-[]-(b)
    RETURN TYPE(r)

Valid:
    MATCH (c)-[r]-(b)
    RETURN TYPE(r)

Invalid:
    LABELS((c)--(b))

Valid:
    LABELS(c)

Here are examples of correct conversions:"""

cypher_prompt = FewShotPromptTemplate(
    examples=few_shot_examples,
    example_prompt=example_prompt,
    prefix=prefix,
    suffix="\nQuestion: {question}\nCypher Query:",
    input_variables=["schema", "question"],
)

cypher_generation_chain = cypher_prompt | llm | StrOutputParser()


# -----------------------------------------------------------
# 2. Native Agent Tool Export with Context-Enforcing Docstring
# -----------------------------------------------------------
@tool
def query_graph_database(question: str) -> str:
    """
    Executes a read-only natural language query against the graph database to find paths,
    connections, transaction trends, or verify entities.

    CRITICAL INPUT REQUIREMENTS:
    - The input must be a highly explicit, standalone question containing real values.
    - This tool is completely STATELESS and has zero memory of previous conversation turns.
    - Therefore, you MUST NEVER use pronouns or relative phrases like 'this customer', 'their devices',
    'that transaction', or 'the merchant identified above'.
    - You MUST extract the exact ID, hash, or name strings from your previous thoughts or tool outputs
    and place them directly into the text.
    - BAD: "Find transactions for the customer we just discovered"
    - GOOD: "Find transactions for customer_id 'C4920'"
    """

    try:
        current_schema = graph.schema
        generated_cypher = cypher_generation_chain.invoke(
            {"schema": current_schema, "question": question}
        )
        clean_cypher = (
            generated_cypher.replace("```cypher", "").replace("```", "").strip()
        )

        print(f"\n[Generated Cypher]: {clean_cypher}")

        # =======================================================
        # 🛡️ CALL SEPARATED GUARDRAIL GATEWAY
        # =======================================================
        is_safe, message = CypherGuardrail.verify_query_safety(clean_cypher)

        if not is_safe:
            print(f"[SECURITY BLOCK]: {message}")
            return (
                f"Investigation Note: Safety guardrail blocked execution. Reason: {message} "
                "Please rewrite your inquiry using standard read-only investigative questions."
            )
        # =======================================================

        db_result = graph.query(clean_cypher)

        if not db_result:
            return "Investigation Note: No records found in the graph for this query configuration."

        return str(db_result)

    except Exception as e:
        return f"Investigation Note: Query failed to execute. Error: {str(e)}."
