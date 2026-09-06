<!-- partial_schema: plan@1 -->

# Implementation Plan: Health route, static asset hosting, and OpenAPI contract

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-api/charter.md
> **Spec:** .context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md
> **Review:** PASS (2026-09-06)
> **Platform:** FastAPI 0.141.1, Python 3.11, sqlite3 (stdlib, no ORM), pytest 9.1.1 + httpx 0.28.1

**Goal:** Add a DB-independent `GET /health` route, conditional static asset hosting for `crm-ui`'s
build output at `GET /` (200 when present, clean 404 when absent), and confirm `GET /openapi.json`
already reflects every mounted route.

**Architecture:** Extends the existing single-file-per-concern FastAPI layout
(`accounts.py`/`contacts.py`/`opportunities.py` each an `APIRouter`, wired in `app.py`). Health
gets its own small router module for consistency. Static hosting is implemented as an explicit
catch-all route (not a `StaticFiles` mount) registered last in `app.py`, because the existing
codebase pattern reads env-driven configuration (`DB_PATH`) fresh on every call rather than baking
it in at import time — `mock_salesforce.app` is a module-level singleton re-imported once per test
session, so a static mount fixed at import/startup time would leak stale state across tests that
vary `STATIC_ASSETS_PATH`. A per-request catch-all avoids that entirely and matches the project's
existing "read the env var when you need it" idiom (see `db.py:get_db_path()`). `GET /openapi.json`
requires no code change — FastAPI auto-generates it from mounted routes; this plan only adds a
verification test.

---

## File Structure

**Create:**
- `src/mock_salesforce/health.py` — `APIRouter` with `GET /health`, no DB dependency
- `tests/test_health.py` — BEH-1 coverage
- `tests/test_static_hosting.py` — BEH-2 (present) and BEH-3 (absent) coverage
- `tests/test_openapi.py` — BEH-4 verification (no source change expected)

**Modify:**
- `src/mock_salesforce/app.py` — include the health router; add the catch-all static-serving route,
  registered after all API routers so it never shadows `/accounts`, `/contacts`, `/opportunities`,
  `/health`, `/openapi.json`, `/docs`, `/redoc` (the latter three are registered by FastAPI's own
  `__init__` before any user route, so ordering only matters relative to the routers this repo adds)

**Reference (read, do not modify):**
- `src/mock_salesforce/db.py:5-6` — `get_db_path()` pattern: env var read fresh via
  `os.environ.get(...)`, never cached at import time. Follow this same idiom for the static
  assets path (`STATIC_ASSETS_PATH`).
- `src/mock_salesforce/errors.py` — `error_body(code, message)` helper; reuse it for the
  `STATIC_ASSET_NOT_FOUND` error body rather than hand-rolling a dict.
