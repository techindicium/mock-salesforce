<!-- partial_schema: plan@1 -->

# Implementation Plan: Account and Contact MCP tools

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/account-contact-tools.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`require_review: false` for
>   all risk tiers in this repo's `governance/risk-policies.yaml`); treated as a clean pass.
> **Platform:** Python 3.11, no framework mandated (mcp-server is a new, separate process from
>   `crm-api`'s FastAPI app), no ORM, no auth, runs locally only

**Goal:** Stand up the `mcp-server` module — a brand-new top-level process, separate from
`crm-api` — exposing all 10 Account/Contact CRUD operations (5 Account tools, 5 Contact tools)
as MCP tools over Streamable HTTP transport, wrapping `crm-api`'s HTTP endpoints with schema
validation, verbatim error passthrough, and clear connection-error handling per the Live Spec's
9 numbered behaviors (BEH-1 through BEH-9 — note this is a *behavior* count, not a tool count;
several behaviors, e.g. BEH-7, cover more than one tool).

**Architecture:** This is the first spec of the `mcp-server` module and the first spec of the
whole module to be planned, so — mirroring how `crm-api/account-and-contact-management.plan.md`
bootstrapped its own module — this plan also bootstraps `mcp-server`'s project skeleton: a new
top-level `mcp_server/` package (parallel to `src/mock_salesforce/`, never importing from it —
per the charter, `mcp-server` is "a pure client of `crm-api`" reached only over HTTP), its own
`mcp_server/requirements.txt` (the deployment charter's `docker-packaging.spec.md` expects two
separate images/containers, so `mcp-server` needs its own dependency manifest rather than
sharing `crm-api`'s root `requirements.txt`), and the shared HTTP client wrapper every tool goes
through.

**SDK choice:** the official Python MCP SDK (`mcp` package, `mcp.server.fastmcp.FastMCP`) is
used, per the charter's explicit choice of Streamable HTTP transport (a network-reachable,
long-running, containerizable, health-checkable process — deliberately not stdio). `FastMCP`
supports Streamable HTTP transport natively (`mcp.run(transport="streamable-http")` /
`mcp.streamable_http_app()`) and registers tools via a plain `@mcp.tool()` decorator over a
normal, type-annotated Python function — no separate JSON-Schema authoring needed, matching the
charter's "structured, JSON-schema tool input/output definitions... without out-of-band
documentation" requirement. **Confirm the exact decorator/settings surface (e.g. how `PORT` is
passed to `FastMCP`) against whatever `mcp` version actually resolves at implementation time** —
this plan was written without network access to verify the installed package's precise API, so
Task 1's implementer should sanity-check the constructor/run() signature against the installed
version's own docs/source before finalizing that one wiring line. If `mcp` cannot be installed in
the implementation environment for any reason, the fallback is a minimal hand-rolled Streamable
HTTP JSON-RPC shim over Starlette — a genuine risk worth flagging up front, but not something
this plan builds in parallel; the official SDK is the primary, and only, path taken here.

**Testability choice (deliberate, drives every task below):** each MCP-facing tool in `app.py` is
kept as a **plain, directly callable Python function** — `@mcp.tool()` decorators over ordinary
functions, not wrapped in Pydantic input models and not requiring any FastMCP transport
machinery to invoke in tests. This lets every test in this plan call the registered tool
functions (and the plain-function tool *implementations* they delegate to, in
`mcp_server/tools/`) directly, with zero dependency on `mcp` SDK internals:
- **BEH-1 through BEH-7, BEH-9** (the actual HTTP wrapping + verbatim error passthrough + clear
  connection-error message) are tested by calling the `mcp_server/tools/*.py` implementation
  functions directly, with `mcp_server.client.CrmApiClient` wired to `httpx.MockTransport` (no
  real network, no real `crm-api` process needed).
- **BEH-8** (schema-invalid input errors before any HTTP call) is tested by calling the
  `@mcp.tool()`-decorated wrapper functions in `app.py` directly with a required argument
  omitted, and asserting Python's own call-binding raises `TypeError` — proving the argument has
  no default in the function signature FastMCP introspects to build the tool's JSON Schema, so
  the *real* MCP-protocol path (which this plan does not re-implement in tests) rejects the call
  before ever reaching the function body, and therefore before any HTTP request.

---

## File Structure

**Create:**
- `mcp_server/__init__.py` — empty package marker
- `mcp_server/requirements.txt` — `mcp`, `httpx`, `uvicorn[standard]` (pin exact versions
  resolved at implementation time, matching this repo's existing exact-pin convention in the
  root `requirements.txt`)
