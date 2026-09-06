from datetime import datetime, timezone
import sqlite3

from mock_salesforce.models import AccountCreate, ContactCreate

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


SEED_CONTACTS: list[dict] = [
    {"account_name": "Nordkai Logistics", "first_name": "Ana", "last_name": "Fialho",
     "title": "VP Product", "email": "ana.fialho@nordkailogistics.com"},
    {"account_name": "Nordkai Logistics", "first_name": "Joao", "last_name": "Pinto",
     "title": "Support Engineer", "email": "joao.pinto@nordkailogistics.com"},
    {"account_name": "Halden Cold Chain", "first_name": "Priya", "last_name": "Nair",
     "title": "Solution Consultant", "email": "priya.nair@haldencoldchain.com"},
    {"account_name": "Sunder Retail Supply", "first_name": "Gabriela", "last_name": "Rocha",
     "title": "Customer Success Director", "email": "gabriela.rocha@sunderretailsupply.com"},
    {"account_name": "Brightpath Freight", "first_name": "Rui", "last_name": "Bastos",
     "title": "Support Manager", "email": "rui.bastos@brightpathfreight.com"},
    {"account_name": "Kestrel Parts Group", "first_name": "Mei", "last_name": "Tan",
     "title": "Head of Engineering", "email": "mei.tan@kestrelpartsgroup.com"},
    {"account_name": "Tavares Distribuicao", "first_name": "Sofia", "last_name": "Marques",
     "title": "Analytics Lead", "email": "sofia.marques@tavaresdistribuicao.com"},
    {"account_name": "Meseta Almacenes", "first_name": "Lucia", "last_name": "Ferreira",
     "title": "Service Delivery Manager", "email": "lucia.ferreira@mesetaalmacenes.com"},
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


def _insert_contact(conn: sqlite3.Connection, row: dict, account_id: int, now: str) -> int:
    fields = {k: v for k, v in row.items() if k != "account_name"}
    payload = ContactCreate(account_id=account_id, **fields)
    cur = conn.execute(
        """
        INSERT INTO contacts (
            account_id, first_name, last_name, email, phone, title, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.account_id, payload.first_name, payload.last_name, payload.email,
            payload.phone, payload.title, now, now,
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

    for row in SEED_CONTACTS:
        _insert_contact(conn, row, account_ids[row["account_name"]], now)

    conn.commit()
