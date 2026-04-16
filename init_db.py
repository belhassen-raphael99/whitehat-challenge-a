"""
Initialize the SQLite database from schema.sql.

Usage:
    python init_db.py

Idempotent: safe to run multiple times (CREATE TABLE IF NOT EXISTS).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    schema_sql = SCHEMA_PATH.read_text()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    print(f"OK Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
