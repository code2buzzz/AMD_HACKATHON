from langgraph.graph import StateGraph
from langgraph.graph import END

from .state import InvestigationState

from src.components.agents.routers import confidence_router
from src.components.agents.nodes.anomaly_node import anomaly_node
from src.components.agents.nodes.behavioral_node import behavioral_node
from src.components.agents.nodes.network_node import network_node
from src.components.agents.nodes.compliance_node import compliance_node
from src.components.agents.nodes.reasoning_node import reasoning_node
from src.components.agents.nodes.decision_node import decision_node
from src.components.agents.nodes.report_node import report_node


builder = StateGraph(InvestigationState)
builder.add_node("anomaly", anomaly_node)
builder.add_node("behavioral", behavioral_node)
builder.add_node("network", network_node)
builder.add_node("compliance", compliance_node)
builder.add_node("reasoning", reasoning_node)
builder.add_node("decision", decision_node)
builder.add_node("report", report_node)
builder.set_entry_point("anomaly")
builder.add_edge("anomaly", "behavioral")
builder.add_edge("anomaly", "network")
builder.add_edge("anomaly", "compliance")
builder.add_edge("behavioral", "reasoning")
builder.add_edge("network", "reasoning")
builder.add_edge("compliance", "reasoning")
builder.add_conditional_edges("reasoning", confidence_router, {"retry": "behavioral", "approved": "decision"})
builder.add_edge("decision", "report")
builder.add_edge("report", END)

graph = builder.compile()
