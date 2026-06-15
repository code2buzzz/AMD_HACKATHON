"""
postgres_client.py
Reusable PostgreSQL connection manager
"""

import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()


class PostgresClient:
    def __init__(self):
        
        self.config = {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

    def get_connection(self):
        return psycopg2.connect(**self.config)