- `src/mock_salesforce/accounts.py` — router/module shape to mirror for `health.py`.
- `tests/conftest.py` — `client` fixture: monkeypatches env vars *before* importing
  `mock_salesforce.app`, then uses `with TestClient(app) as c:` so the `startup` event re-runs
  per test. Any new env var this plan introduces must be set via `monkeypatch.setenv(...)`
  before that import, in the same pattern as `DB_PATH`.

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md` (BEH-1)
- Charter: `.context-index/specs/features/crm-api/charter.md` (capability: Health route and static
  asset hosting)
- Source files: `src/mock_salesforce/accounts.py` (router module shape, full read), `src/mock_salesforce/app.py` (current router wiring, full read)
- Test fixture: `tests/conftest.py` (the `client` fixture — reuse as-is, no changes needed)

### Task 2 Context
- Spec: `.context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md`
  (BEH-2, BEH-3, Error Cases table row for `STATIC_ASSET_NOT_FOUND`)
- Charter: `.context-index/specs/features/crm-api/charter.md` (capability: Health route and static
  asset hosting — "Listen port is read from an environment variable rather than hardcoded" /
  "the file path is read from an environment variable" establishes the env-var-for-config
  precedent this task follows for `STATIC_ASSETS_PATH`)
- Source files: `src/mock_salesforce/db.py:5-6` (`get_db_path()` — env-var-read-per-call pattern
  to mirror), `src/mock_salesforce/errors.py` (`error_body()` helper, full read)
- Cross-cutting: `.context-index/specs/cross-cutting/docker-packaging.spec.md` (confirms
  `crm-ui`'s build output is bundled into the image at build time via a fixed path — this task's
  `STATIC_ASSETS_PATH` env var, defaulting to a `static` directory that does not exist by
  default, is compatible with that packaging step supplying the real path at deploy time)
- Depends on: Task 1 (shared file `app.py`)

### Task 3 Context
- Spec: `.context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md` (BEH-4,
  Postconditions: "`GET /openapi.json` always reflects the currently mounted routes... regenerated
  per request, never cached stale")
- Charter: `.context-index/specs/features/crm-api/charter.md` (capability: OpenAPI contract)
- Source files: `src/mock_salesforce/app.py` (final route wiring, full read, no modification
  expected)
- Depends on: Task 1, Task 2 (asserts the full mounted route set, including `/health`)

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3

All three tasks touch or depend on the final state of `app.py`; there is no independent group for
a plan this small.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | GET /health route | small | unit | — | 2 create, 1 modify |
| 2 | Conditional static asset hosting | small | unit | Task 1 | 1 create, 1 modify |
| 3 | Confirm OpenAPI reflects all mounted routes | small | unit | Task 1, Task 2 | 1 create, 0 modify |

---

## Task Structure

### Task 1: GET /health route [specialist: none]

**Charter capability:** Health route and static asset hosting
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `src/mock_salesforce/health.py`
- Modify: `src/mock_salesforce/app.py:1-25` (import and `include_router` the health router)
- Test: `tests/test_health.py`

**Tests:** `tests/test_health.py` — new suite (source: fallback/first task on BEH-1); create it.

**Context to load:**
- `src/mock_salesforce/accounts.py` (router module shape — `APIRouter()`, `@router.get(...)`)
- `src/mock_salesforce/app.py` (current `include_router` calls, `on_startup` handler)

- [ ] **Write failing test**

```python
def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_health.py`
Expected: FAIL — 404 (no route registered for `/health`)

- [ ] **Implement**

```python
# src/mock_salesforce/health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

```python
# src/mock_salesforce/app.py — add alongside the other router imports/includes
from mock_salesforce.health import router as health_router
...
app.include_router(health_router)
```

Note: this route must not open a DB connection — no `get_connection()` call, matching BEH-1's
"no database round trip is required for this route to succeed."

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_health.py`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/crm-api/health-static-hosting-openapi`

```bash
git add src/mock_salesforce/health.py src/mock_salesforce/app.py tests/test_health.py
git commit -m "feat(crm-api): add GET /health with no DB dependency"
```

---

### Task 2: Conditional static asset hosting [specialist: none]

**Depends on:** Task 1
**Charter capability:** Health route and static asset hosting
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `src/mock_salesforce/app.py` (add the catch-all static-serving route, registered last)
- Test: `tests/test_static_hosting.py`

**Tests:** `tests/test_static_hosting.py` — new suite (source: fallback/first task touching
BEH-2 and BEH-3); create it. Both behaviors are the same code path branching on directory
existence, so one task and one suite cover both — write both test functions before implementing.

**Context to load:**
- `src/mock_salesforce/db.py:5-6` (`get_db_path()` env-var-per-call pattern — mirror this, do not
  bake `STATIC_ASSETS_PATH` into a module-level constant)
- `src/mock_salesforce/errors.py` (`error_body()` helper)
- `.context-index/specs/cross-cutting/docker-packaging.spec.md` (BEH-1: crm-ui's build output is
  bundled at image build time via a fixed path, not passed per-request — confirms an env-var
  default that resolves to "nothing present" in local dev is the right default)

