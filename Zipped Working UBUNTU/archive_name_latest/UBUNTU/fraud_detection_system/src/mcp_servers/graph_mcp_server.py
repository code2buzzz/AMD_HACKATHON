from fastmcp import FastMCP
import random

mcp = FastMCP("Graph Fraud MCP Server")


# ----------------------------
# Dummy graph dataset
# ----------------------------
GRAPH_DB = {
    "A": ["B", "C", "D"],
    "B": ["A", "E", "F"],
    "C": ["A", "G"],
    "D": ["A", "H"],
    "E": ["B", "I"],
    "F": ["B"],
    "G": ["C", "J"],
}


# ----------------------------
# 1. Get neighbors
# ----------------------------
@mcp.tool
def get_neighbors(node_id: str):
    """
    Returns direct connections of a node.
    """
    return {"node": node_id, "neighbors": GRAPH_DB.get(node_id, [])}


# ----------------------------
# 2. Fraud ring detection (dummy logic)
# ----------------------------
@mcp.tool
def detect_fraud_ring(node_id: str):
    """
    Fake fraud ring detection based on connectivity.
    """
    neighbors = GRAPH_DB.get(node_id, [])

    cluster_size = len(neighbors) + random.randint(1, 5)
    risk_score = min(1.0, cluster_size / 10)

    return {
        "node": node_id,
        "cluster_size": cluster_size,
        "risk_score": risk_score,
        "flagged": risk_score > 0.6,
    }


# ----------------------------
# 3. Multi-hop traversal
# ----------------------------
@mcp.tool
def traverse_network(node_id: str, depth: int = 2):
    """
    Expands network up to N hops.
    """
    visited = set()
    frontier = [node_id]
    result = []

    for _ in range(depth):
        next_frontier = []
        for node in frontier:
            if node in visited:
                continue
            visited.add(node)

            neighbors = GRAPH_DB.get(node, [])
            result.append({"node": node, "neighbors": neighbors})
            next_frontier.extend(neighbors)

        frontier = next_frontier

    return {"start_node": node_id, "depth": depth, "graph": result}


# ----------------------------
# 4. Simple risk scoring
# ----------------------------
@mcp.tool
def compute_risk_score(node_id: str):
    """
    Dummy risk scoring based on connectivity.
    """
    neighbors = GRAPH_DB.get(node_id, [])

    score = len(neighbors) * 0.2 + random.uniform(0, 0.3)

    score = min(1.0, round(score, 2))

    return {
        "node": node_id,
        "risk_score": score,
        "risk_level": "HIGH" if score > 0.6 else "MEDIUM" if score > 0.3 else "LOW",
    }


# ----------------------------
# Run MCP server
# ----------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
