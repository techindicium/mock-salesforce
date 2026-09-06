<!-- partial_schema: plan@1 -->

# Implementation Plan: Opportunity Lifecycle CRUD

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-api/charter.md
> **Spec:** .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`require_review: false`
>   for all risk tiers in this repo's `governance/risk-policies.yaml`); treated as a clean pass.
> **Platform:** Python 3.11, FastAPI 0.141.1, SQLite (stdlib `sqlite3`, no ORM), no auth, runs
>   locally only

**Goal:** Add the full Opportunity CRUD HTTP surface — including the stage-transition endpoint
that drives `crm-ui`'s pipeline board — on top of the already-implemented Account/Contact
scaffold, with server-derived `is_closed`/`is_won` and the ten-stage enum invariant enforced at
every write path.

**Architecture:** This spec extends the existing `mock_salesforce` FastAPI project (not a fresh
scaffold) built by the sibling `account-and-contact-management` spec/plan. It reuses
`src/mock_salesforce/db.py`'s connection factory and `init_db()` idempotency pattern, `errors.py`'s
exception handlers (already wired in `app.py` and requiring no changes), and
`accounts.py`/`contacts.py`'s router/try-finally/`model_dump(exclude_unset=True)` conventions —
this plan's `opportunities.py` follows the same shape line for line. `is_closed`/`is_won` are
computed server-side from `stage_name` at both insert and update time (never accepted as client
input — enforced by their absence from `OpportunityCreate`/`OpportunityUpdate`) and persisted as
`INTEGER` (0/1) columns, matching the Actionable Task Map's "computed at read/write time"
phrasing. `stage_name` (and the two other closed-vocabulary fields, `opportunity_type` and
`lead_source`, per the charter's Domain Model) are modeled as Pydantic `Literal` types so the
ten-stage/enum validation in BEH-8 falls out of existing `RequestValidationError` → `422
VALIDATION_ERROR` handling with no new error-handling code. Work happens on a new branch
`feat/crm-api/opportunity-lifecycle`, branched from the already-merged
`feat/crm-api/account-contact-scaffolding` work.

---

## File Structure

**Create:**
- `src/mock_salesforce/opportunities.py` — `APIRouter` with all five Opportunity routes
- `tests/test_opportunities.py` — Opportunity behavior suite (Tasks 2-5; extended, not
  recreated, by each per this repo's `per-behavior` test-policy granularity)

**Modify:**
- `src/mock_salesforce/db.py` — add `CREATE TABLE IF NOT EXISTS opportunities` to `init_db()`
- `src/mock_salesforce/models.py` — add `StageName`, `OpportunityType`, `LeadSource` `Literal`
  types and `OpportunityCreate`, `OpportunityOut`, `OpportunityUpdate` models
- `src/mock_salesforce/app.py` — mount the new `opportunities` router
- `tests/test_db_schema.py` — extend the schema-idempotency test to assert the `opportunities`
  table exists

**Reference (read, do not modify):**
- `src/mock_salesforce/accounts.py` — follow this router's try/finally connection-handling
  pattern, `model_dump(exclude_unset=True)` partial-update pattern, and `HTTPException(detail={
  "error": ..., "message": ...})` error shape
- `src/mock_salesforce/contacts.py` — follow this router's parent-existence-check-before-create
  pattern (`CONTACT_ACCOUNT_NOT_FOUND` → this spec's `OPPORTUNITY_ACCOUNT_NOT_FOUND`) and its
  optional-query-filter `list_*` pattern
- `.context-index/specs/features/crm-api/charter.md` — Domain Model (Opportunity key
  attributes, ten fixed stages, Invariants on `is_closed`/`is_won`)
- `.context-index/specs/features/crm-api/opportunity-lifecycle.spec.md` — full Behavioral
  Contract, Error Cases table
- `.context-index/specs/features/crm-api/account-and-contact-management.plan.md` — sibling plan;
  this plan mirrors its task granularity and TDD step format

## Context Packets

No source-manifest exists yet on this spec (its Behavioral Contract has not been implemented) —
packets fall back to charter Dependencies/Domain Model and the spec's own Behavioral Contract
sections, plus the sibling spec's already-implemented source files as pattern references.

### Task 1 Context
- Spec: Preconditions (Account-and-Contact endpoints must already exist); Actionable Task Map
  row "Define the Opportunity table"
- Charter: Domain Model → Entities table (Opportunity key attributes); Invariants (ten fixed
  stages; `is_closed`/`is_won` server-derived)
- Reference: `src/mock_salesforce/db.py` (existing `accounts`/`contacts` table DDL and
  `init_db()` idempotency pattern)

### Task 2 Context
- Spec: BEH-1, BEH-2, BEH-3, BEH-8 (create half), Error Cases rows
  `OPPORTUNITY_ACCOUNT_NOT_FOUND`, `VALIDATION_ERROR`
- Charter: Domain Model → Opportunity key attributes; Invariants ("`is_closed` is true if and
  only if `stage_name` is `Closed Won` or `Closed Lost`; `is_won` is true if and only if
  `stage_name` is `Closed Won`. Both are server-derived and never accepted as client input.")
- Reference: `src/mock_salesforce/contacts.py` (`create_contact`'s parent-existence-check
  pattern, directly reused for the Account-existence check here)

### Task 3 Context
- Spec: BEH-4, BEH-5, BEH-6, Error Cases row `OPPORTUNITY_NOT_FOUND`
- Reference: `src/mock_salesforce/contacts.py` (`list_contacts`'s optional `account_id` query
  filter pattern, extended here with a second optional `stage_name` filter)

### Task 4 Context
- Spec: BEH-7, BEH-8 (patch half), Postconditions ("`is_closed` and `is_won` are always
  consistent with the Opportunity's current `stage_name`... they are never independently stale
  after any successful `PATCH`")
- Charter: Invariants; Postconditions ("An Opportunity's `account_id` never changes once
  assigned, including across `PATCH` updates")
- Reference: `src/mock_salesforce/accounts.py` (`update_account`'s `model_dump(exclude_unset=True)`
  + dynamic `SET` clause pattern — `id`/`account_id`/`is_closed`/`is_won`/`created_at` are simply
  absent from `OpportunityUpdate`, so Pydantic's default `extra="ignore"` drops them with no
  extra code, exactly as the sibling plan relies on for `AccountUpdate`/`ContactUpdate`)

### Task 5 Context
- Spec: BEH-9
- Postconditions: "A deleted Opportunity no longer appears in any subsequent `GET
  /opportunities`... (the id is not reused for a future Opportunity)"

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5

This spec is a single-entity CRUD surface (unlike the sibling Account+Contact spec, which had two
independent entity chains) — every task modifies the same `opportunities.py` and shares
`models.py`/`app.py`/`db.py` with the prior task, so there is no independent group to run
alongside Group A.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Define the Opportunity table | medium | unit | — | 0 create, 2 modify |
| 2 | POST /opportunities (create + validation) | medium | unit | Task 1 | 1 create, 3 modify |
| 3 | GET /opportunities (+filters), GET /opportunities/{id} | small | unit | Task 2 | 0 create, 2 modify |
| 4 | PATCH /opportunities/{id} | medium | unit | Task 3 | 0 create, 3 modify |
| 5 | DELETE /opportunities/{id} | small | unit | Task 4 | 0 create, 2 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no matching `manifest.yaml` `test_strategies` entry, and file paths under
`src/mock_salesforce/**` / `tests/**` don't match any non-unit auto-detection heuristic). No
Strategy Summary or Test Infrastructure Requirements section follows, per the omission rule for
all-unit plans with no `infra_requirements:` in the spec.

Granularity is resolved once for the whole plan: `test_policy.granularity: per-behavior` in
`manifest.yaml` (source: manifest — no module-level override exists for `crm-api`). Per this
policy, `tests/test_opportunities.py` is created once (by Task 2) and **extended**, not
recreated, by every later task; `tests/test_db_schema.py` is extended (not recreated) by Task 1
since it already exists from the sibling plan and covers the same non-`BEH-*` schema-idempotency
precondition.

No heuristics matched module `crm-api` at plan time (`adev heuristics retrieve` returned
`__NONE__`) — no Heuristics section follows.

## Task Structure

> Per-task `- [ ]` checkboxes are authoring guides only; authoritative task state lives in the
> spec's lifecycle event log (`plan_task` events), not in this markdown. No `Status` column
> appears in any task table in this plan.

### Task 1: Define the Opportunity table [specialist: none]

**Charter capability:** Opportunity CRUD (foundation)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `src/mock_salesforce/db.py`, `tests/test_db_schema.py`

**Tests:** `tests/test_db_schema.py` — extend (schema-idempotency precondition, not a numbered
`BEH-*`)

**Context to load:**
- `.context-index/specs/features/crm-api/charter.md` (Domain Model → Entities table, Opportunity
  row)
- `src/mock_salesforce/db.py` (existing `accounts`/`contacts` DDL to match column-naming and
  `NOT NULL`/`REFERENCES` conventions)

- [ ] **Write failing test**

```python
# tests/test_db_schema.py (extend)
def test_init_db_creates_opportunities_table(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "schema2.db"))
    conn = get_connection()
    init_db(conn)
    init_db(conn)  # second call must not raise
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "opportunities" in tables
    conn.close()
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_db_schema.py`
Expected: FAIL — `AssertionError: 'opportunities' in {'accounts', 'contacts'}` (table not
created yet)

- [ ] **Implement**

Append the new table to `init_db()` in `src/mock_salesforce/db.py`, before the existing
`conn.commit()` call:

```python
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
```

`is_closed`/`is_won` are stored as `INTEGER` (0/1) — SQLite has no native boolean type; Task 2's
router casts them to Python `bool` before constructing `OpportunityOut`, matching the explicit
(non-implicit) coercion style this plan uses throughout rather than relying on Pydantic's lax-mode
int-to-bool coercion.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_db_schema.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/crm-api/opportunity-lifecycle`

```bash
git add src/mock_salesforce/db.py tests/test_db_schema.py
git commit -m "feat(crm-api): add opportunities table schema"
```

---

### Task 2: POST /opportunities (create + validation) [specialist: none]

**Charter capability:** Opportunity CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `src/mock_salesforce/opportunities.py`
- Create (test): `tests/test_opportunities.py`
- Modify: `src/mock_salesforce/models.py`, `src/mock_salesforce/app.py`

**Tests:** `tests/test_opportunities.py` — new suite (BEH-1, BEH-2, BEH-3, BEH-8 create half)

**Context to load:**
- Spec: BEH-1, BEH-2, BEH-3, BEH-8, Error Cases rows `OPPORTUNITY_ACCOUNT_NOT_FOUND`,
  `VALIDATION_ERROR`
- Charter: Domain Model → Opportunity key attributes; Invariants (ten fixed stages;
  `is_closed`/`is_won` server-derived)
- Reference: `src/mock_salesforce/contacts.py` (`create_contact`'s account-existence-check
  pattern)

- [ ] **Write failing test**

```python
# tests/test_opportunities.py
def test_create_opportunity_defaults_to_prospecting(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Big Deal", "close_date": "2026-12-01"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["stage_name"] == "Prospecting"
    assert body["is_closed"] is False
    assert body["is_won"] is False
    assert body["account_id"] == account["id"]
    assert body["id"] is not None


def test_create_opportunity_unknown_account(client):
    resp = client.post(
        "/opportunities",
        json={"account_id": 999999, "name": "Big Deal", "close_date": "2026-12-01"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_ACCOUNT_NOT_FOUND"
    assert client.get("/opportunities").json() == []


def test_create_opportunity_missing_required_fields(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    base = {"account_id": account["id"], "name": "Big Deal", "close_date": "2026-12-01"}
    for missing_field in ("name", "account_id", "close_date"):
        payload = {k: v for k, v in base.items() if k != missing_field}
        resp = client.post("/opportunities", json=payload)
        assert resp.status_code == 422
        assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_opportunity_invalid_stage_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post(
        "/opportunities",
        json={
            "account_id": account["id"],
            "name": "Big Deal",
            "close_date": "2026-12-01",
            "stage_name": "Bogus Stage",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: FAIL — `404 Not Found` on `POST /opportunities` (no route mounted yet)

- [ ] **Implement**

Append to `src/mock_salesforce/models.py` (add `date` to the existing `datetime` import):

```python
from datetime import date, datetime

StageName = Literal[
    "Prospecting",
    "Qualification",
    "Needs Analysis",
    "Value Proposition",
    "Id. Decision Makers",
    "Perception Analysis",
    "Proposal/Price Quote",
    "Negotiation/Review",
    "Closed Won",
    "Closed Lost",
]
OpportunityType = Literal["New Business", "Existing Business"]
LeadSource = Literal["Web", "Phone Inquiry", "Partner Referral", "Other"]


class OpportunityCreate(BaseModel):
    account_id: int
    name: str
    stage_name: StageName = "Prospecting"
    amount: Optional[float] = None
    close_date: date
    probability: Optional[float] = None
    opportunity_type: Optional[OpportunityType] = None
    lead_source: Optional[LeadSource] = None
    next_step: Optional[str] = None


class OpportunityOut(OpportunityCreate):
    id: int
    is_closed: bool
    is_won: bool
    created_at: datetime
    updated_at: datetime
```

Create `src/mock_salesforce/opportunities.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import OpportunityCreate, OpportunityOut

router = APIRouter()

CLOSED_STAGES = {"Closed Won", "Closed Lost"}


def _derive_closed_won(stage_name: str) -> tuple[bool, bool]:
    return stage_name in CLOSED_STAGES, stage_name == "Closed Won"


def _to_opportunity_out(row) -> OpportunityOut:
    data = dict(row)
    data["is_closed"] = bool(data["is_closed"])
    data["is_won"] = bool(data["is_won"])
    return OpportunityOut(**data)


@router.post("/opportunities", response_model=OpportunityOut, status_code=201)
def create_opportunity(payload: OpportunityCreate) -> OpportunityOut:
    conn = get_connection()
    try:
        account = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (payload.account_id,)
        ).fetchone()
        if account is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "OPPORTUNITY_ACCOUNT_NOT_FOUND",
                    "message": f"No account with id {payload.account_id}",
                },
            )
        is_closed, is_won = _derive_closed_won(payload.stage_name)
        now = datetime.now(timezone.utc).isoformat()
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
                payload.close_date.isoformat(), payload.probability,
                payload.opportunity_type, payload.lead_source, payload.next_step,
                int(is_closed), int(is_won), now, now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _to_opportunity_out(row)
    finally:
        conn.close()
```

Modify `src/mock_salesforce/app.py` — mount the router:

```python
from mock_salesforce.opportunities import router as opportunities_router

app.include_router(opportunities_router)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/opportunities.py \
  src/mock_salesforce/app.py tests/test_opportunities.py
git commit -m "feat(crm-api): add POST /opportunities with validation"
```

---

### Task 3: GET /opportunities (+filters), GET /opportunities/{id} [specialist: none]

**Charter capability:** Opportunity CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `src/mock_salesforce/opportunities.py`, `tests/test_opportunities.py`

**Tests:** `tests/test_opportunities.py` — extend (BEH-4, BEH-5, BEH-6)

**Context to load:**
- Spec: BEH-4, BEH-5, BEH-6, Error Cases row `OPPORTUNITY_NOT_FOUND`

- [ ] **Write failing test**

```python
# tests/test_opportunities.py (append)
def test_list_opportunities_filters(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    client.post(
        "/opportunities",
        json={
            "account_id": a1["id"], "name": "Deal One", "close_date": "2026-12-01",
            "stage_name": "Qualification",
        },
    )
    client.post(
        "/opportunities",
        json={"account_id": a2["id"], "name": "Deal Two", "close_date": "2026-12-01"},
    )

    resp = client.get("/opportunities", params={"account_id": a1["id"]})
    assert resp.status_code == 200
    assert [o["name"] for o in resp.json()] == ["Deal One"]

    resp = client.get("/opportunities", params={"stage_name": "Qualification"})
    assert [o["name"] for o in resp.json()] == ["Deal One"]

    resp_all = client.get("/opportunities")
    assert len(resp_all.json()) == 2


def test_get_opportunity_by_id_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.get(f"/opportunities/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Deal"


def test_get_opportunity_by_id_not_found(client):
    resp = client.get("/opportunities/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: FAIL — `404 Not Found` on `GET /opportunities` (route not mounted yet)

- [ ] **Implement**

Append to `src/mock_salesforce/opportunities.py`:

```python
@router.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities(
    account_id: int | None = None, stage_name: str | None = None
) -> list[OpportunityOut]:
    conn = get_connection()
    try:
        query = "SELECT * FROM opportunities WHERE 1=1"
        params: list = []
        if account_id is not None:
            query += " AND account_id = ?"
            params.append(account_id)
        if stage_name is not None:
            query += " AND stage_name = ?"
            params.append(stage_name)
        query += " ORDER BY created_at, id"
        rows = conn.execute(query, params).fetchall()
        return [_to_opportunity_out(r) for r in rows]
    finally:
        conn.close()


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(opportunity_id: int) -> OpportunityOut:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "OPPORTUNITY_NOT_FOUND",
                    "message": f"No opportunity with id {opportunity_id}",
                },
            )
        return _to_opportunity_out(row)
    finally:
        conn.close()
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/opportunities.py tests/test_opportunities.py
git commit -m "feat(crm-api): add GET /opportunities (with filters) and GET /opportunities/{id}"
```

---

### Task 4: PATCH /opportunities/{id} [specialist: none]

**Charter capability:** Opportunity CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 3
**Files:**
- Modify: `src/mock_salesforce/models.py`, `src/mock_salesforce/opportunities.py`,
  `tests/test_opportunities.py`

**Tests:** `tests/test_opportunities.py` — extend (BEH-7, BEH-8 patch half)

**Context to load:**
- Spec: BEH-7, BEH-8 (patch half), Postconditions (`is_closed`/`is_won` never stale after a
  successful PATCH)
- Charter: Postconditions ("An Opportunity's `account_id` never changes once assigned, including
  across `PATCH` updates")

- [ ] **Write failing test**

```python
# tests/test_opportunities.py (append)
def test_patch_opportunity_updates_fields(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(
        f"/opportunities/{created['id']}",
        json={"amount": 50000, "next_step": "Send proposal"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == 50000
    assert body["next_step"] == "Send proposal"
    assert body["updated_at"] != created["updated_at"]


def test_patch_opportunity_stage_recomputes_is_closed_is_won(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()

    won = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Closed Won"})
    assert won.status_code == 200
    assert won.json()["is_closed"] is True
    assert won.json()["is_won"] is True

    lost = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Closed Lost"})
    assert lost.status_code == 200
    assert lost.json()["is_closed"] is True
    assert lost.json()["is_won"] is False


def test_patch_opportunity_ignores_immutable_fields(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": a1["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(
        f"/opportunities/{created['id']}",
        json={
            "id": 999999, "account_id": a2["id"], "is_closed": True, "is_won": True,
            "created_at": "2000-01-01T00:00:00Z", "name": "Updated",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["account_id"] == a1["id"]
    assert body["created_at"] == created["created_at"]
    assert body["is_closed"] is False
    assert body["is_won"] is False
    assert body["name"] == "Updated"


def test_patch_opportunity_invalid_stage_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.patch(f"/opportunities/{created['id']}", json={"stage_name": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: FAIL — `405 Method Not Allowed` on `PATCH /opportunities/{id}` (route doesn't exist yet)

- [ ] **Implement**

Append to `src/mock_salesforce/models.py` (note: `OpportunityUpdate` never declares `account_id`,
`id`, `is_closed`, `is_won`, or `created_at`, so Pydantic's default `extra="ignore"` behavior
silently drops those keys if a client sends them — satisfying BEH-7's immutability requirement
with no extra code, exactly as `AccountUpdate`/`ContactUpdate` already do):

```python
class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    stage_name: Optional[StageName] = None
    amount: Optional[float] = None
    close_date: Optional[date] = None
    probability: Optional[float] = None
    opportunity_type: Optional[OpportunityType] = None
    lead_source: Optional[LeadSource] = None
    next_step: Optional[str] = None
```

Append to `src/mock_salesforce/opportunities.py`:

```python
from mock_salesforce.models import OpportunityUpdate


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def update_opportunity(opportunity_id: int, payload: OpportunityUpdate) -> OpportunityOut:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "OPPORTUNITY_NOT_FOUND",
                    "message": f"No opportunity with id {opportunity_id}",
                },
            )
        updates = payload.model_dump(exclude_unset=True)
        if updates:
            if updates.get("close_date") is not None:
                updates["close_date"] = updates["close_date"].isoformat()
            if "stage_name" in updates:
                is_closed, is_won = _derive_closed_won(updates["stage_name"])
                updates["is_closed"] = int(is_closed)
                updates["is_won"] = int(is_won)
            now = datetime.now(timezone.utc).isoformat()
            set_clause = ", ".join(f"{field} = ?" for field in updates)
            conn.execute(
                f"UPDATE opportunities SET {set_clause}, updated_at = ? WHERE id = ?",
                (*updates.values(), now, opportunity_id),
            )
            conn.commit()
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        return _to_opportunity_out(row)
    finally:
        conn.close()
```

`updates` only ever contains mutable fields (see the `OpportunityUpdate` model above), so
recomputation only touches `is_closed`/`is_won` when `stage_name` is actually part of the
request — an update to `amount` alone leaves the existing (already-consistent) derived flags
untouched, matching the Postconditions clause precisely.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/opportunities.py \
  tests/test_opportunities.py
git commit -m "feat(crm-api): add PATCH /opportunities/{id} with stage recomputation"
```

---

### Task 5: DELETE /opportunities/{id} [specialist: none]

**Charter capability:** Opportunity CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Modify: `src/mock_salesforce/opportunities.py`, `tests/test_opportunities.py`

**Tests:** `tests/test_opportunities.py` — extend (BEH-9)

**Context to load:**
- Spec: BEH-9; Postconditions ("A deleted Opportunity no longer appears in any subsequent `GET
  /opportunities`... the id is not reused for a future Opportunity")

- [ ] **Write failing test**

```python
# tests/test_opportunities.py (append)
def test_delete_opportunity_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/opportunities",
        json={"account_id": account["id"], "name": "Deal", "close_date": "2026-12-01"},
    ).json()
    resp = client.delete(f"/opportunities/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/opportunities/{created['id']}").status_code == 404
    assert client.get("/opportunities").json() == []


def test_delete_opportunity_not_found(client):
    resp = client.delete("/opportunities/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "OPPORTUNITY_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: FAIL — `405 Method Not Allowed` on `DELETE /opportunities/{id}` (route doesn't exist
yet)

- [ ] **Implement**

Append to `src/mock_salesforce/opportunities.py`:

```python
@router.delete("/opportunities/{opportunity_id}", status_code=204)
def delete_opportunity(opportunity_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "OPPORTUNITY_NOT_FOUND",
                    "message": f"No opportunity with id {opportunity_id}",
                },
            )
        conn.execute("DELETE FROM opportunities WHERE id = ?", (opportunity_id,))
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_opportunities.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/opportunities.py tests/test_opportunities.py
git commit -m "feat(crm-api): add DELETE /opportunities/{id}"
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
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-9, plus the
  `OPPORTUNITY_ACCOUNT_NOT_FOUND`/`OPPORTUNITY_NOT_FOUND` Error Cases rows this spec owns; the
  general `VALIDATION_ERROR`/`MALFORMED_JSON` shapes are already covered by the sibling spec's
  suite and `errors.py`, unchanged by this plan).

No boundary rules are defined in `.context-index/governance/boundaries.yaml` (empty list) — no
cross-boundary flags apply to this plan's file set. Per the constitution's Architecture
Boundaries, adding these routes is "adding new mock endpoints that extend (not break) the
existing contract" — autonomous, no human approval required.
