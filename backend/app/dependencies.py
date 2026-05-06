import os
from collections.abc import Generator
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import Connection

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url


def get_db_connection() -> Generator[Connection, None, None]:
    connection = psycopg.connect(get_database_url())
    # Registra suporte a vetores no psycopg
    import pgvector.psycopg
    pgvector.psycopg.register_vector(connection)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
