from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from pydantic import ValidationError

from mock_salesforce.db import get_db_path
from mock_salesforce.models import AccountCreate, ContactCreate, OpportunityCreate

CLOSED_STAGES = {"Closed Won", "Closed Lost"}


class SeedDataError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

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


SEED_OPPORTUNITIES: list[dict] = [
    {"account_name": "Nordkai Logistics", "name": "Nordkai Logistics - Integrations Expansion",
     "stage_name": "Negotiation/Review", "amount": 185000, "close_date": "2026-11-15",
     "probability": 80, "opportunity_type": "Existing Business", "lead_source": "Partner Referral",
     "next_step": "Finalize integrations SOW ahead of Q4 renewal; webhook-retry behavior "
                  "revisited after INCIDENT-02 (read-only reference, not owned by this API)"},
    {"account_name": "Tavares Distribuicao", "name": "Tavares Distribuicao - Cycle Count Rollout",
     "stage_name": "Closed Won", "amount": 42000, "close_date": "2026-05-20",
     "probability": 100, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Kickoff scheduled"},
    {"account_name": "Halden Cold Chain", "name": "Halden Cold Chain - Billing Module Add-on",
     "stage_name": "Proposal/Price Quote", "amount": 96000, "close_date": "2026-12-01",
     "probability": 60, "opportunity_type": "Existing Business", "lead_source": "Phone Inquiry",
     "next_step": "Awaiting signed quote"},
    {"account_name": "Brightpath Freight", "name": "Brightpath Freight - Billing Seats Expansion",
     "stage_name": "Qualification", "amount": 31000, "close_date": "2026-12-20",
     "probability": 30, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Confirm budget owner"},
    {"account_name": "Meseta Almacenes", "name": "Meseta Almacenes - Picking Optimization",
     "stage_name": "Prospecting", "amount": 15000, "close_date": "2027-01-31",
     "probability": 10, "opportunity_type": "New Business", "lead_source": "Web",
     "next_step": "Initial discovery call"},
    {"account_name": "Kestrel Parts Group", "name": "Kestrel Parts Group - Integrations Renewal",
     "stage_name": "Closed Lost", "amount": 54000, "close_date": "2026-04-30",
     "probability": 0, "opportunity_type": "Existing Business", "lead_source": "Partner Referral",
     "next_step": "Lost to competitor at renewal"},
    {"account_name": "Vlietwerk BV", "name": "Vlietwerk BV - Picking Seat Increase",
     "stage_name": "Needs Analysis", "amount": 9000, "close_date": "2026-12-10",
     "probability": 25, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Review current seat utilization"},
    {"account_name": "Sunder Retail Supply", "name": "Sunder Retail Supply - Cycle Count Expansion",
     "stage_name": "Id. Decision Makers", "amount": 210000, "close_date": "2027-02-15",
     "probability": 40, "opportunity_type": "New Business", "lead_source": "Partner Referral",
     "next_step": "Map procurement stakeholders"},
    {"account_name": "Copal Andina", "name": "Copal Andina - Receiving Module Upsell",
     "stage_name": "Perception Analysis", "amount": 28000, "close_date": "2026-12-05",
     "probability": 45, "opportunity_type": "Existing Business", "lead_source": "Phone Inquiry",
     "next_step": "Assess technical fit"},
    {"account_name": "Fjordline Depot", "name": "Fjordline Depot - Putaway Module Trial",
     "stage_name": "Value Proposition", "amount": 6000, "close_date": "2027-01-15",
     "probability": 35, "opportunity_type": "New Business", "lead_source": "Other",
     "next_step": "Draft trial success criteria"},
]


def _insert_account(conn: sqlite3.Connection, row: dict, now: str) -> int:
    try:
        payload = AccountCreate(**row)
    except ValidationError as exc:
        raise SeedDataError(
            "SEED_DATA_INVALID",
            f"Account row '{row.get('name', '<unknown>')}' failed validation: {exc}",
        ) from exc
    cur = conn.execute(
        """
        INSERT INTO accounts (
            external_id, name, account_type, industry, website, phone,
            billing_street, billing_city, billing_state,
            billing_postal_code, billing_country, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.external_id,
            payload.name, payload.account_type, payload.industry, payload.website,
            payload.phone, payload.billing_street, payload.billing_city,
            payload.billing_state, payload.billing_postal_code, payload.billing_country,
            now, now,
        ),
    )
    return cur.lastrowid


def _insert_contact(conn: sqlite3.Connection, row: dict, account_id: int, now: str) -> int:
    fields = {k: v for k, v in row.items() if k != "account_name"}
    try:
        payload = ContactCreate(account_id=account_id, **fields)
    except ValidationError as exc:
        raise SeedDataError(
            "SEED_DATA_INVALID",
            f"Contact row '{row.get('last_name', '<unknown>')}' failed validation: {exc}",
        ) from exc
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


def _insert_opportunity(conn: sqlite3.Connection, row: dict, account_id: int, now: str) -> int:
    fields = {k: v for k, v in row.items() if k != "account_name"}
    try:
        payload = OpportunityCreate(account_id=account_id, **fields)
    except ValidationError as exc:
        raise SeedDataError(
            "SEED_DATA_INVALID",
            f"Opportunity row '{row.get('name', '<unknown>')}' failed validation: {exc}",
        ) from exc
    is_closed = payload.stage_name in CLOSED_STAGES
    is_won = payload.stage_name == "Closed Won"
    cur = conn.execute(
        """
        INSERT INTO opportunities (
            account_id, name, stage_name, amount, close_date, probability,
            opportunity_type, lead_source, next_step, is_closed, is_won,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.account_id, payload.name, payload.stage_name, payload.amount,
            payload.close_date.isoformat(), payload.probability, payload.opportunity_type,
            payload.lead_source, payload.next_step, int(is_closed), int(is_won), now, now,
        ),
    )
    return cur.lastrowid


_FIXTURE = Path(__file__).parent / "fixtures" / "seed.json"


def _load_fixture() -> dict | None:
    """The generated seed, when it has been written into this repo.

    Written here at authoring time by the shared seed generator and committed, so nothing
    outside this repository is opened at runtime. The fixture's own banner names the generator.
    The literals above remain the fallback, which keeps this repo standing alone if the fixture
    is ever absent.
    """
    if not _FIXTURE.exists():
        return None
    data = json.loads(_FIXTURE.read_text())
    by_external = {a["external_id"]: a for a in data["accounts"]}

    accounts = [
        {
            "external_id": a["external_id"],
            "name": a["name"],
            "account_type": a["account_type"],
            "industry": a["industry"],
            "billing_country": _COUNTRY_BY_REGION.get(a["region"]),
        }
        for a in data["accounts"]
    ]
    contacts = [
        {
            "account_name": by_external[c["account_external_id"]]["name"],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "email": c["email"],
            "title": c["title"],
        }
        for c in data["contacts"]
    ]
    opportunities = [
        {
            "account_name": by_external[o["account_external_id"]]["name"],
            "name": o["name"],
            "stage_name": o["stage_name"],
            "amount": o["amount"],
            "close_date": o["close_date"],
            "opportunity_type": o["opportunity_type"],
        }
        for o in data["opportunities"]
    ]
    return {"accounts": accounts, "contacts": contacts, "opportunities": opportunities}


# The canon records a region; a CRM records a country. One per region is enough here.
_COUNTRY_BY_REGION = {"EU": "Germany", "NA": "United States", "LATAM": "Brazil"}


def seed_if_empty(
    conn: sqlite3.Connection,
    accounts: list[dict] | None = None,
    contacts: list[dict] | None = None,
    opportunities: list[dict] | None = None,
) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    if existing > 0:
        return
    fixture = _load_fixture() if accounts is None else None
    if fixture is not None:
        accounts, contacts, opportunities = (
            fixture["accounts"], fixture["contacts"], fixture["opportunities"],
        )
    accounts = SEED_ACCOUNTS if accounts is None else accounts
    contacts = SEED_CONTACTS if contacts is None else contacts
    opportunities = SEED_OPPORTUNITIES if opportunities is None else opportunities
    now = datetime.now(timezone.utc).isoformat()
    account_ids: dict[str, int] = {}
    try:
        for row in accounts:
            account_ids[row["name"]] = _insert_account(conn, row, now)
        for row in contacts:
            _insert_contact(conn, row, account_ids[row["account_name"]], now)
        for row in opportunities:
            _insert_opportunity(conn, row, account_ids[row["account_name"]], now)
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise SeedDataError(
            "SEED_DB_NOT_WRITABLE", f"Database path '{get_db_path()}' is not writable: {exc}"
        ) from exc
