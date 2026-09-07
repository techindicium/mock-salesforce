<!-- partial_schema: plan@1 -->

# Implementation Plan: Account and Contact Management

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-api/charter.md
> **Spec:** .context-index/specs/features/crm-api/account-and-contact-management.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`require_review: false`
>   for all risk tiers in this repo's `governance/risk-policies.yaml`); treated as a clean pass.
> **Platform:** Python 3.11, SQLite, no ORM, no auth, runs locally only

**Goal:** Stand up the Account and Contact CRUD HTTP surface — the master-data foundation of
`mock-salesforce` — backed by a fresh SQLite schema, with full validation, error-shaping, and
delete-guard behavior per the Live Spec.

**Architecture:** This is the first spec of the `crm-api` module to be planned, so this plan
also bootstraps the project itself: package layout, dependency manifest, and the SQLite
connection/schema module. **Framework decision:** FastAPI (not yet chosen in
`platform-context.yaml`, which currently reads `framework: none`) — chosen because the sibling
spec `health-static-hosting-and-openapi.spec.md` requires "the framework's auto-generated
OpenAPI document, never hand-maintained," which FastAPI provides natively via Pydantic models,
and because Pydantic's validation errors map cleanly onto this spec's `422 VALIDATION_ERROR`
shape. This is an autonomous choice per the constitution's Architecture Boundaries (it adds a
pip dependency, not a dependency on another workspace repo, and does not touch the public HTTP
contract's paths/shapes) — `platform-context.yaml` should be updated to record it once this plan
lands (tracked as a follow-up, not a task in this plan). Task 5's delete-guard queries
`sqlite_master` before counting Opportunity rows, since the `opportunities` table is owned by
the sibling `opportunity-lifecycle` spec/plan and may not exist yet when this plan is
implemented — this keeps BEH-9 correct regardless of implementation order between the two
sibling specs.

---

## File Structure

