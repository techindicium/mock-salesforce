<!-- partial_schema: plan@1 -->

# Implementation Plan: Opportunity MCP tools

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/opportunity-tools.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`require_review: false` for
>   all risk tiers in this repo's `governance/risk-policies.yaml`); treated as a clean pass.
> **Platform:** Python 3.11, no framework mandated (mcp-server is its own process, separate from
>   `crm-api`'s FastAPI app), no ORM, no auth, runs locally only

**Goal:** Add the 5 Opportunity MCP tools (`list_opportunities`, `get_opportunity`,
`create_opportunity`, `update_opportunity`, `delete_opportunity`) to the already-scaffolded
`mcp-server` module, wrapping `crm-api`'s Opportunity endpoints — including `stage_name`
transitions and `account_id`/`stage_name` list filters — per the Live Spec's 9 numbered
behaviors (BEH-1 through BEH-9).

**Architecture:** This spec is the third and final tool-surface spec of the `mcp-server` module.
The module skeleton, the shared `CrmApiClient` HTTP wrapper, `McpUpstreamError` /
`McpUpstreamUnreachableError`, and the `FastMCP` app instance were all built by the sibling
`account-contact-tools` spec and are validated on `main` — this plan adds only a new
`mcp_server/tools/opportunities.py` module and five `@mcp.tool()` registrations in the existing
`mcp_server/app.py`, extending (never duplicating) that scaffolding. No new dependency, no new
top-level file beyond the one tools module and its test suite.

**Testability choice (inherited from the sibling plan, unchanged here):** each tool in `app.py`
stays a plain, directly callable Python function — `@mcp.tool()` over an ordinary type-annotated
function, never a Pydantic input model. Every test in this plan calls either the
`mcp_server/tools/opportunities.py` implementation functions directly (with
`mcp_server.client.CrmApiClient` wired to `httpx.MockTransport` — no real network, no real
`crm-api` process) or the `@mcp.tool()`-decorated wrapper functions in `app.py` directly (for the
BEH-8 missing-required-argument case, asserting Python's own call-binding raises `TypeError`
before the function body — and therefore before any HTTP request — ever runs).

**Field/value source of truth:** `mcp-server` owns no field-level validation itself (per the
charter's Invariants, only "does this field exist" is enforced client-side, everything else —
including the ten fixed `stage_name` values — is `crm-api`'s job). Every tool parameter name and
the `close_date`/`stage_name` handling below mirrors `src/mock_salesforce/models.py`'s
`OpportunityCreate`/`OpportunityUpdate` exactly:
`account_id`, `name`, `stage_name` (defaults to `"Prospecting"` — passed through unset so
`crm-api`'s own Pydantic default applies, never re-implemented here), `amount`, `close_date`
(passed as an ISO date string; `crm-api`'s `date` field parses it), `probability`,
`opportunity_type`, `lead_source`, `next_step`.

---

## File Structure

**Create:**
- `mcp_server/tools/opportunities.py` — plain-function implementations of the 5 Opportunity
  tools
- `tests/mcp_server/test_opportunity_tools.py` — Opportunity tool suite (BEH-1 through BEH-7)

**Modify:**
- `mcp_server/app.py` — add 5 `@mcp.tool()`-decorated wrappers (registered incrementally across
  Tasks 1-4)
- `tests/mcp_server/test_input_validation.py` — extend with `create_opportunity` schema-before-
  HTTP-call cases (BEH-8)
- `tests/mcp_server/test_connection_handling.py` — extend the full-surface connection-error
  check and the tool-registration count to cover all 15 tools (BEH-9)

**Reference (read, do not modify):**
- `src/mock_salesforce/models.py` — `OpportunityCreate`/`OpportunityUpdate` exact field sets, the
  `StageName` literal's ten fixed values, and the `"Prospecting"` default
- `src/mock_salesforce/opportunities.py` — the exact routes (`GET/POST /opportunities`,
  `GET/PATCH/DELETE /opportunities/{id}`), status codes, and `{"error": ..., "message": ...}`
  error body shape this spec's tools wrap
- `.context-index/specs/features/crm-api/opportunity-lifecycle.spec.md` — upstream Error Cases
  table (`OPPORTUNITY_ACCOUNT_NOT_FOUND`, `OPPORTUNITY_NOT_FOUND`, `VALIDATION_ERROR`) — the
  verbatim messages this spec's own Error Cases table (`MCP_UPSTREAM_ERROR`) wraps unchanged
- `mcp_server/client.py`, `mcp_server/errors.py` — already-built, unmodified shared HTTP wrapper
  and error types every tool in this plan reuses as-is
- `mcp_server/tools/accounts.py`, `mcp_server/tools/contacts.py` — established plain-function
  tool-implementation pattern (positional `client` first, keyword-only remaining fields, `None`-
  filtered payload dict) mirrored here for `opportunities.py`
- `.context-index/specs/features/mcp-server/account-contact-tools.plan.md` — this module's own
  established plan-document conventions (task structure, TDD step granularity, full-surface
  BEH-9 check pattern) mirrored here

## Context Packets

No source-manifest exists yet for this spec (its own file is new; the module's supporting files
were stamped by the sibling `account-contact-tools` spec) — packets fall back to the charter's
Capability Map / Domain Model, this spec's own Behavioral Contract, and the upstream
`opportunity-lifecycle` spec's Error Cases table for the exact upstream messages being wrapped.

### Task 1 Context
- Spec: BEH-1, BEH-2
- Charter: Capability Map row "list_opportunities / ... / delete_opportunity tools"; Interface
  Contracts → `list_opportunities`, `get_opportunity`
- Reference: `src/mock_salesforce/opportunities.py` (`GET /opportunities` with optional
  `account_id`/`stage_name` query params, `GET /opportunities/{id}`)

### Task 2 Context
- Spec: BEH-3, BEH-4, BEH-6 (create case), BEH-8 (`create_opportunity` case); Error Cases rows
  `MCP_INPUT_INVALID`, `MCP_UPSTREAM_ERROR`
- Charter: Domain Model → Invariants ("Every McpTool's `input_schema` validates before the
  wrapped HTTP call is made")
- Reference: `src/mock_salesforce/models.py` (`OpportunityCreate` full field list; `StageName`
  literal's ten fixed values; `"Prospecting"` default), `src/mock_salesforce/opportunities.py`
  (`POST /opportunities` route, `OPPORTUNITY_ACCOUNT_NOT_FOUND` 404 shape, `VALIDATION_ERROR` 422
  shape)
- Cross-cutting: `.context-index/specs/features/crm-api/opportunity-lifecycle.spec.md` (Error
  Cases table)

### Task 3 Context
- Spec: BEH-5, BEH-6 (update case)
- Reference: `src/mock_salesforce/models.py` (`OpportunityUpdate` full field list — all optional,
  `account_id` not mutable), `src/mock_salesforce/opportunities.py` (`PATCH /opportunities/{id}`
  route; note the `is_closed`/`is_won` derivation on `stage_name` change is `crm-api`'s
  responsibility alone — `mcp-server` never replicates it)

### Task 4 Context
- Spec: BEH-7, BEH-9 (full-surface); Postconditions ("no caching layer sits between this module
  and the API")
- Charter: Domain Model → Relationships ("Each McpTool maps to exactly one crm-api endpoint")
- Reference: `src/mock_salesforce/opportunities.py` (`DELETE /opportunities/{id}` route, 204
  response)

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4

Every task after Task 1 adds `@mcp.tool()` registrations to the same `mcp_server/app.py`, so
running them concurrently risks merge conflicts on that one shared file — the same reasoning the
sibling `account-contact-tools.plan.md` used to keep its own task groups sequential rather than
mark them independent. This plan makes the same call.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Opportunity read tools (list_opportunities, get_opportunity) | small | unit | — | 2 create, 1 modify |
| 2 | create_opportunity (default stage, 404/422 passthrough, schema validation) | medium | unit | Task 1 | 0 create, 3 modify |
| 3 | update_opportunity (stage_name transitions, 422 passthrough) | small | unit | Task 2 | 0 create, 2 modify |
| 4 | delete_opportunity + full-surface BEH-9/tool-count check | small | unit | Task 3 | 0 create, 4 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no matching `manifest.yaml` `test_strategies` entry, and file paths under
`mcp_server/**` / `tests/mcp_server/**` don't match any non-unit auto-detection heuristic). No
Strategy Summary or Test Infrastructure Requirements section follows, per the omission rule for
all-unit plans with no `infra_requirements:` in the spec — every test in this plan runs fully
offline against an `httpx.MockTransport`, never a real `crm-api` process or network call.

Granularity is resolved once for the whole plan: `test_policy.granularity: per-behavior` in
`manifest.yaml` (source: manifest — no module-level override exists for `mcp-server`). Per this
policy, `tests/mcp_server/test_opportunity_tools.py` is created once (Task 1) and **extended**,
not recreated, by every later task that implements a behavior already covered by that file;
`tests/mcp_server/test_input_validation.py` and `tests/mcp_server/test_connection_handling.py`
(both already existing, stamped by the sibling `account-contact-tools` spec) are **extended**
throughout, never recreated.

## Task Structure

> Per-task `- [ ]` checkboxes are authoring guides only; authoritative task state lives in the
> spec's lifecycle event log (`plan_task` events), not in this markdown. No `Status` column
> appears in any task table in this plan.

### Task 1: Opportunity read tools (list_opportunities, get_opportunity) [specialist: none]

**Charter capability:** `list_opportunities` / `get_opportunity` tools
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/tools/opportunities.py`
- Create (test): `tests/mcp_server/test_opportunity_tools.py`
- Modify: `mcp_server/app.py`

**Tests:** `tests/mcp_server/test_opportunity_tools.py` — new suite (BEH-1, BEH-2)

**Context to load:**
- `.context-index/specs/features/mcp-server/opportunity-tools.spec.md` (BEH-1, BEH-2)
- `src/mock_salesforce/opportunities.py` (`GET /opportunities`, `GET /opportunities/{id}` routes)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_opportunity_tools.py
import httpx

from mcp_server.client import CrmApiClient
from mcp_server.tools import opportunities


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_opportunities_without_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/opportunities"
        assert dict(request.url.params) == {}
        return httpx.Response(200, json=[{"id": 1, "name": "Deal"}])

    client = make_client(handler)
    result = opportunities.list_opportunities(client)
    assert result == [{"id": 1, "name": "Deal"}]


def test_list_opportunities_with_account_id_and_stage_name_filters():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/opportunities"
        assert request.url.params["account_id"] == "7"
        assert request.url.params["stage_name"] == "Qualification"
        return httpx.Response(200, json=[{"id": 1, "account_id": 7}])

    client = make_client(handler)
    result = opportunities.list_opportunities(
        client, account_id=7, stage_name="Qualification"
    )
    assert result == [{"id": 1, "account_id": 7}]


def test_get_opportunity_calls_get_opportunities_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/opportunities/9"
        return httpx.Response(200, json={"id": 9, "name": "Deal"})

    client = make_client(handler)
    result = opportunities.get_opportunity(client, 9)
    assert result == {"id": 9, "name": "Deal"}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.tools.opportunities'`

- [ ] **Implement**

Create `mcp_server/tools/opportunities.py`:

```python
from mcp_server.client import CrmApiClient


def list_opportunities(
    client: CrmApiClient,
    account_id: int | None = None,
    stage_name: str | None = None,
) -> list[dict]:
    params = {}
    if account_id is not None:
        params["account_id"] = account_id
    if stage_name is not None:
        params["stage_name"] = stage_name
    return client.request("GET", "/opportunities", params=params or None)


def get_opportunity(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/opportunities/{id}")
```

Modify `mcp_server/app.py` — add:

```python
from mcp_server.tools import opportunities


@mcp.tool()
def list_opportunities(
    account_id: int | None = None, stage_name: str | None = None
) -> list[dict]:
    """List Opportunities, optionally filtered by `account_id` and/or `stage_name`."""
    return opportunities.list_opportunities(client, account_id, stage_name)


@mcp.tool()
def get_opportunity(id: int) -> dict:
    """Fetch one Opportunity by id."""
    return opportunities.get_opportunity(client, id)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/mcp-server/opportunity-tools`

```bash
git add mcp_server/tools/opportunities.py tests/mcp_server/test_opportunity_tools.py \
  mcp_server/app.py
git commit -m "feat(mcp-server): add list_opportunities and get_opportunity tools"
```

---

### Task 2: create_opportunity (default stage, 404/422 passthrough, schema validation) [specialist: none]

**Charter capability:** `create_opportunity` tool
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `mcp_server/tools/opportunities.py`, `mcp_server/app.py`,
  `tests/mcp_server/test_opportunity_tools.py`, `tests/mcp_server/test_input_validation.py`

**Tests:** `tests/mcp_server/test_opportunity_tools.py` — extend (BEH-3, BEH-4, BEH-6 create
case); `tests/mcp_server/test_input_validation.py` — extend (BEH-8, `create_opportunity` case)

**Context to load:**
- Spec: BEH-3, BEH-4, BEH-6 (create case), BEH-8; Error Cases rows `MCP_INPUT_INVALID`,
  `MCP_UPSTREAM_ERROR`
- Reference: `src/mock_salesforce/models.py` (`OpportunityCreate` full field list, `StageName`
  literal's ten fixed values, `"Prospecting"` default), `src/mock_salesforce/opportunities.py`
  (`POST /opportunities` route, `OPPORTUNITY_ACCOUNT_NOT_FOUND` 404 shape, `VALIDATION_ERROR` 422
  shape)

- [ ] **Write failing test**

Add these imports to the top of `tests/mcp_server/test_opportunity_tools.py`, next to its
existing header (never mid-file — ruff's default rule set includes `E402`, which fails the lint
gate on a non-top-of-file import):

```python
import pytest

from mcp_server.errors import McpUpstreamError
```

Then append these test functions below the existing ones in the same file:

```python
def test_create_opportunity_posts_and_defaults_stage():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/opportunities"
        return httpx.Response(
            201,
            json={
                "id": 1, "account_id": 7, "name": "Big Deal", "stage_name": "Prospecting",
            },
        )

    client = make_client(handler)
    result = opportunities.create_opportunity(
        client, account_id=7, name="Big Deal", close_date="2026-12-01"
    )
    assert result == {
        "id": 1, "account_id": 7, "name": "Big Deal", "stage_name": "Prospecting",
    }


def test_create_opportunity_passes_through_404_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": "OPPORTUNITY_ACCOUNT_NOT_FOUND",
                "message": "No account with id 999999",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.create_opportunity(
            client, account_id=999999, name="Big Deal", close_date="2026-12-01"
        )
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "OPPORTUNITY_ACCOUNT_NOT_FOUND"
    assert exc_info.value.message == "No account with id 999999"


def test_create_opportunity_invalid_stage_name_passes_through_422_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "error": "VALIDATION_ERROR",
                "message": "stage_name must be one of the ten fixed values",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.create_opportunity(
            client, account_id=1, name="Big Deal", close_date="2026-12-01",
            stage_name="Bogus Stage",
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "VALIDATION_ERROR"
```

```python
# tests/mcp_server/test_input_validation.py — add this import to the top, next to the
# existing `from mcp_server.app import create_account, create_contact` line:
from mcp_server.app import create_opportunity
```

Then append these test functions below the existing ones in the same file:

```python
def test_create_opportunity_missing_account_id_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_opportunity(name="Big Deal", close_date="2026-12-01")


def test_create_opportunity_missing_name_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_opportunity(account_id=1, close_date="2026-12-01")


def test_create_opportunity_missing_close_date_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_opportunity(account_id=1, name="Big Deal")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_input_validation.py`
Expected: FAIL — `AttributeError`/`ImportError` (`create_opportunity` doesn't exist yet on
`mcp_server.tools.opportunities` or `mcp_server.app`)

- [ ] **Implement**

Modify `mcp_server/tools/opportunities.py` — add:

```python
def create_opportunity(
    client: CrmApiClient,
    *,
    account_id: int,
    name: str,
    close_date: str,
    stage_name: str | None = None,
    amount: float | None = None,
    probability: float | None = None,
    opportunity_type: str | None = None,
    lead_source: str | None = None,
    next_step: str | None = None,
) -> dict:
    payload = {
        "account_id": account_id,
        "name": name,
        "close_date": close_date,
        "stage_name": stage_name,
        "amount": amount,
        "probability": probability,
        "opportunity_type": opportunity_type,
        "lead_source": lead_source,
        "next_step": next_step,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/opportunities", json=payload)
```

Modify `mcp_server/app.py` — add (full field list mirrors `OpportunityCreate` in
`src/mock_salesforce/models.py`; `stage_name` is passed through unset when not given so
`crm-api`'s own `"Prospecting"` default applies):

```python
@mcp.tool()
def create_opportunity(
    account_id: int,
    name: str,
    close_date: str,
    stage_name: str | None = None,
    amount: float | None = None,
    probability: float | None = None,
    opportunity_type: str | None = None,
    lead_source: str | None = None,
    next_step: str | None = None,
) -> dict:
    """Create an Opportunity under an Account. `account_id`, `name`, and
    `close_date` are required; `stage_name` defaults to Prospecting."""
    return opportunities.create_opportunity(
        client,
        account_id=account_id,
        name=name,
        close_date=close_date,
        stage_name=stage_name,
        amount=amount,
        probability=probability,
        opportunity_type=opportunity_type,
        lead_source=lead_source,
        next_step=next_step,
    )
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_input_validation.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/opportunities.py mcp_server/app.py \
  tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_input_validation.py
git commit -m "feat(mcp-server): add create_opportunity tool"
```

---

### Task 3: update_opportunity (stage_name transitions, 422 passthrough) [specialist: none]

**Charter capability:** `update_opportunity` tool
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `mcp_server/tools/opportunities.py`, `mcp_server/app.py`,
  `tests/mcp_server/test_opportunity_tools.py`

**Tests:** `tests/mcp_server/test_opportunity_tools.py` — extend (BEH-5, BEH-6 update case)

**Context to load:**
- Spec: BEH-5, BEH-6 (update case)
- Reference: `src/mock_salesforce/models.py` (`OpportunityUpdate` full field list — all optional,
  `account_id` not mutable), `src/mock_salesforce/opportunities.py` (`PATCH /opportunities/{id}`
  route)

- [ ] **Write failing test**

Append these test functions to `tests/mcp_server/test_opportunity_tools.py`, below the existing
ones:

```python
def test_update_opportunity_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(200, json={"id": 1, "amount": 50000})

    client = make_client(handler)
    result = opportunities.update_opportunity(client, 1, amount=50000)
    assert result == {"id": 1, "amount": 50000}


def test_update_opportunity_stage_name_transition():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(200, json={"id": 1, "stage_name": "Closed Won"})

    client = make_client(handler)
    result = opportunities.update_opportunity(client, 1, stage_name="Closed Won")
    assert result == {"id": 1, "stage_name": "Closed Won"}


def test_update_opportunity_invalid_stage_name_passes_through_422_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "error": "VALIDATION_ERROR",
                "message": "stage_name must be one of the ten fixed values",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        opportunities.update_opportunity(client, 1, stage_name="Bogus Stage")
    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py`
Expected: FAIL — `AttributeError: module 'mcp_server.tools.opportunities' has no attribute
'update_opportunity'`

- [ ] **Implement**

Modify `mcp_server/tools/opportunities.py` — add:

```python
def update_opportunity(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/opportunities/{id}", json=payload)
```

Modify `mcp_server/app.py` — add (full field list mirrors `OpportunityUpdate` in
`src/mock_salesforce/models.py`; note `account_id` is **not** a parameter — an Opportunity's
owning Account never changes):

```python
@mcp.tool()
def update_opportunity(
    id: int,
    name: str | None = None,
    stage_name: str | None = None,
    amount: float | None = None,
    close_date: str | None = None,
    probability: float | None = None,
    opportunity_type: str | None = None,
    lead_source: str | None = None,
    next_step: str | None = None,
) -> dict:
    """Update one or more mutable Opportunity fields, including `stage_name` transitions."""
    return opportunities.update_opportunity(
        client,
        id,
        name=name,
        stage_name=stage_name,
        amount=amount,
        close_date=close_date,
        probability=probability,
        opportunity_type=opportunity_type,
        lead_source=lead_source,
        next_step=next_step,
    )
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/opportunities.py mcp_server/app.py \
  tests/mcp_server/test_opportunity_tools.py
git commit -m "feat(mcp-server): add update_opportunity tool with stage_name transitions"
```

---

### Task 4: delete_opportunity + full-surface BEH-9/tool-count check [specialist: none]

**Charter capability:** `delete_opportunity` tool; plus cross-cutting BEH-9 completion across all
15 Account/Contact/Opportunity tools and the Domain Model Relationship "Each McpTool maps to
exactly one crm-api endpoint" — folded into this task rather than kept as its own task, since it
needs no production code beyond what this task already adds (a standalone "verification-only"
task would have no genuine red/green TDD cycle: everything it asserts would already pass the
moment it's written, with nothing left to implement)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 3
**Files:**
- Modify: `mcp_server/tools/opportunities.py`, `mcp_server/app.py`,
  `tests/mcp_server/test_opportunity_tools.py`, `tests/mcp_server/test_connection_handling.py`

**Tests:** `tests/mcp_server/test_opportunity_tools.py` — extend (BEH-7);
`tests/mcp_server/test_connection_handling.py` — extend (BEH-9, full 15-tool surface + tool
registration count)

**Context to load:**
- Spec: BEH-7, BEH-9 (full-surface); Postconditions ("no caching layer sits between this module
  and the API")
- Charter: Domain Model → Relationships ("Each McpTool maps to exactly one crm-api endpoint"),
  Invariants
- Reference: `src/mock_salesforce/opportunities.py` (`DELETE /opportunities/{id}` route, 204
  response)

- [ ] **Write failing test**

Append this test function to `tests/mcp_server/test_opportunity_tools.py`, below the existing
ones:

```python
def test_delete_opportunity_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/opportunities/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = opportunities.delete_opportunity(client, 1)
    assert result == {"deleted": True, "id": 1}
```

In `tests/mcp_server/test_connection_handling.py`, add an `OPPORTUNITY_TOOL_CALLS` list right
after the existing `ACCOUNT_AND_CONTACT_TOOL_CALLS` list:

```python
OPPORTUNITY_TOOL_CALLS = [
    lambda: app_module.list_opportunities(),
    lambda: app_module.get_opportunity(id=1),
    lambda: app_module.create_opportunity(
        account_id=1, name="Deal", close_date="2026-12-01"
    ),
    lambda: app_module.update_opportunity(id=1, name="Deal"),
    lambda: app_module.delete_opportunity(id=1),
]
```

Change the existing `test_every_tool_surfaces_a_clear_connection_error`'s loop from
`for call in ACCOUNT_AND_CONTACT_TOOL_CALLS:` to:

```python
    for call in ACCOUNT_AND_CONTACT_TOOL_CALLS + OPPORTUNITY_TOOL_CALLS:
```

Rename the existing `test_all_ten_account_and_contact_tools_registered` to
`test_all_fifteen_tools_registered` and replace its `expected` set with the full 15-tool set:

```python
def test_all_fifteen_tools_registered():
    tool_names = {t.name for t in app_module.mcp._tool_manager.list_tools()}
    expected = {
        "list_accounts", "get_account", "create_account", "update_account", "delete_account",
        "list_contacts", "get_contact", "create_contact", "update_contact", "delete_contact",
        "list_opportunities", "get_opportunity", "create_opportunity", "update_opportunity",
        "delete_opportunity",
    }
    assert tool_names == expected
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_connection_handling.py`
Expected: FAIL — `AttributeError` (`delete_opportunity` doesn't exist yet on
`mcp_server.tools.opportunities` or `mcp_server.app`); the full-surface connection test fails for
the same reason, and the 15-tool registration test fails with only 14 of the 15 expected names
present

- [ ] **Implement**

Modify `mcp_server/tools/opportunities.py` — add:

```python
def delete_opportunity(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/opportunities/{id}")
    return {"deleted": True, "id": id}
```

Modify `mcp_server/app.py` — add:

```python
@mcp.tool()
def delete_opportunity(id: int) -> dict:
    """Delete an Opportunity."""
    return opportunities.delete_opportunity(client, id)
```

Note: this task adds no other production code beyond the two additions above — the full-surface
connection-error test and the 15-tool registration test both pass as a direct consequence of
`mcp_server/tools/opportunities.py` and `mcp_server/app.py` now being complete across all 15
tools; nothing further needs implementing for them specifically.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_connection_handling.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/opportunities.py mcp_server/app.py \
  tests/mcp_server/test_opportunity_tools.py tests/mcp_server/test_connection_handling.py
git commit -m "feat(mcp-server): add delete_opportunity tool and full-surface BEH-9 check"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results
are recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:

- **Test Suite** (required, error): `python3 -m pytest -q`
- **Linter** (required, error): `ruff check .`
- **Integration Tests**: unwired (`command: ""` in `gates.yaml`) — skipped, no integration-test
  suite exists yet in this repo
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-9)
