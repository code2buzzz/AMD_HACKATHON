from pathlib import Path

PROJECT_ROOT = Path("fraud_detection_system")

directories = [
    "config",
    "data/raw",
    "data/synthetic",
    "data/sql",
    "deploy",
    "models/artifacts",
    "storage/chroma_storage",
    "src",
    "src/components",
    "src/components/data_gen",
    "src/components/database",
    "src/components/streaming",
    "src/components/models",
    "src/components/rag",
    "src/components/agents",
    "src/components/agents/nodes",
    "src/components/agents/tools",
    "src/dashboard",
    "src/mcp_servers",
]

files = [
    "config/.env",
    "config/settings.py",
    "data/sql/create_tables.sql",
    "data/sql/drop_tables.sql",
    "deploy/docker-compose.yaml",
    "src/__init__.py",
    "src/main.py",
    "src/components/__init__.py",
    "src/components/data_gen/__init__.py",
    "src/components/data_gen/generator.py",
    "src/components/database/__init__.py",
    "src/components/database/postgres_client.py",
    "src/components/database/neo4j_client.py",
    "src/components/database/postgres_ingest.py",
    "src/components/database/neo4j_ingest.py",
    "src/components/streaming/__init__.py",
    "src/components/streaming/producer.py",
    "src/components/streaming/consumer.py",
    "src/components/models/__init__.py",
    "src/components/models/predictor.py",
    "src/components/rag/__init__.py",
    "src/components/rag/ingestion.py",
    "src/components/rag/retriever.py",
    "src/components/agents/__init__.py",
    "src/components/agents/state.py",
    "src/components/agents/graph.py",
    "src/components/agents/nodes/__init__.py",
    "src/components/agents/nodes/anomaly_node.py",
    "src/components/agents/nodes/behavioral_node.py",
    "src/components/agents/nodes/network_node.py",
    "src/components/agents/nodes/compliance_node.py",
    "src/components/agents/tools/__init__.py",
    "src/components/agents/tools/graph_tools.py",
    "src/components/agents/tools/rag_tools.py",
    "src/dashboard/__init__.py",
    "src/dashboard/app.py",
    "src/dashboard/visuals.py",
    "src/mcp_servers/__init__.py",
    "src/mcp_servers/guardrail_server.py",
    "src/mcp_servers/graph_retriever_server.py",
]

# Create directories
for directory in directories:
    (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)

# Create files
for file_path in files:
    full_path = PROJECT_ROOT / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if not full_path.exists():
        full_path.touch()

print(f"Project structure created successfully at: {PROJECT_ROOT.resolve()}")