- [ ] **Write failing test**

```python
# tests/test_static_hosting.py
def test_serves_index_html_when_build_present(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    (static_dir / "app.js").write_text("console.log('hi');")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "crm-ui" in root.text

        asset = client.get("/app.js")
        assert asset.status_code == 200
        assert "javascript" in asset.headers["content-type"]


def test_returns_404_when_build_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(tmp_path / "does-not-exist"))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 404
        assert response.json()["error"] == "STATIC_ASSET_NOT_FOUND"


def test_returns_404_for_path_traversal_attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html><body>crm-ui</body></html>")
    secret = tmp_path / "secret.txt"
    secret.write_text("outside the static root")
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(static_dir))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # A literal "/../secret.txt" gets dot-segment-normalized away by the HTTP client
        # itself (httpx resolves it to "/secret.txt" before the request is even sent — verified
        # empirically, not assumed), so it would never reach the traversal guard. Percent-encoding
        # the slash (`%2F`) prevents that client-side normalization, so the literal string
        # "../secret.txt" arrives as the `full_path` path-parameter value, which is what actually
        # exercises the `static_root not in target.parents` guard in `serve_static`.
        response = client.get("/..%2Fsecret.txt")
        assert response.status_code == 404
        assert response.json()["error"] == "STATIC_ASSET_NOT_FOUND"
```

Note: this test file imports `app`/`TestClient` directly in each test function rather than using
the shared `client` fixture, because `STATIC_ASSETS_PATH` must vary per test case (present in one,
absent in another, present-but-escaped in the third). This works precisely because
`get_static_dir()` reads the env var fresh on every request rather than caching it at import
time (see the architecture note above) — module caching of `mock_salesforce.app` is harmless
here since none of these tests depend on when the module was first imported, only on what
`STATIC_ASSETS_PATH` is set to at request time. `monkeypatch.setenv` before each request is
sufficient; no `importlib.reload` is needed.

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_static_hosting.py`
Expected: FAIL — `test_serves_index_html_when_build_present` gets 404 (no catch-all route yet);
`test_returns_404_when_build_absent` and `test_returns_404_for_path_traversal_attempt` may already
incidentally pass with the wrong error body (generic `HTTP_ERROR`, not `STATIC_ASSET_NOT_FOUND`)
or fail depending on interaction with Task 1's routes — confirm the failure reason for all three
matches "no static route registered yet," not a false pass on the wrong error code.

- [ ] **Implement**

```python
# src/mock_salesforce/app.py — add after all app.include_router(...) calls
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from mock_salesforce.errors import error_body

...

def get_static_dir() -> Path:
    return Path(os.environ.get("STATIC_ASSETS_PATH", "static"))


@app.get("/{full_path:path}", include_in_schema=False)
def serve_static(full_path: str):
    static_dir = get_static_dir()
    if not static_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=error_body("STATIC_ASSET_NOT_FOUND", "No static assets are present"),
        )

    requested = full_path or "index.html"
    target = (static_dir / requested).resolve()
    static_root = static_dir.resolve()
    if static_root != target and static_root not in target.parents:
        raise HTTPException(
            status_code=404,
            detail=error_body("STATIC_ASSET_NOT_FOUND", f"No static asset at {requested}"),
        )
    if not target.is_file():
        raise HTTPException(
            status_code=404,
            detail=error_body("STATIC_ASSET_NOT_FOUND", f"No static asset at {requested}"),
        )
    return FileResponse(target)
```

This route MUST be the last one added in `app.py` — it is a path-parameter catch-all
(`/{full_path:path}`) and would otherwise shadow `/accounts`, `/contacts`, `/opportunities`, and
`/health` if registered before them. `include_in_schema=False` keeps the wildcard fallback out of
the OpenAPI document (Task 3 verifies the *real* API routes are listed; this route is
infrastructure, not part of the documented contract). `FileResponse` derives `content-type` from
the file suffix via the stdlib `mimetypes` module, satisfying "served with its correct content
type" without hand-mapping extensions.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_static_hosting.py`
Expected: PASS

