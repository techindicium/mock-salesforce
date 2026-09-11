from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from pydantic import ValidationError

from mock_salesforce.db import get_db_path
from mock_salesforce.models import AccountCreate, ContactCreate, LeadCreate, OpportunityCreate

CLOSED_STAGES = {"Closed Won", "Closed Lost"}


class SeedDataError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

SEED_ACCOUNTS: list[dict] = [
    {"name": "Marchetti Construction", "account_type": "Customer",
     "industry": "Construction", "billing_country": "Portugal"},
    {"name": "Ferreira Padarias", "account_type": "Customer",
     "industry": "Food and Beverage", "billing_country": "Brazil"},
    {"name": "Hollis Veterinary Group", "account_type": "Customer",
     "industry": "Veterinary Services", "billing_country": "United States"},
    {"name": "Atlantic Marine Supplies", "account_type": "Customer",
     "industry": "Wholesale", "billing_country": "Portugal"},
    {"name": "Cafe Nordeste", "account_type": "Customer",
     "industry": "Hospitality", "billing_country": "Brazil"},
    {"name": "Vaz e Filhos Transportes", "account_type": "Customer",
     "industry": "Transport", "billing_country": "Brazil"},
    {"name": "Clinica Dental Aurora", "account_type": "Customer",
     "industry": "Dental Practice", "billing_country": "Portugal"},
    {"name": "Bright Path Tutoring", "account_type": "Customer",
     "industry": "Education", "billing_country": "United States"},
    {"name": "Studio Lumen", "account_type": "Customer",
     "industry": "Design Services", "billing_country": "Netherlands"},
    {"name": "Oliveira Serralharia", "account_type": "Customer",
     "industry": "Manufacturing", "billing_country": "Brazil"},
]


SEED_CONTACTS: list[dict] = [
    # People at the customer, not Portwell's own staff. The roles a firm of two to thirty
    # people actually has: whoever signs and whoever does the books.
    {"account_name": "Marchetti Construction", "first_name": "Nuno", "last_name": "Marchetti",
     "title": "Owner", "email": "nuno.marchetti@marchetticonstruction.example"},
    {"account_name": "Marchetti Construction", "first_name": "Sara", "last_name": "Lopes",
     "title": "Bookkeeper", "email": "sara.lopes@marchetticonstruction.example"},
    {"account_name": "Ferreira Padarias", "first_name": "Beatriz", "last_name": "Nunes",
     "title": "Gerente de Operações", "email": "beatriz.nunes@ferreirapadarias.example"},
    {"account_name": "Hollis Veterinary Group", "first_name": "Megan", "last_name": "Hollis",
     "title": "Practice Manager", "email": "megan.hollis@hollisveterinarygroup.example"},
    {"account_name": "Atlantic Marine Supplies", "first_name": "Marcus", "last_name": "Webb",
     "title": "Office Manager", "email": "marcus.webb@atlanticmarinesupplies.example"},
    {"account_name": "Vaz e Filhos Transportes", "first_name": "Rafael", "last_name": "Vaz",
     "title": "Owner", "email": "rafael.vaz@vazefilhostransportes.example"},
    {"account_name": "Bright Path Tutoring", "first_name": "Grace", "last_name": "Okonkwo",
     "title": "Founder", "email": "grace.okonkwo@brightpathtutoring.example"},
    {"account_name": "Bright Path Tutoring", "first_name": "Peter", "last_name": "Hallam",
     "title": "Bookkeeper", "email": "peter.hallam@brightpathtutoring.example"},
    # Cafe Nordeste, Clinica Dental Aurora, Studio Lumen and Oliveira Serralharia have nobody
    # named. Small accounts, self-serve onboarding, and nobody ever filled the CRM in.
]


