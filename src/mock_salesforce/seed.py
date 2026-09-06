from datetime import datetime, timezone
import sqlite3

from mock_salesforce.models import AccountCreate

SEED_ACCOUNTS: list[dict] = [
    {"name": "Nordkai Logistics", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Germany"},
    {"name": "Tavares Distribuicao", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Brazil"},
    {"name": "Halden Cold Chain", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Sweden"},
    {"name": "Brightpath Freight", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "United States"},
    {"name": "Meseta Almacenes", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Mexico"},
    {"name": "Kestrel Parts Group", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "United States"},
    {"name": "Vlietwerk BV", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Netherlands"},
    {"name": "Sunder Retail Supply", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "United States"},
    {"name": "Copal Andina", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Peru"},
    {"name": "Fjordline Depot", "account_type": "Customer",
     "industry": "Logistics and Supply Chain", "billing_country": "Denmark"},
]


def _insert_account(conn: sqlite3.Connection, row: dict, now: str) -> int:
    payload = AccountCreate(**row)
    cur = conn.execute(
        """
        INSERT INTO accounts (
            name, account_type, industry, website, phone,
            billing_street, billing_city, billing_state,
            billing_postal_code, billing_country, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name, payload.account_type, payload.industry, payload.website,
            payload.phone, payload.billing_street, payload.billing_city,
            payload.billing_state, payload.billing_postal_code, payload.billing_country,
            now, now,
        ),
    )
    return cur.lastrowid


def seed_if_empty(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    if existing > 0:
        return
    now = datetime.now(timezone.utc).isoformat()
    account_ids: dict[str, int] = {}
    for row in SEED_ACCOUNTS:
        account_ids[row["name"]] = _insert_account(conn, row, now)
    conn.commit()
