<!-- partial_schema: plan@1 -->

# Implementation Plan: Fixture Seed Data

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-api/charter.md
> **Spec:** .context-index/specs/features/crm-api/fixture-seeding.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`require_review: false`
>   for all risk tiers in this repo's `governance/risk-policies.yaml`); treated as a clean pass.
> **Platform:** Python 3.11, FastAPI 0.141.1, SQLite (stdlib `sqlite3`, no ORM), no auth, runs
>   locally only

**Goal:** Seed a fresh (empty) database with the ten canonical `course-shared/canon/company.md`
accounts, at least six of its Named People as Contacts across four-plus accounts, and at least
one Opportunity per account spanning five-plus `stage_name` values (including one `Closed Won`
and one `Closed Lost`) — hardcoded into this repo, reconciled with canon once at authoring time,
never read from `../course-shared` at runtime.

**Architecture:** A new `src/mock_salesforce/seed.py` module owns three hardcoded data constants
(`SEED_ACCOUNTS`, `SEED_CONTACTS`, `SEED_OPPORTUNITIES`) and one function, `seed_if_empty(conn,
...)`, called once from `app.py`'s existing `on_startup` handler right after `init_db(conn)`.
Idempotency (BEH-4) is a single guard: `SELECT COUNT(*) FROM accounts` — if non-zero, return
immediately. Each phase (accounts → contacts → opportunities) reuses the existing
`AccountCreate`/`ContactCreate`/`OpportunityCreate` Pydantic models to validate a row before its
raw-SQL `INSERT`, mirroring `accounts.py`/`opportunities.py`'s own insert shape exactly — no ORM,
no new dependency. Contacts and Opportunities reference their parent Account by name (not a
hardcoded id) via an `account_ids: dict[str, int]` map built from the just-inserted Account rows'
`cur.lastrowid`, so seeded ids are whatever SQLite's `AUTOINCREMENT` assigns — plain integers,
never the canon `ACCOUNT-NNNN`/`TICKET-NNNNNN`/`POLICY-NN` schemes (BEH-5, true by construction,
plus an explicit regression test). `seed_if_empty` accepts optional `accounts=`/`contacts=`/
`opportunities=` override parameters (defaulting to the module constants) purely for test
injection of the Error Cases paths — production code always calls it with no arguments. A new
`SeedDataError(code, message)` exception (raised for `SEED_DATA_INVALID` on a
`pydantic.ValidationError` and `SEED_DB_NOT_WRITABLE` on a `sqlite3.OperationalError`) is added in
the final task, once all three insert phases exist to wrap. Work happens on a new branch
`feat/crm-api/fixture-seeding`, branched from the already-merged
`feat/crm-api/account-contact-scaffolding` work (Account/Contact/Opportunity CRUD are already
implemented and validated).

---

## File Structure

**Create:**
- `src/mock_salesforce/seed.py` — `SEED_ACCOUNTS`/`SEED_CONTACTS`/`SEED_OPPORTUNITIES` constants,
  `SeedDataError`, `seed_if_empty(conn, ...)`
- `tests/test_seed_accounts.py` — BEH-1 suite (Task 1)
- `tests/test_seed_contacts.py` — BEH-2 suite (Task 2)
- `tests/test_seed_opportunities.py` — BEH-3 suite (Task 3)
- `tests/test_seed_idempotency.py` — BEH-4 suite (Task 4)
- `tests/test_seed_ids.py` — BEH-5 suite (Task 5)

**Modify:**
- `src/mock_salesforce/app.py` — call `seed_if_empty(conn)` in `on_startup`, right after
  `init_db(conn)` and before `conn.close()`

**Reference (read, do not modify):**
- `src/mock_salesforce/accounts.py` — `create_account`'s insert shape (column list, `now`
  timestamp, `cur.lastrowid` re-select) — `seed.py`'s account insert mirrors this line for line
- `src/mock_salesforce/opportunities.py` — `_derive_closed_won` logic (`is_closed`/`is_won` from
  `stage_name`); `seed.py` re-derives the same two booleans locally rather than importing this
  module's private helper across module boundaries
- `src/mock_salesforce/models.py` — `AccountCreate`, `ContactCreate`, `OpportunityCreate` (used to
  validate each hardcoded row before insert)
- `src/mock_salesforce/db.py` — `get_db_path()`, `get_connection()` (used in the
  `SEED_DB_NOT_WRITABLE` error message and by tests)
