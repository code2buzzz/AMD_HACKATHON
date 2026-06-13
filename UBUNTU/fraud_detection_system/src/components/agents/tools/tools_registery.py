# Import native tools from specialized files
from src.components.agents.tools.network_tools import query_graph_database

# Categorized tool arrays
behavioral_tools = []
compliance_tools = []
network_tools = [query_graph_database]