**Create:**
- `requirements.txt` — `fastapi`, `uvicorn`, `pytest`, `httpx` (FastAPI's `TestClient` needs
  `httpx` as of FastAPI/Starlette's current TestClient implementation)
- `pyproject.toml` — minimal `[tool.pytest.ini_options]` config (`testpaths = ["tests"]`) and
  `[tool.ruff]` config if none exists at repo root
- `src/mock_salesforce/__init__.py` — empty package marker
- `src/mock_salesforce/db.py` — SQLite connection factory (`DB_PATH` env var, default
  `mock_salesforce.db`), idempotent `init_db()` (`CREATE TABLE IF NOT EXISTS` for `accounts` and
  `contacts`), `foreign_keys = ON` pragma, `dependent_count(conn, account_id)` helper used by
  Task 5
- `src/mock_salesforce/errors.py` — shared error-JSON builder (`{"error": "<CODE>", "message":
  "..."}` shape) and FastAPI exception handlers: `RequestValidationError` → `422
  VALIDATION_ERROR`, malformed-JSON body → `400 MALFORMED_JSON`
- `src/mock_salesforce/models.py` — Pydantic request/response models: `AccountCreate`,
  `AccountUpdate`, `AccountOut`, `ContactCreate`, `ContactUpdate`, `ContactOut`; `account_type`
  as a `Literal["Customer", "Prospect", "Partner", "Other"]` enum field
- `src/mock_salesforce/accounts.py` — `APIRouter` with all five Account routes
- `src/mock_salesforce/contacts.py` — `APIRouter` with all five Contact routes
- `src/mock_salesforce/app.py` — `FastAPI()` instance; calls `init_db()` on startup; mounts
  both routers; registers the exception handlers from `errors.py`
- `tests/conftest.py` — `client` fixture (a `TestClient` wrapping `app.py`'s app, pointed at a
  per-test temp SQLite file via `DB_PATH` env var override so tests never share state)
- `tests/test_db_schema.py` — schema idempotency test (Task 1)
- `tests/test_accounts.py` — Account behavior suite (Tasks 2-5; extended, not recreated, by each)
- `tests/test_contacts.py` — Contact behavior suite (Tasks 6-9; extended, not recreated, by each)

**Modify:**
- `.gitignore` — add `__pycache__/`, `*.pyc`, `.venv/`, `*.db`, `.pytest_cache/`,
  `*.egg-info/` (no Python entries exist yet)

**Reference (read, do not modify):**
- `.context-index/specs/features/crm-api/charter.md` — Domain Model (Entities table), Capability
  Map, Interface Contracts
- `.context-index/specs/features/crm-api/account-and-contact-management.spec.md` — full
  Behavioral Contract, Error Cases table

## Context Packets

No source-manifest exists yet (greenfield spec) — packets fall back to charter Dependencies,
Domain Model, and the spec's own Behavioral Contract sections.

### Task 1 Context
- Spec: `.context-index/specs/features/crm-api/account-and-contact-management.spec.md`
  (Preconditions; Error Cases row for `MALFORMED_JSON`)
- Charter: `.context-index/specs/features/crm-api/charter.md` (Domain Model → Entities table,
  capabilities: Account CRUD, Contact CRUD)
- Constitution: `.context-index/constitution.md` (Coding Standards → Language and Runtime;
  "Fixture-backed, offline only" — no network calls; "fail at the HTTP boundary with a real
  Salesforce-shaped error response, not a generic 500")

### Task 2 Context
- Spec: criteria BEH-1, BEH-2, BEH-3 (create half), Error Cases row `VALIDATION_ERROR`,
  `MALFORMED_JSON`
- Charter: Domain Model → Account key attributes

### Task 3 Context
- Spec: criteria BEH-4, BEH-5, BEH-6, Error Cases row `ACCOUNT_NOT_FOUND`

### Task 4 Context
- Spec: criteria BEH-3 (patch half), BEH-7

### Task 5 Context
- Spec: criteria BEH-8, BEH-9, Error Cases row `ACCOUNT_HAS_DEPENDENTS`
- Charter: Invariants ("An Account cannot be deleted while it still has any Contact or
  Opportunity referencing it"); Deferred Capabilities (cascade/reassignment explicitly
  out of scope)

### Task 6 Context
- Spec: criteria BEH-10, BEH-11, BEH-12, Error Cases rows `CONTACT_ACCOUNT_NOT_FOUND`,
  `VALIDATION_ERROR`
- Charter: Domain Model → Contact key attributes; Relationships ("Every Contact belongs to
  exactly one Account")

### Task 7 Context
- Spec: criteria BEH-13, BEH-14, BEH-15, Error Cases row `CONTACT_NOT_FOUND`

### Task 8 Context
- Spec: criteria BEH-16; Postconditions ("A Contact's `account_id` never changes once assigned")

### Task 9 Context
- Spec: criteria BEH-17

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5
- Group B (sequential): Task 6 → Task 7 → Task 8 → Task 9

Group B shares `src/mock_salesforce/models.py` and `src/mock_salesforce/app.py` with Group A
(both add classes/mount calls to the same files) and only structurally depends on Task 1 (the
schema/app scaffold), not on the rest of Group A. Despite that shallow dependency, `/adev:implement`
should run Group B after Group A completes rather than concurrently with it, to avoid merge
conflicts on those two shared files — this plan does not mark Group B `independent` for that
reason.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Project scaffolding & Account/Contact schema | medium | unit | — | 8 create, 1 modify |
| 2 | POST /accounts (create + validation) | medium | unit | Task 1 | 3 create, 1 modify |
| 3 | GET /accounts, GET /accounts/{id} | small | unit | Task 2 | 0 create, 2 modify |
| 4 | PATCH /accounts/{id} | medium | unit | Task 3 | 0 create, 3 modify |
| 5 | DELETE /accounts/{id} (dependent guard) | medium | unit | Task 4 | 0 create, 3 modify |
| 6 | POST /contacts (create + validation) | medium | unit | Task 1 | 2 create, 2 modify |
| 7 | GET /contacts (+account_id filter), GET /contacts/{id} | small | unit | Task 6 | 0 create, 2 modify |
| 8 | PATCH /contacts/{id} | small | unit | Task 7 | 0 create, 3 modify |
| 9 | DELETE /contacts/{id} | small | unit | Task 8 | 0 create, 2 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no matching `manifest.yaml` `test_strategies` entry, and file paths under
`src/mock_salesforce/**` / `tests/**` don't match any non-unit auto-detection heuristic). No
Strategy Summary or Test Infrastructure Requirements section follows, per the omission rule for
all-unit plans with no `infra_requirements:` in the spec.

Granularity is resolved once for the whole plan: `test_policy.granularity: per-behavior` in
`manifest.yaml` (source: manifest — no module-level override exists for `crm-api`). Per this
policy, `tests/test_accounts.py` and `tests/test_contacts.py` are each created once (by Task 2
and Task 6 respectively) and **extended**, not recreated, by every later task in their group;
`tests/test_db_schema.py` is a one-off suite for the schema-idempotency precondition, which is
not itself a numbered `BEH-*` and so is not subject to the per-behavior sharing rule.

## Task Structure

> Per-task `- [ ]` checkboxes are authoring guides only; authoritative task state lives in the
> spec's lifecycle event log (`plan_task` events), not in this markdown. No `Status` column
> appears in any task table in this plan.

### Task 1: Project scaffolding & Account/Contact schema [specialist: none]

**Charter capability:** Account CRUD, Contact CRUD (foundation)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `requirements.txt`, `pyproject.toml`, `src/mock_salesforce/__init__.py`,
  `src/mock_salesforce/db.py`, `src/mock_salesforce/errors.py`, `src/mock_salesforce/app.py`,
  `tests/conftest.py`
- Create (test): `tests/test_db_schema.py`
- Modify: `.gitignore`

**Tests:** `tests/test_db_schema.py` — new suite (schema-idempotency precondition, not a
numbered `BEH-*`)

**Context to load:**
- `.context-index/specs/features/crm-api/charter.md` (Domain Model → Entities table)
- `.context-index/constitution.md` (Coding Standards; "fail at the HTTP boundary with a real
  Salesforce-shaped error response, not a generic 500")

- [ ] **Write failing test**

```python
# tests/test_db_schema.py
from mock_salesforce.db import get_connection, init_db


def test_init_db_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "schema.db"))
    conn = get_connection()
    init_db(conn)
    init_db(conn)  # second call must not raise
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"accounts", "contacts"}.issubset(tables)
    conn.close()
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_db_schema.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mock_salesforce'` (package doesn't
exist yet)

- [ ] **Implement**

Create `requirements.txt` (`fastapi`, `uvicorn`, `pytest`, `httpx`) and `pyproject.toml`
(`[tool.pytest.ini_options] testpaths = ["tests"]`). Create `src/mock_salesforce/db.py`:

```python
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
```

Create `src/mock_salesforce/errors.py` (shared error shape + handlers registered by `app.py`;
the `HTTPException` handler and the JSON-vs-field-validation branch in the
`RequestValidationError` handler are exercised starting Task 3 and Task 2 respectively, but are
wired here since both are app-wide, startup-time registrations):

```python
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_body(code: str, message: str) -> dict:
    return {"error": code, "message": message}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    if first.get("type") == "json_invalid":
        # NOTE: confirm this literal error `type` string against the installed
        # FastAPI/Pydantic version during implementation — it is version-sensitive.
        return JSONResponse(
            status_code=400,
            content=error_body("MALFORMED_JSON", "Request body is not valid JSON"),
        )
    field = ".".join(str(p) for p in first["loc"] if p != "body")
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", f"{field}: {first['msg']}"),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    content = exc.detail if isinstance(exc.detail, dict) else error_body(
        "HTTP_ERROR", str(exc.detail)
    )
    return JSONResponse(status_code=exc.status_code, content=content)
```

Create `src/mock_salesforce/app.py`:

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mock_salesforce.db import get_connection, init_db
from mock_salesforce.errors import http_exception_handler, validation_exception_handler

app = FastAPI()
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection()
    init_db(conn)
    conn.close()
```

Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    from mock_salesforce.app import app

    with TestClient(app) as c:
        yield c
```

Modify `.gitignore` — append `__pycache__/`, `*.pyc`, `.venv/`, `*.db`, `.pytest_cache/`,
`*.egg-info/`.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_db_schema.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/crm-api/account-contact-scaffolding`

```bash
git add requirements.txt pyproject.toml src/mock_salesforce/__init__.py \
  src/mock_salesforce/db.py src/mock_salesforce/errors.py src/mock_salesforce/app.py \
  tests/conftest.py tests/test_db_schema.py .gitignore
git commit -m "feat(crm-api): scaffold project and Account/Contact schema"
```

---

### Task 2: POST /accounts (create + validation) [specialist: none]

**Charter capability:** Account CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `src/mock_salesforce/models.py`, `src/mock_salesforce/accounts.py`
- Create (test): `tests/test_accounts.py`
- Modify: `src/mock_salesforce/app.py`

**Tests:** `tests/test_accounts.py` — new suite (BEH-1, BEH-2, BEH-3 create half)

**Context to load:**
- Spec: BEH-1, BEH-2, BEH-3 (create half), Error Cases rows `VALIDATION_ERROR`,
  `MALFORMED_JSON`
- Charter: Domain Model → Account key attributes

- [ ] **Write failing test**

```python
# tests/test_accounts.py
def test_create_account_success(client):
    resp = client.post("/accounts", json={"name": "Acme Corp", "account_type": "Customer"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Acme Corp"
    assert body["id"] is not None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_create_account_missing_name(client):
    resp = client.post("/accounts", json={"account_type": "Customer"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_account_invalid_account_type(client):
    resp = client.post("/accounts", json={"name": "Acme", "account_type": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_create_account_malformed_json(client):
    resp = client.post(
        "/accounts",
        content=b"{not valid json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "MALFORMED_JSON"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: FAIL — `404 Not Found` on `POST /accounts` (no route mounted yet)

- [ ] **Implement**

Create `src/mock_salesforce/models.py`:

```python
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

AccountType = Literal["Customer", "Prospect", "Partner", "Other"]


class AccountCreate(BaseModel):
    name: str
    account_type: Optional[AccountType] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    billing_street: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None


class AccountOut(AccountCreate):
    id: int
    created_at: datetime
    updated_at: datetime
```

Create `src/mock_salesforce/accounts.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter

from mock_salesforce.db import get_connection
from mock_salesforce.models import AccountCreate, AccountOut

router = APIRouter()


@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate) -> AccountOut:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
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
    conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return AccountOut(**dict(row))
```

Modify `src/mock_salesforce/app.py` — mount the router:

```python
from mock_salesforce.accounts import router as accounts_router

app.include_router(accounts_router)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: PASS

- [ ] **Commit**

Branch (already created in Task 1): `feat/crm-api/account-contact-scaffolding`

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/accounts.py \
  src/mock_salesforce/app.py tests/test_accounts.py
git commit -m "feat(crm-api): add POST /accounts with validation"
```

---

### Task 3: GET /accounts, GET /accounts/{id} [specialist: none]

**Charter capability:** Account CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `src/mock_salesforce/accounts.py`, `tests/test_accounts.py`

**Tests:** `tests/test_accounts.py` — extend (BEH-4, BEH-5, BEH-6)

**Context to load:**
- Spec: BEH-4, BEH-5, BEH-6, Error Cases row `ACCOUNT_NOT_FOUND`

- [ ] **Write failing test**

```python
# tests/test_accounts.py (append)
def test_list_accounts_ordered_by_created_at(client):
    client.post("/accounts", json={"name": "First"})
    client.post("/accounts", json={"name": "Second"})
    resp = client.get("/accounts")
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert names == ["First", "Second"]


def test_get_account_by_id_success(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.get(f"/accounts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme"


def test_get_account_by_id_not_found(client):
    resp = client.get("/accounts/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "ACCOUNT_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: FAIL — `404 Not Found` on `GET /accounts` (route not mounted yet)

- [ ] **Implement**

Append to `src/mock_salesforce/accounts.py`:

```python
from fastapi import HTTPException


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts() -> list[AccountOut]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM accounts ORDER BY created_at, id").fetchall()
    conn.close()
    return [AccountOut(**dict(r)) for r in rows]


@router.get("/accounts/{account_id}", response_model=AccountOut)
def get_account(account_id: int) -> AccountOut:
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "ACCOUNT_NOT_FOUND", "message": f"No account with id {account_id}"},
        )
    return AccountOut(**dict(row))
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/accounts.py tests/test_accounts.py
git commit -m "feat(crm-api): add GET /accounts and GET /accounts/{id}"
```

---

### Task 4: PATCH /accounts/{id} [specialist: none]

**Charter capability:** Account CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 3
**Files:**
- Modify: `src/mock_salesforce/models.py`, `src/mock_salesforce/accounts.py`,
  `tests/test_accounts.py`

**Tests:** `tests/test_accounts.py` — extend (BEH-3 patch half, BEH-7)

**Context to load:**
- Spec: BEH-3 (patch half), BEH-7

- [ ] **Write failing test**

```python
# tests/test_accounts.py (append)
def test_patch_account_updates_fields(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(f"/accounts/{created['id']}", json={"industry": "Logistics"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["industry"] == "Logistics"
    assert body["updated_at"] != created["updated_at"]


def test_patch_account_ignores_id_and_created_at(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(
        f"/accounts/{created['id']}",
        json={"id": 999999, "created_at": "2000-01-01T00:00:00Z", "name": "Updated"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["created_at"] == created["created_at"]
    assert body["name"] == "Updated"


def test_patch_account_invalid_account_type(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.patch(f"/accounts/{created['id']}", json={"account_type": "Bogus"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: FAIL — `405 Method Not Allowed` on `PATCH /accounts/{id}` (route doesn't exist yet)

- [ ] **Implement**

Append to `src/mock_salesforce/models.py`:

```python
class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    billing_street: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None
```

Append to `src/mock_salesforce/accounts.py` (note: `AccountUpdate` never declares `id` or
`created_at`, so Pydantic's default `extra="ignore"` behavior silently drops those keys if a
client sends them — satisfying BEH-7's immutability requirement with no extra code):

```python
from mock_salesforce.models import AccountUpdate


@router.patch("/accounts/{account_id}", response_model=AccountOut)
def update_account(account_id: int, payload: AccountUpdate) -> AccountOut:
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "ACCOUNT_NOT_FOUND", "message": f"No account with id {account_id}"},
        )
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        now = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{field} = ?" for field in updates)
        conn.execute(
            f"UPDATE accounts SET {set_clause}, updated_at = ? WHERE id = ?",
            (*updates.values(), now, account_id),
        )
        conn.commit()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return AccountOut(**dict(row))
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/accounts.py tests/test_accounts.py
git commit -m "feat(crm-api): add PATCH /accounts/{id}"
```

---

### Task 5: DELETE /accounts/{id} (dependent guard) [specialist: none]

**Charter capability:** Account CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Modify: `src/mock_salesforce/db.py`, `src/mock_salesforce/accounts.py`,
  `tests/test_accounts.py`

**Tests:** `tests/test_accounts.py` — extend (BEH-8, BEH-9)

**Context to load:**
- Spec: BEH-8, BEH-9, Error Cases row `ACCOUNT_HAS_DEPENDENTS`
- Charter: Invariants ("An Account cannot be deleted while it still has any Contact or
  Opportunity referencing it")

- [ ] **Write failing test**

The Contact dependent is seeded by direct SQL through `mock_salesforce.db`, not through
`POST /contacts` (that endpoint doesn't exist until Task 6) — this keeps Task 5 fully
self-contained against the `contacts` table Task 1 already created.

```python
# tests/test_accounts.py (append)
def test_delete_account_no_dependents(client):
    created = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.delete(f"/accounts/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/accounts/{created['id']}").status_code == 404


def test_delete_account_with_contact_returns_409(client):
    from mock_salesforce.db import get_connection

    account = client.post("/accounts", json={"name": "Acme"}).json()
    conn = get_connection()
    conn.execute(
        "INSERT INTO contacts (account_id, last_name, created_at, updated_at) "
        "VALUES (?, ?, datetime('now'), datetime('now'))",
        (account["id"], "Doe"),
    )
    conn.commit()
    conn.close()

    resp = client.delete(f"/accounts/{account['id']}")
    assert resp.status_code == 409
    assert resp.json()["error"] == "ACCOUNT_HAS_DEPENDENTS"
    assert client.get(f"/accounts/{account['id']}").status_code == 200
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: FAIL — `405 Method Not Allowed` on `DELETE /accounts/{id}` (route doesn't exist yet)

- [ ] **Implement**

Append to `src/mock_salesforce/db.py`:

```python
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
```

Append to `src/mock_salesforce/accounts.py`:

```python
from mock_salesforce.db import dependent_count


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(account_id: int) -> None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "ACCOUNT_NOT_FOUND", "message": f"No account with id {account_id}"},
        )
    count = dependent_count(conn, account_id)
    if count > 0:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "ACCOUNT_HAS_DEPENDENTS",
                "message": f"Account {account_id} has {count} dependent record(s)",
            },
        )
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_accounts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/db.py src/mock_salesforce/accounts.py tests/test_accounts.py
git commit -m "feat(crm-api): add DELETE /accounts/{id} with dependent guard"
```

---

### Task 6: POST /contacts (create + validation) [specialist: none]

**Charter capability:** Contact CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `src/mock_salesforce/contacts.py`
- Create (test): `tests/test_contacts.py`
- Modify: `src/mock_salesforce/models.py`, `src/mock_salesforce/app.py`

**Tests:** `tests/test_contacts.py` — new suite (BEH-10, BEH-11, BEH-12)

**Context to load:**
- Spec: BEH-10, BEH-11, BEH-12, Error Cases rows `CONTACT_ACCOUNT_NOT_FOUND`,
  `VALIDATION_ERROR`
- Charter: Domain Model → Contact key attributes; Relationships ("Every Contact belongs to
  exactly one Account")

- [ ] **Write failing test**

```python
# tests/test_contacts.py
def test_create_contact_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post("/contacts", json={"account_id": account["id"], "last_name": "Doe"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["last_name"] == "Doe"
    assert body["account_id"] == account["id"]


def test_create_contact_unknown_account(client):
    resp = client.post("/contacts", json={"account_id": 999999, "last_name": "Doe"})
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONTACT_ACCOUNT_NOT_FOUND"


def test_create_contact_missing_last_name(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    resp = client.post("/contacts", json={"account_id": account["id"]})
    assert resp.status_code == 422
    assert resp.json()["error"] == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: FAIL — `404 Not Found` on `POST /contacts` (no route mounted yet)

- [ ] **Implement**

Append to `src/mock_salesforce/models.py`:

```python
class ContactCreate(BaseModel):
    account_id: int
    first_name: Optional[str] = None
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None


class ContactOut(ContactCreate):
    id: int
    created_at: datetime
    updated_at: datetime
```

Create `src/mock_salesforce/contacts.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from mock_salesforce.db import get_connection
from mock_salesforce.models import ContactCreate, ContactOut

router = APIRouter()


@router.post("/contacts", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactCreate) -> ContactOut:
    conn = get_connection()
    account = conn.execute(
        "SELECT id FROM accounts WHERE id = ?", (payload.account_id,)
    ).fetchone()
    if account is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={
                "error": "CONTACT_ACCOUNT_NOT_FOUND",
                "message": f"No account with id {payload.account_id}",
            },
        )
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO contacts (account_id, first_name, last_name, email, phone, title,
                               created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (payload.account_id, payload.first_name, payload.last_name, payload.email,
         payload.phone, payload.title, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return ContactOut(**dict(row))
```

Modify `src/mock_salesforce/app.py` — mount the router:

```python
from mock_salesforce.contacts import router as contacts_router

app.include_router(contacts_router)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/contacts.py \
  src/mock_salesforce/app.py tests/test_contacts.py
git commit -m "feat(crm-api): add POST /contacts with validation"
```

---

### Task 7: GET /contacts (+account_id filter), GET /contacts/{id} [specialist: none]

**Charter capability:** Contact CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 6
**Files:**
- Modify: `src/mock_salesforce/contacts.py`, `tests/test_contacts.py`

**Tests:** `tests/test_contacts.py` — extend (BEH-13, BEH-14, BEH-15)

**Context to load:**
- Spec: BEH-13, BEH-14, BEH-15, Error Cases row `CONTACT_NOT_FOUND`

- [ ] **Write failing test**

```python
# tests/test_contacts.py (append)
def test_list_contacts_filtered_by_account(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    client.post("/contacts", json={"account_id": a1["id"], "last_name": "One"})
    client.post("/contacts", json={"account_id": a2["id"], "last_name": "Two"})

    resp = client.get("/contacts", params={"account_id": a1["id"]})
    assert resp.status_code == 200
    names = [c["last_name"] for c in resp.json()]
    assert names == ["One"]

    resp_all = client.get("/contacts")
    assert len(resp_all.json()) == 2


def test_get_contact_by_id_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/contacts", json={"account_id": account["id"], "last_name": "Doe"}
    ).json()
    resp = client.get(f"/contacts/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["last_name"] == "Doe"


def test_get_contact_by_id_not_found(client):
    resp = client.get("/contacts/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONTACT_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: FAIL — `404 Not Found` on `GET /contacts` (route not mounted yet)

- [ ] **Implement**

Append to `src/mock_salesforce/contacts.py`:

```python
@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(account_id: int | None = None) -> list[ContactOut]:
    conn = get_connection()
    if account_id is not None:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE account_id = ? ORDER BY created_at, id",
            (account_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM contacts ORDER BY created_at, id").fetchall()
    conn.close()
    return [ContactOut(**dict(r)) for r in rows]


@router.get("/contacts/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: int) -> ContactOut:
    conn = get_connection()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "CONTACT_NOT_FOUND", "message": f"No contact with id {contact_id}"},
        )
    return ContactOut(**dict(row))
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/contacts.py tests/test_contacts.py
git commit -m "feat(crm-api): add GET /contacts (with account_id filter) and GET /contacts/{id}"
```

---

### Task 8: PATCH /contacts/{id} [specialist: none]

**Charter capability:** Contact CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 7
**Files:**
- Modify: `src/mock_salesforce/models.py`, `src/mock_salesforce/contacts.py`,
  `tests/test_contacts.py`

**Tests:** `tests/test_contacts.py` — extend (BEH-16)

**Context to load:**
- Spec: BEH-16; Postconditions ("A Contact's `account_id` never changes once assigned")

- [ ] **Write failing test**

```python
# tests/test_contacts.py (append)
def test_patch_contact_updates_fields(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/contacts", json={"account_id": account["id"], "last_name": "Doe"}
    ).json()
    resp = client.patch(f"/contacts/{created['id']}", json={"title": "VP Sales"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "VP Sales"


def test_patch_contact_ignores_account_id(client):
    a1 = client.post("/accounts", json={"name": "A1"}).json()
    a2 = client.post("/accounts", json={"name": "A2"}).json()
    created = client.post(
        "/contacts", json={"account_id": a1["id"], "last_name": "Doe"}
    ).json()
    resp = client.patch(f"/contacts/{created['id']}", json={"account_id": a2["id"]})
    assert resp.status_code == 200
    assert resp.json()["account_id"] == a1["id"]
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: FAIL — `405 Method Not Allowed` on `PATCH /contacts/{id}` (route doesn't exist yet)

- [ ] **Implement**

Append to `src/mock_salesforce/models.py` (note: `ContactUpdate` never declares `account_id`,
`id`, or `created_at`, so Pydantic's default `extra="ignore"` behavior silently drops those
keys if a client sends them — satisfying BEH-16's immutability requirement with no extra code):

```python
class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
```

Append to `src/mock_salesforce/contacts.py`:

```python
from mock_salesforce.models import ContactUpdate


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, payload: ContactUpdate) -> ContactOut:
    conn = get_connection()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "CONTACT_NOT_FOUND", "message": f"No contact with id {contact_id}"},
        )
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        now = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{field} = ?" for field in updates)
        conn.execute(
            f"UPDATE contacts SET {set_clause}, updated_at = ? WHERE id = ?",
            (*updates.values(), now, contact_id),
        )
        conn.commit()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    conn.close()
    return ContactOut(**dict(row))
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/models.py src/mock_salesforce/contacts.py tests/test_contacts.py
git commit -m "feat(crm-api): add PATCH /contacts/{id} with immutable account_id"
```

---

### Task 9: DELETE /contacts/{id} [specialist: none]

**Charter capability:** Contact CRUD
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 8
**Files:**
- Modify: `src/mock_salesforce/contacts.py`, `tests/test_contacts.py`

**Tests:** `tests/test_contacts.py` — extend (BEH-17)

**Context to load:**
- Spec: BEH-17

- [ ] **Write failing test**

```python
# tests/test_contacts.py (append)
def test_delete_contact_success(client):
    account = client.post("/accounts", json={"name": "Acme"}).json()
    created = client.post(
        "/contacts", json={"account_id": account["id"], "last_name": "Doe"}
    ).json()
    resp = client.delete(f"/contacts/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/contacts/{created['id']}").status_code == 404


def test_delete_contact_not_found(client):
    resp = client.delete("/contacts/999999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "CONTACT_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: FAIL — `405 Method Not Allowed` on `DELETE /contacts/{id}` (route doesn't exist yet)

- [ ] **Implement**

Append to `src/mock_salesforce/contacts.py`:

```python
@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int) -> None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "CONTACT_NOT_FOUND", "message": f"No contact with id {contact_id}"},
        )
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_contacts.py`
Expected: PASS

- [ ] **Commit**

```bash
git add src/mock_salesforce/contacts.py tests/test_contacts.py
git commit -m "feat(crm-api): add DELETE /contacts/{id}"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan. Gate definitions come from
`.context-index/governance/gates.yaml` (this repo has one), not from the constitution's Quality
Gates section:

- **Test Suite** (`test`, deterministic, required, severity error): `python3 -m pytest -q`
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .`
- **Integration Tests** (`integration-test`, deterministic, required): unwired (`command: ""`
  in `gates.yaml`) — no integration-test suite exists yet in this repo; skipped, not failed.
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-17, plus the two Error
  Cases rows this spec owns beyond its numbered behaviors: `MALFORMED_JSON` and the general
  `VALIDATION_ERROR` shape).

No boundary rules are defined in `.context-index/governance/boundaries.yaml` (empty list) — no
cross-boundary flags apply to this plan's file set.