- `../course-shared/canon/company.md` — Accounts table (10 rows) and Named People table (12
  rows); the sole source for every seeded name/tier/region/role — read once, at plan-authoring
  time, never by the running program
- `.context-index/specs/features/crm-api/charter.md` — Capability Map ("Seed fixture data" row)
- `.context-index/specs/features/crm-api/fixture-seeding.spec.md` — full Behavioral Contract,
  Error Cases table
- `.context-index/specs/features/crm-api/opportunity-lifecycle.plan.md` — sibling plan; this plan
  mirrors its task granularity and TDD step format

## Context Packets

No source-manifest exists yet on this spec (its Behavioral Contract has not been implemented) —
packets fall back to charter Capability Map, the spec's own Behavioral Contract sections, and the
already-implemented sibling modules as pattern references.

### Task 1 Context
- Spec: Preconditions (reconciliation happens once, at authoring time; Account entity is a
  distinct integer-id space from canon's `ACCOUNT-NNNN`); BEH-1; Error Cases row
  `SEED_DATA_INVALID` (accounts phase only)
- Charter: Capability Map → "Seed fixture data" row
- Canon: `../course-shared/canon/company.md` Accounts table (10 rows: name, tier, region)
- Reference: `src/mock_salesforce/accounts.py` (`create_account`'s insert-then-reselect pattern);
  `src/mock_salesforce/models.py` (`AccountCreate`)

### Task 2 Context
- Spec: BEH-2
- Canon: `../course-shared/canon/company.md` Named People table (12 rows: name, role)
- Reference: `src/mock_salesforce/contacts.py` (`create_contact`'s column list and
  `ContactCreate` shape)

### Task 3 Context
- Spec: BEH-3; Postconditions (seeded `next_step` may narratively mention canon entities by real
  id, e.g. `INCIDENT-01`, as read-only references, but this module never creates/owns/exposes an
  endpoint for any canon-owned entity type)
- Reference: `src/mock_salesforce/opportunities.py` (`_derive_closed_won`, `OpportunityCreate`
  column list including `close_date.isoformat()`)

### Task 4 Context
- Spec: BEH-4; Postconditions (`GET /accounts` returns exactly ten Accounts after a fresh-database
  startup; `GET /contacts`/`GET /opportunities` return the seeded rows)
- Reference: `src/mock_salesforce/app.py` (existing `on_startup` handler — `init_db(conn)` then
  `conn.close()`); `tests/conftest.py` (`client` fixture — `DB_PATH` env var, `TestClient`
  context-manager triggers `on_startup`)

### Task 5 Context
- Spec: BEH-5; Error Cases table (both rows: `SEED_DATA_INVALID`, `SEED_DB_NOT_WRITABLE`)
- Canon: `../course-shared/canon/identifiers.md` — reserved schemes table (`ACCOUNT-NNNN`,
  `TICKET-NNNNNN`, `POLICY-NN`, etc.) that seeded ids must never collide with
- Reference: `src/mock_salesforce/errors.py` (`error_body(code, message)` shape — `SeedDataError`
  follows the same `{error, message}` vocabulary even though it is raised at startup, not from an
  HTTP handler)

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5

Every task extends the same `seed_if_empty` function in the same new `seed.py` file (Task 2 and
Task 3 both build on Task 1's account-insert scaffold and `account_ids` map; Task 4 wires the
function Tasks 1-3 completed; Task 5 wraps all three phases). There is no independent file group
to run alongside Group A.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Seed the ten canonical Accounts (BEH-1) | medium | unit | — | 2 create, 0 modify |
| 2 | Seed Named People as Contacts (BEH-2) | medium | unit | Task 1 | 1 create, 1 modify |
| 3 | Seed Opportunities across the ten stages (BEH-3) | medium | unit | Task 1 | 1 create, 1 modify |
| 4 | Wire seeding into startup, idempotently (BEH-4) | small | unit | Task 1, Task 2, Task 3 | 1 create, 1 modify |
| 5 | Wrap seed errors + assert id-scheme disjointness (BEH-5) | small | unit | Task 1, Task 2, Task 3, Task 4 | 1 create, 1 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no matching `manifest.yaml` `test_strategies` entry, and file paths under
`src/mock_salesforce/**` / `tests/**` don't match any non-unit auto-detection heuristic). No
Strategy Summary or Test Infrastructure Requirements section follows, per the omission rule for
all-unit plans with no `infra_requirements:` in the spec.

Granularity is resolved once for the whole plan: `test_policy.granularity: per-behavior` in
`manifest.yaml` (source: manifest — no module-level override exists for `crm-api`). Per this
policy, each of the five behaviors (BEH-1 through BEH-5) gets its own suite path, created once by
the task that first implements it; no later task in this plan re-touches an earlier behavior's
suite, so every `**Tests:**` field below reads "create," not "extend."

No heuristics matched module `crm-api` at plan time (`adev heuristics retrieve` returned
`__NONE__`) — no Heuristics section follows.

## Task Structure

> Per-task `- [ ]` checkboxes are authoring guides only; authoritative task state lives in the
> spec's lifecycle event log (`plan_task` events), not in this markdown. No `Status` column
> appears in any task table in this plan.

### Task 1: Seed the ten canonical Accounts (BEH-1) [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `src/mock_salesforce/seed.py`
- Create (test): `tests/test_seed_accounts.py`

**Tests:** `tests/test_seed_accounts.py` — create (BEH-1)

**Context to load:**
- Spec: BEH-1, Preconditions
- Canon: `../course-shared/canon/company.md` Accounts table
- Reference: `src/mock_salesforce/accounts.py` (`create_account` insert shape),
  `src/mock_salesforce/models.py` (`AccountCreate`)

- [ ] **Write failing test**

```python
# tests/test_seed_accounts.py
from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import SEED_ACCOUNTS, seed_if_empty

EXPECTED_NAMES = {
    "Nordkai Logistics", "Tavares Distribuicao", "Halden Cold Chain",
    "Brightpath Freight", "Meseta Almacenes", "Kestrel Parts Group",
    "Vlietwerk BV", "Sunder Retail Supply", "Copal Andina", "Fjordline Depot",
}


def test_seed_if_empty_seeds_ten_canonical_accounts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    conn.close()
    assert len(rows) == 10
    assert {r["name"] for r in rows} == EXPECTED_NAMES
    for row in rows:
        assert row["industry"] == "Logistics and Supply Chain"
        assert row["billing_country"]  # non-empty, no placeholder
        assert row["billing_country"] not in ("TBD", "Lorem", "")


def test_seed_accounts_constant_has_ten_rows_with_valid_countries():
    assert len(SEED_ACCOUNTS) == 10
    eu_countries = {"Germany", "Sweden", "Netherlands", "Denmark"}
    na_countries = {"United States"}
    latam_countries = {"Brazil", "Mexico", "Peru"}
    real_countries = eu_countries | na_countries | latam_countries
    for row in SEED_ACCOUNTS:
        assert row["billing_country"] in real_countries
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_seed_accounts.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mock_salesforce.seed'`

- [ ] **Implement**

```python
# src/mock_salesforce/seed.py
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
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_seed_accounts.py`
Expected: PASS

- [ ] **Commit**

Branch (create): `feat/crm-api/fixture-seeding`

```bash
git checkout -b feat/crm-api/fixture-seeding
git add src/mock_salesforce/seed.py tests/test_seed_accounts.py
git commit -m "feat(crm-api): seed the ten canonical accounts on empty database"
```

---

### Task 2: Seed Named People as Contacts (BEH-2) [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `src/mock_salesforce/seed.py`
- Create (test): `tests/test_seed_contacts.py`

**Tests:** `tests/test_seed_contacts.py` — create (BEH-2)

**Context to load:**
- Spec: BEH-2
- Canon: `../course-shared/canon/company.md` Named People table
- Reference: `src/mock_salesforce/contacts.py` (`create_contact` column list),
  `src/mock_salesforce/models.py` (`ContactCreate`)

- [ ] **Write failing test**

```python
# tests/test_seed_contacts.py
from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import seed_if_empty


def test_seed_if_empty_seeds_named_people_as_contacts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    contacts = conn.execute("SELECT * FROM contacts").fetchall()
    accounts = {r["id"]: r["name"] for r in conn.execute("SELECT * FROM accounts").fetchall()}
    conn.close()

    assert len(contacts) >= 6
    distinct_accounts = {c["account_id"] for c in contacts}
    assert len(distinct_accounts) >= 4
    assert distinct_accounts.issubset(accounts.keys())
    for c in contacts:
        assert c["last_name"]  # never an invented placeholder name
        assert c["title"]      # plausible title derived from canon role
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_seed_contacts.py`
Expected: FAIL — `sqlite3.OperationalError` or `AssertionError: 0 >= 6` (no contacts inserted yet)

- [ ] **Implement**

Add to `src/mock_salesforce/seed.py`:

```python
from mock_salesforce.models import ContactCreate

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
```

Extend `seed_if_empty` (still in `src/mock_salesforce/seed.py`) to call `_insert_contact` for
each `SEED_CONTACTS` row, right after the account loop and before `conn.commit()`:

```python
    for row in SEED_CONTACTS:
        _insert_contact(conn, row, account_ids[row["account_name"]], now)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_seed_contacts.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/crm-api/fixture-seeding`

```bash
git add src/mock_salesforce/seed.py tests/test_seed_contacts.py
git commit -m "feat(crm-api): seed named people as contacts across four+ accounts"
```

---

### Task 3: Seed Opportunities across the ten stages (BEH-3) [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `src/mock_salesforce/seed.py`
- Create (test): `tests/test_seed_opportunities.py`

**Tests:** `tests/test_seed_opportunities.py` — create (BEH-3)

**Context to load:**
- Spec: BEH-3, Postconditions (narrative canon references allowed in `next_step`)
- Reference: `src/mock_salesforce/opportunities.py` (`_derive_closed_won`,
  `OpportunityCreate.close_date.isoformat()`)

- [ ] **Write failing test**

```python
# tests/test_seed_opportunities.py
from mock_salesforce.db import get_connection, init_db
from mock_salesforce.seed import seed_if_empty


def test_seed_if_empty_seeds_opportunities_across_ten_stages(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    accounts = conn.execute("SELECT id FROM accounts").fetchall()
    opps = conn.execute("SELECT * FROM opportunities").fetchall()
    conn.close()

    account_ids = {a["id"] for a in accounts}
    opp_account_ids = {o["account_id"] for o in opps}
    assert account_ids.issubset(opp_account_ids)  # at least one Opportunity per Account

    stages = {o["stage_name"] for o in opps}
    assert len(stages) >= 5
    assert "Closed Won" in stages
    assert "Closed Lost" in stages

    for o in opps:
        expect_closed = o["stage_name"] in ("Closed Won", "Closed Lost")
        assert bool(o["is_closed"]) == expect_closed
        assert bool(o["is_won"]) == (o["stage_name"] == "Closed Won")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_seed_opportunities.py`
Expected: FAIL — `AssertionError` (no opportunities inserted yet, `opp_account_ids` is empty)

- [ ] **Implement**

Add to `src/mock_salesforce/seed.py`:

```python
from mock_salesforce.models import OpportunityCreate

CLOSED_STAGES = {"Closed Won", "Closed Lost"}

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


def _insert_opportunity(conn: sqlite3.Connection, row: dict, account_id: int, now: str) -> int:
    fields = {k: v for k, v in row.items() if k != "account_name"}
    payload = OpportunityCreate(account_id=account_id, **fields)
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
```

Extend `seed_if_empty` to call `_insert_opportunity` for each `SEED_OPPORTUNITIES` row, after the
contacts loop and before `conn.commit()`:

```python
    for row in SEED_OPPORTUNITIES:
        _insert_opportunity(conn, row, account_ids[row["account_name"]], now)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_seed_opportunities.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/crm-api/fixture-seeding`

```bash
git add src/mock_salesforce/seed.py tests/test_seed_opportunities.py
git commit -m "feat(crm-api): seed one opportunity per account across ten stages"
```

---

### Task 4: Wire seeding into startup, idempotently (BEH-4) [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 2, Task 3
**Files:**
- Modify: `src/mock_salesforce/app.py`
- Create (test): `tests/test_seed_idempotency.py`

**Tests:** `tests/test_seed_idempotency.py` — create (BEH-4)

**Context to load:**
- Spec: BEH-4, Postconditions (`GET /accounts` returns exactly ten Accounts after a fresh startup)
- Reference: `src/mock_salesforce/app.py` (existing `on_startup`), `tests/conftest.py` (`client`
  fixture pattern)

- [ ] **Write failing test**

```python
# tests/test_seed_idempotency.py
from fastapi.testclient import TestClient


def test_fresh_startup_seeds_accounts_via_http(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "startup.db"))
    from mock_salesforce.app import app

    with TestClient(app) as client:
        resp = client.get("/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) == 10


def test_restart_against_seeded_database_does_not_duplicate(tmp_path, monkeypatch):
    db_path = str(tmp_path / "restart.db")
    monkeypatch.setenv("DB_PATH", db_path)
    from mock_salesforce.app import app

    with TestClient(app) as client:
        assert len(client.get("/accounts").json()) == 10
        assert len(client.get("/contacts").json()) >= 6
        assert len(client.get("/opportunities").json()) == 10

    # Second startup against the same DB_PATH — a fresh TestClient re-runs on_startup.
    with TestClient(app) as client:
        assert len(client.get("/accounts").json()) == 10
        assert len(client.get("/contacts").json()) >= 6
        assert len(client.get("/opportunities").json()) == 10
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_seed_idempotency.py`
Expected: FAIL — `AssertionError: 0 == 10` (`seed_if_empty` not called from startup yet)

- [ ] **Implement**

Modify `src/mock_salesforce/app.py`:

```python
from mock_salesforce.seed import seed_if_empty


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    conn.close()
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_seed_idempotency.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/crm-api/fixture-seeding`

```bash
git add src/mock_salesforce/app.py tests/test_seed_idempotency.py
git commit -m "feat(crm-api): seed fixture data once on startup against an empty database"
```

---

### Task 5: Wrap seed errors + assert id-scheme disjointness (BEH-5) [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 2, Task 3, Task 4
**Files:**
- Modify: `src/mock_salesforce/seed.py`
- Create (test): `tests/test_seed_ids.py`

**Tests:** `tests/test_seed_ids.py` — create (BEH-5, plus the `SEED_DATA_INVALID` /
`SEED_DB_NOT_WRITABLE` Error Cases rows)

**Context to load:**
- Spec: BEH-5, Error Cases table
- Canon: `../course-shared/canon/identifiers.md` full scheme table (`P-XXX`, `ACCOUNT-NNNN`,
  `POLICY-NN`, `INCIDENT-NN`, `TICKET-NNNNNN`, `INTERACTION-NNNNNNN`, `PROPOSAL-NNNNNN`,
  `ARTICLE-NNNN`, `OPPORTUNITY-NN`, `EXPERIMENT-NN`, `HELDOUT-<track>-NN`)
- Reference: `src/mock_salesforce/errors.py` (`error_body(code, message)` shape)

**Note (advisory, from plan review):** `SEED_DB_NOT_WRITABLE` cannot be triggered through the
real `on_startup` path as wired in Task 4 — `init_db(conn)` already commits the schema before
`seed_if_empty` runs, so a genuinely unwritable `DB_PATH` fails earlier, at `init_db`, with a raw
`sqlite3.OperationalError` outside this spec's scope. The wrapping added here still correctly
covers the seed-phase write (contacts/opportunities inserts, or the final `commit()`), which is
what this spec owns; the test below exercises that seed-phase failure directly via a `Connection`
subclass, not via a real read-only filesystem path.

- [ ] **Write failing test**

```python
# tests/test_seed_ids.py
import re
import sqlite3

import pytest

from mock_salesforce.db import get_connection, get_db_path, init_db
from mock_salesforce.seed import SeedDataError, seed_if_empty

RESERVED_ID_PATTERN = re.compile(
    r"^(P|ACCOUNT|POLICY|INCIDENT|TICKET|INTERACTION|PROPOSAL|ARTICLE|OPPORTUNITY|EXPERIMENT"
    r"|HELDOUT)-"
)


def test_seeded_ids_never_match_canon_reserved_schemes(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    seed_if_empty(conn)
    for table in ("accounts", "contacts", "opportunities"):
        for row in conn.execute(f"SELECT id FROM {table}").fetchall():
            assert not RESERVED_ID_PATTERN.match(str(row["id"]))
    conn.close()


def test_seed_module_never_reads_outside_this_repository():
    # Guards the "no runtime file read outside this repository" acceptance criterion as an
    # automated gate rather than review-by-inspection.
    import mock_salesforce.seed as seed_module

    source = open(seed_module.__file__).read()
    assert "course-shared" not in source
    assert "open(" not in source


def test_seed_data_invalid_names_the_offending_row(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "seed.db"))
    conn = get_connection()
    init_db(conn)
    bad_accounts = [
        {"name": "Bad Account", "account_type": "NotARealType",
         "industry": "Logistics and Supply Chain", "billing_country": "United States"}
    ]
    with pytest.raises(SeedDataError) as exc_info:
        seed_if_empty(conn, accounts=bad_accounts)
    assert exc_info.value.code == "SEED_DATA_INVALID"
    assert "Bad Account" in exc_info.value.message  # names the offending row, per spec
    conn.close()


def test_seed_db_not_writable_names_the_path(tmp_path, monkeypatch):
    db_path = str(tmp_path / "seed.db")
    monkeypatch.setenv("DB_PATH", db_path)
    conn = get_connection()
    init_db(conn)
    conn.close()

    class _BoomOnCommit(sqlite3.Connection):
        def commit(self):
            raise sqlite3.OperationalError("attempt to write a readonly database")

    boom_conn = sqlite3.connect(get_db_path(), factory=_BoomOnCommit)
    boom_conn.row_factory = sqlite3.Row
    with pytest.raises(SeedDataError) as exc_info:
        seed_if_empty(boom_conn)
    assert exc_info.value.code == "SEED_DB_NOT_WRITABLE"
    assert db_path in exc_info.value.message  # names the path, per spec
    boom_conn.close()
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_seed_ids.py`
Expected: FAIL — `ImportError: cannot import name 'SeedDataError'` (does not exist yet); the
disjointness and file-read-guard tests alone would already pass (ids are plain integers by
construction, and `seed.py` already has no `course-shared`/`open(` reference) but the two
error-wrapping tests fail

- [ ] **Implement**

Add to `src/mock_salesforce/seed.py`:

```python
from pydantic import ValidationError

from mock_salesforce.db import get_db_path


class SeedDataError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
```

Wrap the pydantic construction inside each of the three `_insert_*` helpers (defined in Tasks
1-3) so a `ValidationError` is re-raised as a `SeedDataError` naming the offending row — this is
what makes `test_seed_data_invalid_names_the_offending_row` pass, and it must happen at the
construction site, not around the whole loop, or the row identity is lost by the time the
exception is caught:

```python
def _insert_account(conn: sqlite3.Connection, row: dict, now: str) -> int:
    try:
        payload = AccountCreate(**row)
    except ValidationError as exc:
        raise SeedDataError(
            "SEED_DATA_INVALID",
            f"Account row '{row.get('name', '<unknown>')}' failed validation: {exc}",
        ) from exc
    cur = conn.execute(...)  # unchanged INSERT from Task 1
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
    cur = conn.execute(...)  # unchanged INSERT from Task 2
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
    cur = conn.execute(...)  # unchanged INSERT from Task 3
    return cur.lastrowid
```

Then wrap only the write side (the three loops plus `conn.commit()`) in `seed_if_empty`, since
`SeedDataError` from the helpers above already propagates untouched (it is not a
`sqlite3.OperationalError`, so this `except` clause never intercepts it):

```python
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
```

and change `seed_if_empty`'s signature to accept the test-injection overrides used above:

```python
def seed_if_empty(
    conn: sqlite3.Connection,
    accounts: list[dict] | None = None,
    contacts: list[dict] | None = None,
    opportunities: list[dict] | None = None,
) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    if existing > 0:
        return
    accounts = SEED_ACCOUNTS if accounts is None else accounts
    contacts = SEED_CONTACTS if contacts is None else contacts
    opportunities = SEED_OPPORTUNITIES if opportunities is None else opportunities
    now = datetime.now(timezone.utc).isoformat()
    account_ids: dict[str, int] = {}
    # ... try/except body above ...
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_seed_ids.py`
Expected: PASS

Then run the full suite once to confirm no regression across all seed tests and the pre-existing
Account/Contact/Opportunity CRUD suites:

Run: `python3 -m pytest -q`
Expected: PASS (all tests green)

- [ ] **Commit**

Branch: `feat/crm-api/fixture-seeding`

```bash
git add src/mock_salesforce/seed.py tests/test_seed_ids.py
git commit -m "feat(crm-api): wrap seed errors as SeedDataError, assert id-scheme disjointness"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan. Gate definitions come from
`.context-index/governance/gates.yaml` (this repo has one), not from the constitution's Quality
Gates section:

- **Test Suite** (`test`, deterministic, required, severity error): `python3 -m pytest -q`
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .`
- **Integration Tests** (`integration-test`, deterministic, required): unwired (`command: ""` in
  `gates.yaml`) — no integration-test suite exists yet in this repo; skipped, not failed.
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-5; both Error Cases rows,
  `SEED_DATA_INVALID` and `SEED_DB_NOT_WRITABLE`; "no runtime file read outside this repository" —
  enforced as an automated gate by Task 5's `test_seed_module_never_reads_outside_this_repository`,
  not review-by-inspection).

No boundary rules are defined in `.context-index/governance/boundaries.yaml` (empty list) — no
cross-boundary flags apply to this plan's file set. Per the constitution's Architecture
Boundaries, seeding fixture data on top of the existing Account/Contact/Opportunity tables is an
internal refactor with no HTTP-surface change — autonomous, no human approval required.