- `mcp_server/errors.py` — `McpUpstreamError` (verbatim status/error-code/message from a
  `crm-api` 4xx/5xx JSON body) and `McpUpstreamUnreachableError` (connection-level failure)
- `mcp_server/client.py` — `CrmApiClient`: a thin synchronous `httpx.Client` wrapper reading
  `API_BASE_URL` from the environment; the single place BEH-9 and the Error Cases table's
  verbatim-passthrough rule are implemented
- `mcp_server/app.py` — `FastMCP` instance, the shared `CrmApiClient` instance, and every
  `@mcp.tool()`-decorated wrapper (registered incrementally across Tasks 2-5); `main()` running
  the Streamable HTTP transport, reading `PORT` from the environment
- `mcp_server/tools/__init__.py` — empty package marker
- `mcp_server/tools/accounts.py` — plain-function implementations of the 5 Account tools
- `mcp_server/tools/contacts.py` — plain-function implementations of the 5 Contact tools
- `tests/mcp_server/test_connection_handling.py` — `CrmApiClient` connection-error and
  verbatim-error-passthrough suite (BEH-9; extended by Task 5 for full-surface coverage)
- `tests/mcp_server/test_account_tools.py` — Account tool suite (BEH-1 through BEH-5)
- `tests/mcp_server/test_contact_tools.py` — Contact tool suite (BEH-6, BEH-7)
- `tests/mcp_server/test_input_validation.py` — schema-before-HTTP-call suite (BEH-8)

**Modify:**
- `pyproject.toml` — add `"."` to `[tool.pytest.ini_options] pythonpath` (currently `["src"]`)
  so `tests/mcp_server/**` can `import mcp_server...`; `mcp_server/` lives at the repo root,
  parallel to `src/`, not inside it

**Reference (read, do not modify):**
- `src/mock_salesforce/models.py` — the exact `AccountCreate`/`AccountUpdate`/`ContactCreate`/
  `ContactUpdate` field sets and the `AccountType` literal values; every MCP tool's parameter
  list must mirror these fields exactly, since `mcp-server` owns no validation logic of its own
  beyond "does this field exist" — `crm-api` is still the sole source of field-level validation
  (e.g. the `account_type` enum) per BEH-8's own scope (missing required field only)
- `src/mock_salesforce/accounts.py`, `src/mock_salesforce/contacts.py` — the exact routes
  (`GET/POST /accounts`, `GET/PATCH/DELETE /accounts/{id}`, `GET/POST /contacts`,
  `GET/PATCH/DELETE /contacts/{id}`), status codes, and `{"error": ..., "message": ...}` error
  body shape these tools wrap
- `.context-index/specs/features/crm-api/account-and-contact-management.spec.md` — upstream
  Error Cases table (`ACCOUNT_NOT_FOUND`, `ACCOUNT_HAS_DEPENDENTS`, `CONTACT_ACCOUNT_NOT_FOUND`,
  `CONTACT_NOT_FOUND`, `VALIDATION_ERROR`) — these are the verbatim messages this spec's own
  Error Cases table (`MCP_UPSTREAM_ERROR`) wraps unchanged
- `tests/conftest.py` — existing `crm-api` test fixture convention (not reused directly here,
  since `mcp-server` tests never boot a real `crm-api` process, but kept as a style reference)
- `.context-index/specs/features/crm-api/account-and-contact-management.plan.md` — this repo's
  established plan-document conventions (task structure, TDD step granularity) mirrored here

## Context Packets

No source-manifest exists yet for this spec (greenfield module) — packets fall back to the
charter's Domain Model / Capability Map, this spec's own Behavioral Contract, and the upstream
`crm-api` spec's Error Cases table for the exact upstream messages being wrapped.

### Task 1 Context
- Spec: Preconditions (`API_BASE_URL`, `PORT` env vars; Streamable HTTP transport); Error Cases
  row `MCP_UPSTREAM_UNREACHABLE`; BEH-9
- Charter: `.context-index/specs/features/mcp-server/charter.md` (Scope and Boundaries →
  Streamable HTTP transport rationale; Domain Model → McpTool entity)
- Constitution: `.context-index/constitution.md` (Coding Standards → Language and Runtime;
  "fail at the HTTP boundary with a real Salesforce-shaped error response" — mirrored here as
  "never swallow the upstream error, never crash on a dropped connection")
- Cross-cutting: `.context-index/specs/cross-cutting/docker-packaging.spec.md` (BEH-2, BEH-6 —
  `mcp-server` reads `API_BASE_URL`/`PORT` from env; not built in this plan, but the env-var
  contract this plan's `client.py`/`app.py` must honor so that spec's plan needs no rework here)

