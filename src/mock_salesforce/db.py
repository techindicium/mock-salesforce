import os
import sqlite3
from pathlib import Path


def get_db_path() -> str:
    return os.environ.get("DB_PATH", "mock_salesforce.db")


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    parent = Path(db_path).parent
    # NOTE: os.access(parent, os.W_OK) is best-effort only. On Linux, a process
    # running as root bypasses the permission bits entirely, so this check
    # always reports "writable" for a root-run process regardless of the
    # directory's actual mode. That is the default for the Docker images this
    # feature packages (no non-root USER is set), so this guard does not
    # protect against permission problems in that environment.
    if str(parent) and (not parent.exists() or not os.access(parent, os.W_OK)):
        raise RuntimeError(
            f"[DEPLOY_VOLUME_NOT_WRITABLE] Cannot write to directory '{parent}' for "
            f"DB_PATH='{db_path}'. Check the volume mount is writable."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- The account's identifier in the systems that own it. Salesforce keeps its own
            -- integer primary key and carries the other system's key alongside, which is how
            -- a real CRM is integrated.
            external_id TEXT UNIQUE,
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            name TEXT NOT NULL,
            stage_name TEXT NOT NULL,
            amount REAL,
            close_date TEXT NOT NULL,
            probability REAL,
            opportunity_type TEXT,
            lead_source TEXT,
            next_step TEXT,
            is_closed INTEGER NOT NULL,
            is_won INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def dependent_count(conn: sqlite3.Connection, account_id: int) -> int:
    count = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE account_id = ?", (account_id,)
    ).fetchone()[0]
    opportunities_table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='opportunities'"
    ).fetchone()
    if opportunities_table_exists:
        count += conn.execute(
            "SELECT COUNT(*) FROM opportunities WHERE account_id = ?", (account_id,)
        ).fetchone()[0]
    return count