# One renewal per account, spanning all ten stages, so a consumer sees the whole enum. The
# amount is the plan's monthly price over twelve months: this is a subscription book, and
# there is nothing else to sell a customer who already has an account.
SEED_OPPORTUNITIES: list[dict] = [
    {"account_name": "Marchetti Construction", "name": "Marchetti Construction renewal 2026",
     "stage_name": "Prospecting", "amount": 1788, "close_date": "2026-01-28",
     "probability": 10, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Confirm who signs now that the second site was added"},
    {"account_name": "Ferreira Padarias", "name": "Ferreira Padarias renewal 2026",
     "stage_name": "Qualification", "amount": 1788, "close_date": "2026-02-28",
     "probability": 30, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Account is restricted; renewal conversation is on hold until it is lifted"},
    {"account_name": "Hollis Veterinary Group", "name": "Hollis Veterinary Group renewal 2026",
     "stage_name": "Needs Analysis", "amount": 1788, "close_date": "2026-03-28",
     "probability": 40, "opportunity_type": "Existing Business", "lead_source": "Partner Referral",
     "next_step": "Asked for expense cards across all four practices"},
    {"account_name": "Atlantic Marine Supplies", "name": "Atlantic Marine Supplies renewal 2026",
     "stage_name": "Value Proposition", "amount": 588, "close_date": "2026-04-28",
     "probability": 35, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Comparing the credit line against their current overdraft"},
    {"account_name": "Cafe Nordeste", "name": "Cafe Nordeste renewal 2026",
     "stage_name": "Id. Decision Makers", "amount": 588, "close_date": "2026-05-28",
     "probability": 45, "opportunity_type": "Existing Business", "lead_source": "Phone Inquiry",
     "next_step": "Two of the six shops are franchised; unclear who holds the contract"},
    {"account_name": "Vaz e Filhos Transportes", "name": "Vaz e Filhos Transportes renewal 2026",
     "stage_name": "Perception Analysis", "amount": 588, "close_date": "2026-06-28",
     "probability": 45, "opportunity_type": "Existing Business", "lead_source": "Phone Inquiry",
     "next_step": "Unhappy about a fee dispute still open from June"},
    {"account_name": "Clinica Dental Aurora", "name": "Clinica Dental Aurora renewal 2026",
     "stage_name": "Proposal/Price Quote", "amount": 228, "close_date": "2026-07-28",
     "probability": 60, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Quote sent for the Business plan"},
    {"account_name": "Bright Path Tutoring", "name": "Bright Path Tutoring renewal 2026",
     "stage_name": "Negotiation/Review", "amount": 228, "close_date": "2026-08-28",
     "probability": 80, "opportunity_type": "Existing Business", "lead_source": "Web",
     "next_step": "Wants the statement export their accountant asked for"},
    {"account_name": "Studio Lumen", "name": "Studio Lumen renewal 2026",
     "stage_name": "Closed Won", "amount": 0, "close_date": "2026-09-28",
     "probability": 100, "opportunity_type": "Existing Business", "lead_source": "Other",
     "next_step": "Stays on the grandfathered Free plan for another year"},
    {"account_name": "Oliveira Serralharia", "name": "Oliveira Serralharia renewal 2026",
     "stage_name": "Closed Lost", "amount": 0, "close_date": "2026-10-28",
     "probability": 0, "opportunity_type": "Existing Business", "lead_source": "Other",
     "next_step": "Declined to move off the Free plan. Still a customer, still paying nothing."},
]


# Prospects, not customers. Small firms that asked about a business account and have not
# opened one, which is why none of them carries an ACCOUNT-NNNN.
SEED_LEADS: list[dict] = [
    {"first_name": "Cristina", "last_name": "Meireles", "company": "Meireles Contabilidade",
     "title": "Owner", "email": "cristina.meireles@meirelescontabilidade.example",
     "lead_source": "Web", "status": "New", "rating": "Warm"},
    {"first_name": "Dev", "last_name": "Reddy", "company": "Reddy and Hall Architects",
     "title": "Practice Manager", "email": "dev.reddy@reddyandhall.example",
     "lead_source": "Partner Referral", "status": "Contacted", "rating": "Hot"},
    {"first_name": "Ines", "last_name": "Coelho", "company": "Coelho Floristas",
     "title": "Owner", "email": "ines.coelho@coelhofloristas.example",
     "lead_source": "Phone Inquiry", "status": "New", "rating": "Cold"},
    {"first_name": "Tomas", "last_name": "Berg", "company": "Bergstrom Fysio",
     "title": "Founder", "email": "tomas.berg@bergstromfysio.example",
     "lead_source": "Web", "status": "Qualified", "rating": "Hot"},
    {"first_name": "Aline", "last_name": "Dubois", "company": "Atelier Dubois",
     "title": "Office Manager", "email": "aline.dubois@atelierdubois.example",
     "lead_source": "Other", "status": "Unqualified", "rating": "Cold"},
]


def _insert_lead(conn: sqlite3.Connection, row: dict, now: str) -> int:
    try:
        payload = LeadCreate(**row)
    except ValidationError as exc:
        raise SeedDataError(
            "SEED_DATA_INVALID",
            f"Lead row '{row.get('last_name', '<unknown>')}' failed validation: {exc}",
        ) from exc
    cur = conn.execute(
        """
        INSERT INTO leads (
            first_name, last_name, company, title, email, phone,
            lead_source, status, rating, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.first_name, payload.last_name, payload.company, payload.title,
            payload.email, payload.phone, payload.lead_source, payload.status,
            payload.rating, now, now,
        ),
    )
    return cur.lastrowid


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
    leads: list[dict] | None = None,
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
    leads = SEED_LEADS if leads is None else leads
    now = datetime.now(timezone.utc).isoformat()
    account_ids: dict[str, int] = {}
    try:
        for row in accounts:
            account_ids[row["name"]] = _insert_account(conn, row, now)
        for row in contacts:
            _insert_contact(conn, row, account_ids[row["account_name"]], now)
        for row in opportunities:
            _insert_opportunity(conn, row, account_ids[row["account_name"]], now)
        for row in leads:
            _insert_lead(conn, row, now)
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise SeedDataError(
            "SEED_DB_NOT_WRITABLE", f"Database path '{get_db_path()}' is not writable: {exc}"
        ) from exc