Also re-run the full suite to confirm the catch-all doesn't shadow existing routes:
Run: `python3 -m pytest -q`
Expected: PASS (all existing account/contact/opportunity/seed tests still pass)

- [ ] **Commit**

```bash
git add src/mock_salesforce/app.py tests/test_static_hosting.py
git commit -m "feat(crm-api): serve crm-ui static build output at / when present, 404 when absent"
```

---

### Task 3: Confirm OpenAPI reflects all mounted routes [specialist: none]

**Depends on:** Task 1, Task 2
**Charter capability:** OpenAPI contract
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/test_openapi.py` (create)
- No source files expected to change — FastAPI auto-generates `/openapi.json` from mounted
  routes with no manual authoring required. If this task's failing test somehow does NOT pass
  after Task 1 and Task 2 land, that signals a routing-registration bug in `app.py` to fix as
  part of this task, not a new hand-written OpenAPI document.

**Tests:** `tests/test_openapi.py` — new suite (source: fallback/first task on BEH-4); create it.

**Context to load:**
- `src/mock_salesforce/app.py` (final route wiring after Tasks 1-2, full read, no modification
  expected)

- [ ] **Write failing test**

```python
def test_openapi_lists_all_mounted_routes(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    doc = response.json()
    paths = doc["paths"]

    assert "/health" in paths
    assert "get" in paths["/health"]

    for path in ("/accounts", "/contacts", "/opportunities"):
        assert path in paths
        assert "get" in paths[path]
        assert "post" in paths[path]

    for path in ("/accounts/{account_id}", "/contacts/{contact_id}", "/opportunities/{opportunity_id}"):
        assert path in paths

    # the static-serving catch-all is infrastructure, not a documented API route
    assert "/{full_path}" not in paths
```

Adjust the exact `{..._id}` path-parameter names above to match whatever `accounts.py` /
`contacts.py` / `opportunities.py` actually use if they differ (verify against source before
finalizing the test — do not guess if grep shows different parameter names than `account_id`,
`contact_id`, `opportunity_id`).

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_openapi.py`
Expected: FAIL only if Tasks 1-2 are not yet complete (missing `/health`) — since this task
depends on both, run it only after Tasks 1 and 2 are committed; at that point this test should
already pass on first write, which is an acceptable outcome for a pure-verification task
(the "RED" phase here is expected to be brief/immediate since no implementation is pending).

- [ ] **Implement**

No implementation step — this task is verification-only per the spec's Actionable Task Map
("Confirm OpenAPI wiring... no manual OpenAPI authoring"). If the test fails for a reason other
than Tasks 1-2 being incomplete (e.g., a router missing a `response_model`, or a path genuinely
not mounted), fix the specific registration gap in `app.py` and note it as a deviation in the
commit message.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_openapi.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests/test_openapi.py
git commit -m "test(crm-api): confirm GET /openapi.json reflects all mounted routes"
```

---

## Quality Gates

Per `.context-index/governance/gates.yaml`:

- Tests pass: `python3 -m pytest -q`
- Lint passes: `ruff check .`
- `integration-test` gate is unwired (`command: ""`) in this repo — skipped, not applicable.
- All acceptance criteria from the spec satisfied:
  - [ ] `GET /health` returns 200 with no DB dependency (BEH-1)
  - [ ] `GET /` serves crm-ui's `index.html` and static assets when the build output is present (BEH-2)
  - [ ] `GET /` returns 404 (not a server error) when the build output is absent (BEH-3)
  - [ ] `GET /openapi.json` returns a valid OpenAPI document listing every mounted route (BEH-4)
  - [ ] No constitutional violations introduced

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.
