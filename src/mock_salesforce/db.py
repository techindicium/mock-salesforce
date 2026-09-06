import os
import sqlite3


def get_db_path() -> str:
    return os.environ.get("DB_PATH", "mock_salesforce.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_type TEXT,
            industry TEXT,
            website TEXT,
            phone TEXT,
            billing_street TEXT,
            billing_city TEXT,
            billing_state TEXT,
            billing_postal_code TEXT,
            billing_country TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            first_name TEXT,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            title TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