### Task 2 Context
- Spec: BEH-1, BEH-2
- Charter: Capability Map row "list_accounts / ... / delete_account tools"; Interface Contracts
  → `list_accounts`, `get_account`

### Task 3 Context
- Spec: BEH-3, BEH-4, BEH-5, BEH-8 (create_account case); Error Cases rows
  `MCP_INPUT_INVALID`, `MCP_UPSTREAM_ERROR`
- Charter: Domain Model → Invariants ("Every McpTool's `input_schema` validates before the
  wrapped HTTP call is made")

### Task 4 Context
- Spec: BEH-6, BEH-7 (get_contact half)
- Charter: Interface Contracts → `list_contacts`, `get_contact`

### Task 5 Context
- Spec: BEH-7 (create/update/delete half), BEH-8 (create_contact case), BEH-9 (full-surface);
  Postconditions ("no caching layer sits between this module and the API")
- Charter: Domain Model → Relationships ("Each McpTool maps to exactly one crm-api endpoint";
  "no tool spans more than one endpoint call")

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5

Account tools (Tasks 2-3) and Contact tools (Tasks 4-5) are logically independent domains, but
every task after Task 1 adds `@mcp.tool()` registrations to the same `mcp_server/app.py`, so
running them concurrently risks merge conflicts on that one shared file — the same reasoning
`crm-api`'s own `account-and-contact-management.plan.md` used to keep its Account/Contact task
groups sequential rather than mark them `independent`. This plan makes the same call.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | mcp-server scaffold & crm-api client wrapper | medium | unit | — | 6 create, 1 modify |
| 2 | Account read tools (list_accounts, get_account) | small | unit | Task 1 | 3 create, 1 modify |
| 3 | Account write tools (create/update/delete_account) | medium | unit | Task 2 | 1 create, 3 modify |
| 4 | Contact read tools (list_contacts, get_contact) | small | unit | Task 3 | 2 create, 1 modify |
| 5 | Contact write tools + full-surface BEH-9/tool-count check | medium | unit | Task 4 | 0 create, 5 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no matching `manifest.yaml` `test_strategies` entry, and file paths under
`mcp_server/**` / `tests/mcp_server/**` don't match any non-unit auto-detection heuristic). No
Strategy Summary or Test Infrastructure Requirements section follows, per the omission rule for
all-unit plans with no `infra_requirements:` in the spec — every test in this plan runs fully
offline against an `httpx.MockTransport`, never a real `crm-api` process or network call.

Granularity is resolved once for the whole plan: `test_policy.granularity: per-behavior` in
`manifest.yaml` (source: manifest — no module-level override exists for `mcp-server`). Per this
policy, `tests/mcp_server/test_account_tools.py`, `tests/mcp_server/test_contact_tools.py`,
`tests/mcp_server/test_connection_handling.py`, and `tests/mcp_server/test_input_validation.py`
are each created once and **extended**, not recreated, by every later task that implements a
behavior already covered by that file.

## Task Structure

> Per-task `- [ ]` checkboxes are authoring guides only; authoritative task state lives in the
> spec's lifecycle event log (`plan_task` events), not in this markdown. No `Status` column
> appears in any task table in this plan.

### Task 1: mcp-server scaffold & crm-api client wrapper [specialist: none]

**Charter capability:** foundation for all Account/Contact tool capabilities
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/__init__.py`, `mcp_server/requirements.txt`, `mcp_server/errors.py`,
  `mcp_server/client.py`, `mcp_server/app.py`
- Create (test): `tests/mcp_server/test_connection_handling.py`
- Modify: `pyproject.toml`

**Tests:** `tests/mcp_server/test_connection_handling.py` — new suite (BEH-9)

**Context to load:**
- `.context-index/specs/features/mcp-server/account-contact-tools.spec.md` (Preconditions,
  BEH-9, Error Cases row `MCP_UPSTREAM_UNREACHABLE`)
- `.context-index/specs/features/mcp-server/charter.md` (Scope and Boundaries → Streamable HTTP
  transport rationale)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_connection_handling.py
import httpx
import pytest

from mcp_server.client import CrmApiClient
from mcp_server.errors import McpUpstreamError, McpUpstreamUnreachableError


def test_connect_error_raises_clear_unreachable_message():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(McpUpstreamUnreachableError) as exc_info:
        client.request("GET", "/accounts")
    assert "crm-api.test" in str(exc_info.value)


def test_upstream_error_status_carries_verbatim_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404, json={"error": "ACCOUNT_NOT_FOUND", "message": "No account with id 99"}
        )

    client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )

    with pytest.raises(McpUpstreamError) as exc_info:
        client.request("GET", "/accounts/99")
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "ACCOUNT_NOT_FOUND"
    assert exc_info.value.message == "No account with id 99"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_connection_handling.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server'` (package doesn't exist yet)

- [ ] **Implement**

Create `mcp_server/requirements.txt`:

```
mcp==1.9.4
httpx==0.28.1
uvicorn[standard]==0.52.4
```

Create `mcp_server/errors.py`:

```python
class McpUpstreamError(Exception):
    """A crm-api HTTP call returned a 4xx/5xx response. Carries the upstream
    error code/message verbatim so tool callers see it unchanged (never
    swallowed or rewritten — see the mcp-server charter's Invariants)."""

    def __init__(self, status_code: int, error_code: str | None, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class McpUpstreamUnreachableError(Exception):
    """crm-api could not be reached at all (connection refused, DNS failure,
    timeout) — raised instead of letting a raw httpx exception surface."""
```

Create `mcp_server/client.py`:

```python
import os

import httpx

from mcp_server.errors import McpUpstreamError, McpUpstreamUnreachableError


class CrmApiClient:
    """Thin synchronous wrapper around crm-api's HTTP surface. Every MCP tool
    goes through this so BEH-9 and the verbatim-passthrough rule are
    satisfied in exactly one place, never reimplemented per tool."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        # A default (rather than a bare `os.environ["API_BASE_URL"]` subscript)
        # is deliberate: `mcp_server/app.py` builds a module-level `client =
        # CrmApiClient()` at import time, and every test in this plan imports
        # `mcp_server.app`. A missing env var must not raise `KeyError` during
        # pytest collection and take down the whole `python3 -m pytest -q`
        # gate — mirrors `src/mock_salesforce/db.py`'s
        # `os.environ.get("DB_PATH", "mock_salesforce.db")` default pattern.
        self.base_url = (
            base_url or os.environ.get("API_BASE_URL", "http://localhost:8000")
        ).rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, transport=transport)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list | None:
        try:
            resp = self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise McpUpstreamUnreachableError(
                f"Cannot reach crm-api at {self.base_url}: {exc}"
            ) from exc
        if resp.status_code >= 400:
            body = resp.json() if resp.content else {}
            raise McpUpstreamError(
                resp.status_code, body.get("error"), body.get("message", resp.text)
            )
        return resp.json() if resp.content else None

    def close(self) -> None:
        self._client.close()
```

Create `mcp_server/app.py` (tool registrations added incrementally in Tasks 2-5; no tools
registered yet):

```python
import os

from mcp.server.fastmcp import FastMCP

from mcp_server.client import CrmApiClient

# NOTE: confirm the exact FastMCP constructor/settings field for reading PORT
# against the installed `mcp` SDK version — this line is written for the
# general shape documented by the SDK, not verified against a pinned release.
mcp = FastMCP("mock-salesforce-crm", port=int(os.environ.get("PORT", "8000")))
client = CrmApiClient()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
```

Modify `pyproject.toml`: change `pythonpath = ["src"]` to `pythonpath = ["src", "."]`.

Install `mcp_server`'s dependencies into the same environment the root quality gate uses (this
course-fixture repo runs one shared venv, not two separate ones, per the governance posture's
"single operator" stance):

```bash
pip install -r mcp_server/requirements.txt
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_connection_handling.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/mcp-server/account-contact-tools-scaffolding`

```bash
git add mcp_server/__init__.py mcp_server/requirements.txt mcp_server/errors.py \
  mcp_server/client.py mcp_server/app.py tests/mcp_server/test_connection_handling.py \
  pyproject.toml
git commit -m "feat(mcp-server): scaffold module and crm-api client wrapper"
```

---

### Task 2: Account read tools (list_accounts, get_account) [specialist: none]

**Charter capability:** `list_accounts` / `get_account` tools
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `mcp_server/tools/__init__.py`, `mcp_server/tools/accounts.py`
- Create (test): `tests/mcp_server/test_account_tools.py`
- Modify: `mcp_server/app.py`

**Tests:** `tests/mcp_server/test_account_tools.py` — new suite (BEH-1, BEH-2)

**Context to load:**
- Spec: BEH-1, BEH-2
- Reference: `src/mock_salesforce/accounts.py` (`GET /accounts`, `GET /accounts/{id}` routes)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_account_tools.py
import httpx

from mcp_server.client import CrmApiClient
from mcp_server.tools import accounts


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_accounts_calls_get_accounts_and_returns_unmodified():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json=[{"id": 1, "name": "Acme"}])

    client = make_client(handler)
    result = accounts.list_accounts(client)

    assert seen == {"method": "GET", "path": "/accounts"}
    assert result == [{"id": 1, "name": "Acme"}]


def test_get_account_calls_get_accounts_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/accounts/42"
        return httpx.Response(200, json={"id": 42, "name": "Acme"})

    client = make_client(handler)
    result = accounts.get_account(client, 42)
    assert result == {"id": 42, "name": "Acme"}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_account_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.tools'`

- [ ] **Implement**

Create `mcp_server/tools/accounts.py`:

```python
from mcp_server.client import CrmApiClient


def list_accounts(client: CrmApiClient) -> list[dict]:
    return client.request("GET", "/accounts")


def get_account(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/accounts/{id}")
```

Modify `mcp_server/app.py` — add:

```python
from mcp_server.tools import accounts


@mcp.tool()
def list_accounts() -> list[dict]:
    """List every Account."""
    return accounts.list_accounts(client)


@mcp.tool()
def get_account(id: int) -> dict:
    """Fetch one Account by id."""
    return accounts.get_account(client, id)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_account_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/__init__.py mcp_server/tools/accounts.py \
  tests/mcp_server/test_account_tools.py mcp_server/app.py
git commit -m "feat(mcp-server): add list_accounts and get_account tools"
```

---

### Task 3: Account write tools (create/update/delete_account) [specialist: none]

**Charter capability:** `create_account` / `update_account` / `delete_account` tools
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Create (test): `tests/mcp_server/test_input_validation.py`
- Modify: `mcp_server/tools/accounts.py`, `mcp_server/app.py`,
  `tests/mcp_server/test_account_tools.py`

**Tests:** `tests/mcp_server/test_account_tools.py` — extend (BEH-3, BEH-4, BEH-5);
`tests/mcp_server/test_input_validation.py` — new suite (BEH-8, create_account case)

**Context to load:**
- Spec: BEH-3, BEH-4, BEH-5, BEH-8; Error Cases rows `MCP_INPUT_INVALID`, `MCP_UPSTREAM_ERROR`
- Reference: `src/mock_salesforce/models.py` (`AccountCreate`/`AccountUpdate` full field list),
  `src/mock_salesforce/accounts.py` (`POST`/`PATCH`/`DELETE /accounts` routes,
  `ACCOUNT_HAS_DEPENDENTS` 409 shape)

- [ ] **Write failing test**

Add these two imports to the top of `tests/mcp_server/test_account_tools.py`, next to its
existing `import httpx` / `from mcp_server...` header (never mid-file — ruff's default rule set
includes `E402`, which fails the lint gate on a non-top-of-file import):

```python
import pytest

from mcp_server.errors import McpUpstreamError
```

Then append these test functions below the existing ones in the same file:

```python
def test_create_account_posts_and_returns_created():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/accounts"
        return httpx.Response(201, json={"id": 1, "name": "Acme"})

    client = make_client(handler)
    result = accounts.create_account(client, name="Acme")
    assert result == {"id": 1, "name": "Acme"}


def test_update_account_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/accounts/1"
        return httpx.Response(200, json={"id": 1, "name": "New Name"})

    client = make_client(handler)
    result = accounts.update_account(client, 1, name="New Name")
    assert result == {"id": 1, "name": "New Name"}


def test_delete_account_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/accounts/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = accounts.delete_account(client, 1)
    assert result == {"deleted": True, "id": 1}


def test_delete_account_passes_through_409_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "error": "ACCOUNT_HAS_DEPENDENTS",
                "message": "Account 1 has 2 dependent record(s)",
            },
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        accounts.delete_account(client, 1)
    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "ACCOUNT_HAS_DEPENDENTS"
    assert exc_info.value.message == "Account 1 has 2 dependent record(s)"
```

```python
# tests/mcp_server/test_input_validation.py
import inspect

import pytest

from mcp_server.app import create_account


def test_create_account_missing_name_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_account()  # `name` has no default — enforced at call time,
        # standing in for FastMCP's own schema-derived rejection of a tool
        # call missing a required argument, before the function body (and
        # therefore any HTTP request) ever runs.


def test_create_account_name_is_required_in_signature():
    sig = inspect.signature(create_account)
    assert sig.parameters["name"].default is inspect.Parameter.empty
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_account_tools.py tests/mcp_server/test_input_validation.py`
Expected: FAIL — `AttributeError`/`ImportError` (create_account/update_account/delete_account
don't exist yet)

- [ ] **Implement**

Modify `mcp_server/tools/accounts.py` — add:

```python
def create_account(
    client: CrmApiClient,
    *,
    name: str,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
) -> dict:
    payload = {
        "name": name,
        "account_type": account_type,
        "industry": industry,
        "website": website,
        "phone": phone,
        "billing_street": billing_street,
        "billing_city": billing_city,
        "billing_state": billing_state,
        "billing_postal_code": billing_postal_code,
        "billing_country": billing_country,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/accounts", json=payload)


def update_account(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/accounts/{id}", json=payload)


def delete_account(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/accounts/{id}")
    return {"deleted": True, "id": id}
```

Modify `mcp_server/app.py` — add (full field list mirrors `AccountCreate`/`AccountUpdate` in
`src/mock_salesforce/models.py`):

```python
@mcp.tool()
def create_account(
    name: str,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
) -> dict:
    """Create an Account. `name` is required."""
    return accounts.create_account(
        client,
        name=name,
        account_type=account_type,
        industry=industry,
        website=website,
        phone=phone,
        billing_street=billing_street,
        billing_city=billing_city,
        billing_state=billing_state,
        billing_postal_code=billing_postal_code,
        billing_country=billing_country,
    )


@mcp.tool()
def update_account(
    id: int,
    name: str | None = None,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    billing_street: str | None = None,
    billing_city: str | None = None,
    billing_state: str | None = None,
    billing_postal_code: str | None = None,
    billing_country: str | None = None,
) -> dict:
    """Update one or more mutable Account fields."""
    return accounts.update_account(
        client,
        id,
        name=name,
        account_type=account_type,
        industry=industry,
        website=website,
        phone=phone,
        billing_street=billing_street,
        billing_city=billing_city,
        billing_state=billing_state,
        billing_postal_code=billing_postal_code,
        billing_country=billing_country,
    )


@mcp.tool()
def delete_account(id: int) -> dict:
    """Delete an Account. Errors verbatim with 409/ACCOUNT_HAS_DEPENDENTS if it
    still has Contacts or Opportunities."""
    return accounts.delete_account(client, id)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_account_tools.py tests/mcp_server/test_input_validation.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/accounts.py mcp_server/app.py \
  tests/mcp_server/test_account_tools.py tests/mcp_server/test_input_validation.py
git commit -m "feat(mcp-server): add create/update/delete_account tools"
```

---

### Task 4: Contact read tools (list_contacts, get_contact) [specialist: none]

**Charter capability:** `list_contacts` / `get_contact` tools
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 3
**Files:**
- Create: `mcp_server/tools/contacts.py`
- Create (test): `tests/mcp_server/test_contact_tools.py`
- Modify: `mcp_server/app.py`

**Tests:** `tests/mcp_server/test_contact_tools.py` — new suite (BEH-6, BEH-7 read half)

**Context to load:**
- Spec: BEH-6, BEH-7 (get_contact half)
- Reference: `src/mock_salesforce/contacts.py` (`GET /contacts` with optional `account_id`
  query param, `GET /contacts/{id}`)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_contact_tools.py
import httpx

from mcp_server.client import CrmApiClient
from mcp_server.tools import contacts


def make_client(handler) -> CrmApiClient:
    return CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )


def test_list_contacts_without_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/contacts"
        assert dict(request.url.params) == {}
        return httpx.Response(200, json=[{"id": 1, "last_name": "Doe"}])

    client = make_client(handler)
    result = contacts.list_contacts(client)
    assert result == [{"id": 1, "last_name": "Doe"}]


def test_list_contacts_with_account_id_filter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/contacts"
        assert request.url.params["account_id"] == "7"
        return httpx.Response(200, json=[{"id": 1, "account_id": 7}])

    client = make_client(handler)
    result = contacts.list_contacts(client, account_id=7)
    assert result == [{"id": 1, "account_id": 7}]


def test_get_contact_calls_get_contacts_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/contacts/9"
        return httpx.Response(200, json={"id": 9, "last_name": "Doe"})

    client = make_client(handler)
    result = contacts.get_contact(client, 9)
    assert result == {"id": 9, "last_name": "Doe"}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_contact_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.tools.contacts'`

- [ ] **Implement**

Create `mcp_server/tools/contacts.py`:

```python
from mcp_server.client import CrmApiClient


def list_contacts(client: CrmApiClient, account_id: int | None = None) -> list[dict]:
    params = {"account_id": account_id} if account_id is not None else None
    return client.request("GET", "/contacts", params=params)


def get_contact(client: CrmApiClient, id: int) -> dict:
    return client.request("GET", f"/contacts/{id}")
```

Modify `mcp_server/app.py` — add:

```python
from mcp_server.tools import contacts


@mcp.tool()
def list_contacts(account_id: int | None = None) -> list[dict]:
    """List Contacts, optionally filtered by `account_id`."""
    return contacts.list_contacts(client, account_id)


@mcp.tool()
def get_contact(id: int) -> dict:
    """Fetch one Contact by id."""
    return contacts.get_contact(client, id)
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_contact_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/contacts.py tests/mcp_server/test_contact_tools.py mcp_server/app.py
git commit -m "feat(mcp-server): add list_contacts and get_contact tools"
```

---

### Task 5: Contact write tools (create/update/delete_contact) + full-surface BEH-9 check [specialist: none]

**Charter capability:** `create_contact` / `update_contact` / `delete_contact` tools; plus
cross-cutting BEH-9 completion across all 10 Account/Contact tools and the Domain Model
Relationship "Each McpTool maps to exactly one crm-api endpoint" — folded into this task rather
than kept as its own task, since it needs no production code beyond what this task already adds
(a standalone "verification-only" task would have no genuine red/green TDD cycle: everything it
asserts would already pass the moment it's written, with nothing left to implement)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Modify: `mcp_server/tools/contacts.py`, `mcp_server/app.py`,
  `tests/mcp_server/test_contact_tools.py`, `tests/mcp_server/test_input_validation.py`,
  `tests/mcp_server/test_connection_handling.py`

**Tests:** `tests/mcp_server/test_contact_tools.py` — extend (BEH-7 write half);
`tests/mcp_server/test_input_validation.py` — extend (BEH-8, create_contact case);
`tests/mcp_server/test_connection_handling.py` — extend (BEH-9, full 10-tool surface + tool
registration count)

**Context to load:**
- Spec: BEH-7 (create/update/delete half), BEH-8, BEH-9 (full-surface); Postconditions ("no
  caching layer sits between this module and the API")
- Charter: Domain Model → Relationships ("Each McpTool maps to exactly one crm-api endpoint"),
  Invariants
- Reference: `src/mock_salesforce/models.py` (`ContactCreate`/`ContactUpdate` field list —
  `account_id` and `last_name` required on create, never mutable after; note
  `account_id` is **not** a parameter of `update_contact`), `src/mock_salesforce/contacts.py`
  (`CONTACT_ACCOUNT_NOT_FOUND` 404 on unknown `account_id`)

- [ ] **Write failing test**

Add these two imports to the top of `tests/mcp_server/test_contact_tools.py`, next to its
existing header (never mid-file — ruff's default rule set includes `E402`, which fails the lint
gate on a non-top-of-file import):

```python
import pytest

from mcp_server.errors import McpUpstreamError
```

Then append these test functions below the existing ones in the same file:

```python
def test_create_contact_posts_and_returns_created():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/contacts"
        return httpx.Response(201, json={"id": 1, "account_id": 7, "last_name": "Doe"})

    client = make_client(handler)
    result = contacts.create_contact(client, account_id=7, last_name="Doe")
    assert result == {"id": 1, "account_id": 7, "last_name": "Doe"}


def test_create_contact_passes_through_404_verbatim():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": "CONTACT_ACCOUNT_NOT_FOUND", "message": "No account with id 99"},
        )

    client = make_client(handler)
    with pytest.raises(McpUpstreamError) as exc_info:
        contacts.create_contact(client, account_id=99, last_name="Doe")
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "CONTACT_ACCOUNT_NOT_FOUND"


def test_update_contact_patches_and_returns_updated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/contacts/1"
        return httpx.Response(200, json={"id": 1, "last_name": "New Name"})

    client = make_client(handler)
    result = contacts.update_contact(client, 1, last_name="New Name")
    assert result == {"id": 1, "last_name": "New Name"}


def test_delete_contact_confirms_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/contacts/1"
        return httpx.Response(204)

    client = make_client(handler)
    result = contacts.delete_contact(client, 1)
    assert result == {"deleted": True, "id": 1}
```

Add this import to the top of `tests/mcp_server/test_input_validation.py`, next to its existing
header:

```python
from mcp_server.app import create_contact
```

Then append these test functions below the existing ones in the same file:

```python
def test_create_contact_missing_account_id_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_contact(last_name="Doe")


def test_create_contact_missing_last_name_errors_before_any_http_call():
    with pytest.raises(TypeError):
        create_contact(account_id=7)
```

Add these imports to the top of `tests/mcp_server/test_connection_handling.py` (created in Task
1), next to its existing header:

```python
import mcp_server.app as app_module
```

Then append this full-surface BEH-9 check and tool-registration smoke check below the existing
tests in the same file — both genuinely fail right now, before this task's Implement step below,
because `create_contact`, `update_contact`, and `delete_contact` don't exist yet on
`mcp_server.app`:

```python
ACCOUNT_AND_CONTACT_TOOL_CALLS = [
    lambda: app_module.list_accounts(),
    lambda: app_module.get_account(id=1),
    lambda: app_module.create_account(name="Acme"),
    lambda: app_module.update_account(id=1, name="Acme"),
    lambda: app_module.delete_account(id=1),
    lambda: app_module.list_contacts(),
    lambda: app_module.get_contact(id=1),
    lambda: app_module.create_contact(account_id=1, last_name="Doe"),
    lambda: app_module.update_contact(id=1, last_name="Doe"),
    lambda: app_module.delete_contact(id=1),
]


def test_every_tool_surfaces_a_clear_connection_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    unreachable_client = CrmApiClient(
        base_url="http://crm-api.test", transport=httpx.MockTransport(handler)
    )
    monkeypatch.setattr(app_module, "client", unreachable_client)

    for call in ACCOUNT_AND_CONTACT_TOOL_CALLS:
        with pytest.raises(McpUpstreamUnreachableError):
            call()


def test_all_ten_account_and_contact_tools_registered():
    tool_names = {t.name for t in app_module.mcp._tool_manager.list_tools()}
    expected = {
        "list_accounts", "get_account", "create_account", "update_account", "delete_account",
        "list_contacts", "get_contact", "create_contact", "update_contact", "delete_contact",
    }
    assert expected.issubset(tool_names)
    # NOTE: confirm `mcp._tool_manager.list_tools()` (or the installed SDK
    # version's equivalent introspection surface) against the actual `mcp`
    # package resolved during implementation — if the attribute name differs,
    # adjust this assertion to whatever the installed FastMCP exposes for
    # "list registered tools," rather than skipping the check.
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_contact_tools.py tests/mcp_server/test_input_validation.py tests/mcp_server/test_connection_handling.py`
Expected: FAIL — `AttributeError` (create_contact/update_contact/delete_contact don't exist yet
on `mcp_server.tools.contacts` or `mcp_server.app`); the full-surface connection test fails for
the same reason (the lambdas referencing `app_module.create_contact` etc. raise `AttributeError`
instead of the expected `McpUpstreamUnreachableError`), and the tool-count test fails with only
7 of the 10 expected names present

- [ ] **Implement**

Modify `mcp_server/tools/contacts.py` — add:

```python
def create_contact(
    client: CrmApiClient,
    *,
    account_id: int,
    last_name: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    payload = {
        "account_id": account_id,
        "last_name": last_name,
        "first_name": first_name,
        "email": email,
        "phone": phone,
        "title": title,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return client.request("POST", "/contacts", json=payload)


def update_contact(client: CrmApiClient, id: int, **fields) -> dict:
    payload = {k: v for k, v in fields.items() if v is not None}
    return client.request("PATCH", f"/contacts/{id}", json=payload)


def delete_contact(client: CrmApiClient, id: int) -> dict:
    client.request("DELETE", f"/contacts/{id}")
    return {"deleted": True, "id": id}
```

Modify `mcp_server/app.py` — add (note `update_contact` has no `account_id` parameter — a
Contact's owning Account never changes, per the upstream spec's Postconditions):

```python
@mcp.tool()
def create_contact(
    account_id: int,
    last_name: str,
    first_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    """Create a Contact under an Account. `account_id` and `last_name` are required."""
    return contacts.create_contact(
        client,
        account_id=account_id,
        last_name=last_name,
        first_name=first_name,
        email=email,
        phone=phone,
        title=title,
    )


@mcp.tool()
def update_contact(
    id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    title: str | None = None,
) -> dict:
    """Update one or more mutable Contact fields."""
    return contacts.update_contact(
        client,
        id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        title=title,
    )


@mcp.tool()
def delete_contact(id: int) -> dict:
    """Delete a Contact."""
    return contacts.delete_contact(client, id)
```

Note: this task adds no other production code beyond `mcp_server/tools/contacts.py` and
`mcp_server/app.py` above — the full-surface connection-error test and the tool-registration
count test both pass as a direct consequence of those two files now being complete across all
10 tools; nothing further needs implementing for them specifically.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_contact_tools.py tests/mcp_server/test_input_validation.py tests/mcp_server/test_connection_handling.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/contacts.py mcp_server/app.py \
  tests/mcp_server/test_contact_tools.py tests/mcp_server/test_input_validation.py \
  tests/mcp_server/test_connection_handling.py
git commit -m "feat(mcp-server): add create/update/delete_contact tools and full-surface BEH-9 check"
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
