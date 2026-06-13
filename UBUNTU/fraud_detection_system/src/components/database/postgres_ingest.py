"""
postgres_ingest.py

1. Create tables
2. Load CSV data
"""

from pathlib import Path
from psycopg2 import sql

from src.components.database.postgres_client import PostgresClient
from config.settings import TABLE_CREATION_SCHEMA_PATH
from config.settings import INGESTION_PIPELINE


class PostgresIngestor:

    def __init__(
        self,
        csv_dir: str,
        schema_file: str,
    ):
        self.csv_dir = Path(csv_dir)
        self.schema_file = Path(schema_file)
        self.client = PostgresClient()
        self.INGESTION_PIPELINE = INGESTION_PIPELINE

    def create_tables(self):
        with self.client.get_connection() as conn:
            with conn.cursor() as cur:
                with open(TABLE_CREATION_SCHEMA_PATH, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                    cur.execute(sql_script)
                    conn.commit()

        print("Tables created successfully.")

    def _copy_csv(self, cur, table_name: str, csv_path: Path):
        if not csv_path.exists():
            print(f"Missing file: {csv_path}")
            return

        copy_sql = sql.SQL("COPY {} FROM STDIN WITH CSV HEADER").format(
            sql.Identifier(table_name)
        )

        with open(csv_path, "r", encoding="utf-8") as f:
            cur.copy_expert(copy_sql.as_string(cur.connection), f)

    def ingest_data(self):
        with self.client.get_connection() as conn:
            with conn.cursor() as cur:

                print("\nLoading CSV files...\n")

                for table_name, csv_file in self.INGESTION_PIPELINE:
                    print(f"Loading {table_name}...")

                    self._copy_csv(
                        cur,
                        table_name,
                        self.csv_dir / csv_file,
                    )

                    conn.commit()

                    print(f"Loaded {table_name}")

        print("\nSUCCESS - All data loaded.")

    def setup_database(self):
        self.create_tables()
        self.ingest_data()
