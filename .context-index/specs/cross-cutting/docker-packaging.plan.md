<!-- partial_schema: plan@1 -->

# Implementation Plan: Docker packaging and run instructions

> **Methodology:** adev
> **Charter:** .context-index/specs/cross-cutting/deployment/charter.md
> **Spec:** .context-index/specs/cross-cutting/docker-packaging.spec.md
> **Review:** PASS (2026-09-05) — review skipped per risk policy (`risk_level: low`), no findings.
> **Platform:** FastAPI 0.141.1 + uvicorn (crm-api), FastMCP/`mcp` 1.29.1 (mcp-server), Python 3.11+ (dev venv observed at 3.12), SQLite, no ORM, no deployment target beyond local Docker.

**Goal:** Package `crm-api` (bundling `crm-ui`'s static assets) and `mcp-server` into two Docker images wired by a single `docker-compose.yml`, with a named volume for the SQLite file, environment-variable driven port remapping, and written run instructions — so `docker compose up` from a clean checkout brings up the whole stack with one command.

**Architecture:** Two single-stage `python:3.12-slim` Dockerfiles under `docker/<service>/Dockerfile` (build context is the repo root so each can `COPY` its own source tree plus, for crm-api, `static/`). `crm-ui` has no Dockerfile of its own — its plain static files are copied into crm-api's image at build time, satisfying BEH-1's "bundled at build time, not runtime" requirement without any actual JS build tooling (there is none — `static/` is already built output). `docker-compose.yml` wires both services with `depends_on: condition: service_healthy` so `mcp-server` waits for `crm-api`'s `GET /health`, a named volume (`mock_salesforce_db`) mounted at `/data` for the SQLite file, and `${PORT:-8000}` / `${MCP_PORT:-8001}` host-port overrides bound to `127.0.0.1` only. Two small gaps in the already-implemented modules block full spec compliance and are closed as Tasks 1-2 before packaging: `mcp-server` has no `GET /health` route yet (BEH-6), and `crm-api` has no explicit, named error when its SQLite volume mount isn't writable (the spec's `DEPLOY_VOLUME_NOT_WRITABLE` error case). The repo's `governance/gates.yaml` already scaffolds an unwired `integration-test` tier gate with the comment "seed once one exists" — Task 3 wires it to the new Docker-dependent test suite and excludes that suite from the default fast `pytest -q` gate, so the two tiers stay separated as the scaffolding intended.

## Plan Notes — Deviations From Spec Prose (documented, not silent)

1. **Env var name: `DB_PATH`, not `DATABASE_PATH`.** The spec's Error Cases table and the parent charter's Interface Contracts both use the name `DATABASE_PATH` as the packaging convention for crm-api's SQLite path. The already-implemented, already-tested `src/mock_salesforce/db.py` reads `DB_PATH` (default `"mock_salesforce.db"`), and 11 test files (30 call sites across `fixture-seeding`, `health-static-hosting-and-openapi`, `account-and-contact-management` specs) already depend on that exact name. Renaming it now would touch every one of those already-validated suites for a purely cosmetic gain (no HTTP-contract change either way — this is an internal env var, principle 4 doesn't apply). This plan wires Docker/compose to the **actual** variable, `DB_PATH`, and treats `DATABASE_PATH` in the spec/charter prose as the generic convention name for "wherever crm-api's SQLite path env var points," not a literal string to match. `DEPLOY_VOLUME_NOT_WRITABLE`'s error message names the real `DB_PATH` value so the code and the run instructions never disagree.
2. **Base image: `python:3.12-slim`, not `3.11-slim`.** The constitution requires "Python 3.11+"; the actual dev `.venv` is 3.12, and the sibling `mock-jira` repo (referenced for conventions) already uses `python:3.12-slim`. Using 3.12 satisfies the "3.11+" floor and keeps parity with the one other repo in this workspace that already made this call.
3. **No literal multi-stage `FROM ... AS build`.** BEH-1 requires crm-ui's assets to be "bundled ... during the build step, not at runtime" — satisfied by a single-stage Dockerfile's `COPY static/ ./static/`, since `crm-ui` is plain static files with no build tool to run in a separate stage. An actual two-`FROM` multi-stage Dockerfile would add ceremony with no artifact to build in the first stage.
4. **`mcp-server` gets a new `HOST` env var (default `127.0.0.1`, image sets it to `0.0.0.0`).** `FastMCP(...)` defaults to binding `127.0.0.1`, which Docker cannot forward a published port to (the docker-proxy connects to the container's external interface, not its loopback). This is additive and non-breaking: the default preserves today's local-dev behavior (and FastMCP's auto DNS-rebinding protection, which only auto-enables for loopback hosts) for anyone running `mcp_server.app` directly outside Docker; only the Docker image's `ENV HOST=0.0.0.0` changes the bind.
5. **`DEPLOY_UPSTREAM_UNREACHABLE` is already satisfied by existing code.** `mcp_server/client.py`'s `CrmApiClient.request()` already raises `McpUpstreamUnreachableError` naming the unreachable `base_url` on any `httpx.HTTPError`, tested in `tests/mcp_server/test_connection_handling.py`. `mcp-server` never proactively pings `crm-api` at process startup (tools are invoked lazily), so there is no crash-loop risk to begin with. Task 5's container-level test adds one more confirmation (container stays up with a deliberately-bad `API_BASE_URL`) rather than a new implementation task.

---

## File Structure

**Create:**
- `docker/crm-api/Dockerfile` — crm-api image (bundles `static/` at build time)
- `docker/mcp-server/Dockerfile` — mcp-server image
- `docker-compose.yml` — wires both services, named volume, healthchecks, `depends_on`
- `.dockerignore` — keeps `.venv/`, `__pycache__/`, `.git/`, `tests/`, `.context-index/`, `*.db` out of build contexts
- `tests/test_db_path_not_writable.py` — DEPLOY_VOLUME_NOT_WRITABLE
- `tests/mcp_server/test_health_route.py` — BEH-6 + HOST env
- `tests/docker/test_gate_wiring.py` — proves the fast/integration pytest split works
- `tests/docker/test_crm_api_image.py` — standalone crm-api image build/run (BEH-1 partial)
- `tests/docker/test_mcp_server_image.py` — standalone mcp-server image build/run (BEH-1 partial, BEH-6 in-container, upstream-unreachable non-crash-loop)
- `tests/docker/test_compose_build_and_startup.py` — BEH-1 (exactly two images via compose), BEH-2 (startup order)
- `tests/docker/test_volume_persistence.py` — BEH-3
- `tests/docker/test_port_override.py` — BEH-4
- `tests/docker/test_combined_logs.py` — BEH-5
- `tests/test_readme_docker_instructions.py` — run-instructions content check
- `tests/docker/test_clean_checkout_smoke.py` — Postconditions (single-command bring-up, localhost-only ports)

**Modify:**
- `src/mock_salesforce/db.py` — writable-directory check before `sqlite3.connect`
- `mcp_server/app.py` — `HOST` env var on `FastMCP(...)`, new `GET /health` custom route
- `pyproject.toml` — exclude `tests/docker/` from the default `pytest -q` collection
- `.context-index/governance/gates.yaml` — wire the scaffolded `integration-test` gate's `command`
- `README.md` — "Running with Docker" section

**Reference (read, do not modify):**
- `../mock-jira/docker-compose.yml`, `../mock-jira/docker/*/Dockerfile` — sibling conventions (adapted, not copied verbatim: different module layout, `DB_PATH` vs `DATABASE_PATH`, single healthcheck definition instead of duplicating it in both the Dockerfile and compose)
- `src/mock_salesforce/static.py` — existing `STATIC_ASSETS_PATH` convention
- `mcp_server/client.py`, `mcp_server/errors.py` — existing `DEPLOY_UPSTREAM_UNREACHABLE`-equivalent behavior

---

## Context Packets

### Task 1 Context
- Spec: `docker-packaging.spec.md` (Error Cases table, `DEPLOY_VOLUME_NOT_WRITABLE`)
- Charter: `deployment/charter.md` (capability: crm-api Dockerfile / env-var convention)
- Source: `src/mock_salesforce/db.py` (full), `src/mock_salesforce/app.py:24-29` (`on_startup`), `src/mock_salesforce/errors.py` (`error_body` pattern for the message shape)
- Existing tests using `DB_PATH` (do not break): `tests/conftest.py`, `tests/test_db_schema.py`

### Task 2 Context
- Spec: `docker-packaging.spec.md` (BEH-6)
- Charter: `deployment/charter.md` (mcp-server row: "own GET /health route")
- Source: `mcp_server/app.py` (full — module-level tool registration pattern), FastMCP `custom_route` API at `.venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py:709-753` (docstring example is literally `/health`)
- Existing tests: `tests/mcp_server/test_connection_handling.py` (style reference — imports `mcp_server.app as app_module`)

### Task 3 Context
- Charter: `deployment/charter.md` (Quality Attributes: Observability)
- Source: `.context-index/governance/gates.yaml` (the pre-scaffolded, unwired `integration-test` gate), `pyproject.toml` (current `[tool.pytest.ini_options]`)

### Task 4 Context
- Spec: `docker-packaging.spec.md` (BEH-1, Module Impact Map crm-api row)
- Source: `src/mock_salesforce/` (full tree — what gets copied), `requirements.txt`, `pyproject.toml`
- Sibling reference: `../mock-jira/docker/issue-tracker-api/Dockerfile`

### Task 5 Context
- Spec: `docker-packaging.spec.md` (BEH-1, BEH-6, Error Cases `DEPLOY_UPSTREAM_UNREACHABLE`)
- Source: `mcp_server/` (full tree), `mcp_server/requirements.txt`
- Sibling reference: `../mock-jira/docker/mcp-server/Dockerfile`
- Depends on Task 2 (health route must exist) and Task 4 (established `docker/` layout)

### Task 6 Context
- Spec: `docker-packaging.spec.md` (BEH-1, BEH-2), charter Interface Contracts + Consumed APIs tables
- Sibling reference: `../mock-jira/docker-compose.yml` (adapted: single healthcheck source of truth, `DB_PATH` not `DATABASE_PATH`, module-specific volume/network names)
- Depends on Task 4, Task 5

### Task 7 Context
- Spec: `docker-packaging.spec.md` (BEH-3)
- Depends on Task 6 (named volume must exist)

### Task 8 Context
- Spec: `docker-packaging.spec.md` (BEH-4)
- Depends on Task 6 (`${PORT}`/`${MCP_PORT}` interpolation must exist)

### Task 9 Context
- Spec: `docker-packaging.spec.md` (BEH-5)
- Depends on Task 6

### Task 10 Context
- Charter: `deployment/charter.md` (Scope: "Written run instructions ... in this repo's README/CLAUDE.md")
- Source: current `README.md` (stub), `../mock-jira/README.md` ("Running with Docker" section — style reference only)
- Depends on Task 6

### Task 11 Context
- Spec: `docker-packaging.spec.md` (Postconditions section in full)
- Depends on all of Tasks 1-10

---

## Parallelization

- Group A (independent): Task 1
- Group B (independent): Task 2
- Group C (independent): Task 3
- Group D (independent): Task 7
- Group E (independent): Task 8
- Group F (independent): Task 9
- Group G (independent): Task 10

"Independent" above means independent **of the other groups in this list** — it does not mean dependency-free in absolute terms. Tasks 4, 5, 6, and 11 are deliberately excluded from these group lines because each is a join (it depends on more than one predecessor and would misrepresent a fan-in as a linear chain if forced into the `Task <n> → Task <n>` grammar): Task 4 depends on Task 1 and Task 3; Task 5 depends on Task 2 and Task 3; Task 6 depends on Task 4 and Task 5; Task 11 depends on Tasks 1 through 10. Groups D, E, F, and G (Tasks 7, 8, 9, 10) are each individually gated on Task 6 completing — that gating lives on each task's own `Depends on:` line and in the Task Summary table, not in this group label — but once Task 6 lands, Tasks 7, 8, 9, and 10 have no file overlap with one another and can run concurrently. Task 11 runs last, after every other task, gated on the full set.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | crm-api: fail fast on unwritable DB_PATH directory | small | unit | — | 1 create, 1 modify |
| 2 | mcp-server: HOST env + GET /health route | small | unit | — | 1 create, 1 modify |
| 3 | Wire the integration-test gate for Docker suites | small | unit | — | 1 create, 2 modify |
| 4 | crm-api Dockerfile + .dockerignore | medium | unit | Task 1, Task 3 | 3 create, 0 modify |
| 5 | mcp-server Dockerfile | small | unit | Task 2, Task 3 | 2 create, 0 modify |
| 6 | docker-compose.yml | medium | unit | Task 4, Task 5 | 2 create, 0 modify |
| 7 | SQLite persistence across down/up | small | unit | Task 6 | 1 create, 0 modify |
| 8 | PORT/MCP_PORT override remaps host ports | small | unit | Task 6 | 1 create, 0 modify |
| 9 | docker compose logs combined output | small | unit | Task 6 | 1 create, 0 modify |
| 10 | Written run instructions (README.md) | small | unit | Task 6 | 1 create, 1 modify |
| 11 | Clean-checkout acceptance sweep | medium | unit | Tasks 1-10 | 1 create, 0 modify |

All tasks resolve to strategy `unit` (source: fallback — the spec declares no `test_strategy` in frontmatter, `manifest.yaml` has no `test_strategies` globs, and the per-task path detector in `lib/test-strategies/detection.mjs` has no rule matching `Dockerfile`/`docker-compose.yml` paths). Tasks 4-11's "unit" tests are pytest tests that shell out to the real `docker`/`docker compose` CLI (available and running in this environment) rather than mocks — genuinely exercising the behavior, just collected under the `unit` strategy label per the documented resolution chain. Task 3 routes these into `governance/gates.yaml`'s pre-existing `integration-test` tier so the default fast gate (`pytest -q`) stays fast.

---

## Task Structure

### Task 1: crm-api: fail fast on unwritable DB_PATH directory [specialist: none]

**Charter capability:** crm-api Dockerfile / env-var convention (Error Cases: `DEPLOY_VOLUME_NOT_WRITABLE`)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `src/mock_salesforce/db.py`
- Test: `tests/test_db_path_not_writable.py`

**Tests:** `tests/test_db_path_not_writable.py` (create)

**Context to load:**
- `src/mock_salesforce/errors.py` (existing `error_body(code, message)` shape)
- `src/mock_salesforce/app.py:24-29` (`on_startup` calls `get_connection()` then `init_db()`)

- [ ] **Write failing test**

```python
import os
import stat

import pytest


def test_startup_raises_clear_error_when_db_dir_not_writable(tmp_path, monkeypatch):
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(stat.S_IREAD | stat.S_IEXEC)  # r-x, no write
    monkeypatch.setenv("DB_PATH", str(readonly_dir / "mock_salesforce.db"))

    from mock_salesforce.db import get_connection

    with pytest.raises(RuntimeError) as exc_info:
        get_connection()
    assert "DEPLOY_VOLUME_NOT_WRITABLE" in str(exc_info.value)
    assert str(readonly_dir) in str(exc_info.value)

    readonly_dir.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)  # restore for cleanup
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_db_path_not_writable.py`
Expected: FAIL — `sqlite3.OperationalError: unable to open database file` (raw, uncoded) instead of the expected `RuntimeError` naming `DEPLOY_VOLUME_NOT_WRITABLE`.

- [ ] **Implement**

```python
# src/mock_salesforce/db.py
import os
import sqlite3
from pathlib import Path


def get_db_path() -> str:
    return os.environ.get("DB_PATH", "mock_salesforce.db")


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    parent = Path(db_path).parent
    if parent != Path("") and parent.exists() and not os.access(parent, os.W_OK):
        raise RuntimeError(
            f"[DEPLOY_VOLUME_NOT_WRITABLE] Cannot write to directory '{parent}' for "
            f"DB_PATH='{db_path}'. Check the volume mount is writable."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_db_path_not_writable.py`
Expected: PASS. Then run the full fast gate to confirm no regression: `python3 -m pytest -q`.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add src/mock_salesforce/db.py tests/test_db_path_not_writable.py
git commit -m "feat(deployment): fail fast with DEPLOY_VOLUME_NOT_WRITABLE on unwritable DB_PATH"
```

---

### Task 2: mcp-server: HOST env var + GET /health route [specialist: none]

**Charter capability:** mcp-server Dockerfile ("own GET /health route", BEH-6)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/app.py`
- Test: `tests/mcp_server/test_health_route.py`

**Tests:** `tests/mcp_server/test_health_route.py` (create)

**Context to load:**
- `mcp_server/app.py` (full — module-level registration pattern)
- FastMCP `custom_route` decorator, `.venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py:709-753`

- [ ] **Write failing test**

```python
import os

from starlette.testclient import TestClient

import mcp_server.app as app_module


def test_default_host_stays_loopback():
    assert app_module.mcp.settings.host == "127.0.0.1"


def test_host_env_var_override(monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    import importlib

    importlib.reload(app_module)
    assert app_module.mcp.settings.host == "0.0.0.0"
    monkeypatch.delenv("HOST", raising=False)
    importlib.reload(app_module)  # restore module state for later tests


def test_health_route_returns_ok():
    client = TestClient(app_module.mcp.streamable_http_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/mcp_server/test_health_route.py`
Expected: FAIL — `app_module.mcp.settings.host` is `"127.0.0.1"` already (that assertion passes by luck), but `GET /health` returns 404 (no such route registered yet).

- [ ] **Implement**

```python
# mcp_server/app.py — near the top, alongside the `mcp = FastMCP(...)` line
import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.client import CrmApiClient
from mcp_server.tools import accounts, contacts, opportunities

mcp = FastMCP(
    "mock-salesforce-crm",
    host=os.environ.get("HOST", "127.0.0.1"),
    port=int(os.environ.get("PORT", "8000")),
)
client = CrmApiClient()


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/mcp_server/test_health_route.py`
Expected: PASS. Then: `python3 -m pytest -q` (full fast gate, no regression in the other 14 mcp_server tests).

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add mcp_server/app.py tests/mcp_server/test_health_route.py
git commit -m "feat(deployment): add mcp-server GET /health route and HOST env var"
```

---

### Task 3: Wire the integration-test gate for Docker suites [specialist: none]

**Charter capability:** deployment (Observability — separating fast unit gate from slow Docker-dependent checks)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `pyproject.toml`
- Modify: `.context-index/governance/gates.yaml`
- Test: `tests/docker/test_gate_wiring.py`

**Tests:** `tests/docker/test_gate_wiring.py` (create)

**Context to load:**
- `.context-index/governance/gates.yaml` (the pre-scaffolded `integration-test` gate, currently `command: ""`)
- `pyproject.toml` (current `[tool.pytest.ini_options]`)

- [ ] **Write failing test**

```python
import shutil

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")
def test_docker_cli_is_available():
    assert shutil.which("docker") is not None
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q` (default, repo-root scope)
Expected: this new file is collected and run today (no exclusion configured yet) — confirms the "before" state that Task 3 must change.

- [ ] **Implement**

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]
addopts = "--ignore=tests/docker"
```

```yaml
# .context-index/governance/gates.yaml — replace the integration-test gate's command
  - id: integration-test
    name: Integration Tests
    kind: deterministic
    tier: integration
    command: [python3, -m, pytest, -q, tests/docker]
    scope: project
    required: true
    severity: error
    triggers:
      - post-implement
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q` — Expected: `tests/docker/` is NOT collected (ignored), so this file's test does not run under the fast gate.
Run: `python3 -m pytest -q tests/docker/` — Expected: PASS (the file IS collected and passes when invoked directly, matching the new `integration-test` gate command).

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add pyproject.toml .context-index/governance/gates.yaml tests/docker/test_gate_wiring.py
git commit -m "feat(deployment): wire the integration-test gate to tests/docker and exclude it from the fast gate"
```

---

### Task 4: crm-api Dockerfile + .dockerignore [specialist: none]

**Charter capability:** crm-api Dockerfile (BEH-1)
**Depends on:** Task 1, Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `docker/crm-api/Dockerfile`
- Create: `.dockerignore`
- Test: `tests/docker/test_crm_api_image.py`

**Tests:** `tests/docker/test_crm_api_image.py` (create)

**Context to load:**
- `src/mock_salesforce/` (full tree), `requirements.txt`, `static/`
- `../mock-jira/docker/issue-tracker-api/Dockerfile` (sibling convention, adapted)

- [ ] **Write failing test**

```python
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

IMAGE = "mock-salesforce-crm-api-test"
CONTAINER = "mock-salesforce-crm-api-test-run"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)


def test_crm_api_image_builds_and_serves_health_and_static():
    subprocess.run(
        ["docker", "build", "-f", "docker/crm-api/Dockerfile", "-t", IMAGE, "."],
        check=True,
    )
    subprocess.run(
        ["docker", "run", "-d", "--name", CONTAINER, "-p", "18000:8000", IMAGE],
        check=True,
    )
    _wait_for_http("http://localhost:18000/health", expect_status=200)
    with urllib.request.urlopen("http://localhost:18000/") as resp:
        assert resp.status == 200


def _wait_for_http(url, expect_status, timeout=20):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == expect_status:
                    return
        except Exception as exc:  # noqa: BLE001 - polling until the container is ready
            last_exc = exc
        time.sleep(1)
    raise AssertionError(f"{url} never returned {expect_status}: {last_exc}")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_crm_api_image.py`
Expected: FAIL — `docker build` errors, `docker/crm-api/Dockerfile: no such file or directory`.

- [ ] **Implement**

```dockerfile
# docker/crm-api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/

ENV PYTHONPATH=/app/src
ENV PORT=8000
ENV DB_PATH=/data/mock_salesforce.db
ENV STATIC_ASSETS_PATH=/app/static

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/health', timeout=2)"

CMD ["sh", "-c", "uvicorn mock_salesforce.app:app --host 0.0.0.0 --port ${PORT}"]
```

```gitignore
# .dockerignore
.git/
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.context-index/
tests/
tests_e2e/
*.db
docker/
docker-compose.yml
README.md
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_crm_api_image.py`
Expected: PASS. `docker image rm mock-salesforce-crm-api-test` after to clean up local disk.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add docker/crm-api/Dockerfile .dockerignore tests/docker/test_crm_api_image.py
git commit -m "feat(deployment): add crm-api Dockerfile bundling crm-ui's static assets"
```

---

### Task 5: mcp-server Dockerfile [specialist: none]

**Charter capability:** mcp-server Dockerfile (BEH-1, BEH-6 in-container, `DEPLOY_UPSTREAM_UNREACHABLE` non-crash-loop)
**Depends on:** Task 2, Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `docker/mcp-server/Dockerfile`
- Test: `tests/docker/test_mcp_server_image.py`

**Tests:** `tests/docker/test_mcp_server_image.py` (create)

**Context to load:**
- `mcp_server/` (full tree), `mcp_server/requirements.txt`
- `../mock-jira/docker/mcp-server/Dockerfile` (sibling convention, adapted)

- [ ] **Write failing test**

```python
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")

IMAGE = "mock-salesforce-mcp-server-test"
CONTAINER = "mock-salesforce-mcp-server-test-run"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)


def test_mcp_server_image_builds_and_serves_health():
    subprocess.run(
        ["docker", "build", "-f", "docker/mcp-server/Dockerfile", "-t", IMAGE, "."],
        check=True,
    )
    subprocess.run(
        [
            "docker", "run", "-d", "--name", CONTAINER, "-p", "18001:8001",
            "-e", "API_BASE_URL=http://does-not-exist.invalid:9999",
            IMAGE,
        ],
        check=True,
    )
    _wait_for_http("http://localhost:18001/health", timeout=20)
    # container must still be running (no crash-loop) despite the bad API_BASE_URL
    status = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert status == "true"


def _wait_for_http(url, timeout):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - polling until the container is ready
            last_exc = exc
        time.sleep(1)
    raise AssertionError(f"{url} never returned 200: {last_exc}")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_mcp_server_image.py`
Expected: FAIL — `docker/mcp-server/Dockerfile: no such file or directory`.

- [ ] **Implement**

```dockerfile
# docker/mcp-server/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY mcp_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server/ ./mcp_server/

ENV HOST=0.0.0.0
ENV PORT=8001
ENV API_BASE_URL=http://crm-api:8000

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8001') + '/health', timeout=2)"

CMD ["python3", "-m", "mcp_server.app"]
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_mcp_server_image.py`
Expected: PASS. `docker image rm mock-salesforce-mcp-server-test` after to clean up local disk.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add docker/mcp-server/Dockerfile tests/docker/test_mcp_server_image.py
git commit -m "feat(deployment): add mcp-server Dockerfile"
```

---

### Task 6: docker-compose.yml [specialist: none]

**Charter capability:** deployment (BEH-1 full, BEH-2)
**Depends on:** Task 4, Task 5
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `docker-compose.yml`
- Test: `tests/docker/test_compose_build_and_startup.py`

**Tests:** `tests/docker/test_compose_build_and_startup.py` (create)

**Context to load:**
- `../mock-jira/docker-compose.yml` (sibling convention, adapted: single healthcheck source of truth in the Dockerfile, not duplicated in compose; `DB_PATH` not `DATABASE_PATH`; `mock_salesforce_db` volume name)

- [ ] **Write failing test**

```python
import json
import shutil
import subprocess
import time

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_compose_build_produces_exactly_two_images():
    subprocess.run(["docker", "compose", "build"], check=True)
    config = json.loads(
        subprocess.run(["docker", "compose", "config", "--format", "json"], check=True, capture_output=True, text=True).stdout
    )
    assert set(config["services"].keys()) == {"crm-api", "mcp-server"}


def test_crm_api_becomes_healthy_before_mcp_server_starts():
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    deadline = time.time() + 60
    crm_api_healthy_at = None
    mcp_server_running_at = None
    while time.time() < deadline and (crm_api_healthy_at is None or mcp_server_running_at is None):
        cid = subprocess.run(["docker", "compose", "ps", "-q", "crm-api"], capture_output=True, text=True).stdout.strip()
        if cid:
            state = json.loads(
                subprocess.run(["docker", "inspect", "-f", "{{json .State}}", cid], capture_output=True, text=True).stdout or "{}"
            )
            if crm_api_healthy_at is None and state.get("Health", {}).get("Status") == "healthy":
                crm_api_healthy_at = time.time()
        mcp_ps = subprocess.run(["docker", "compose", "ps", "--status", "running", "mcp-server"], capture_output=True, text=True).stdout
        if mcp_server_running_at is None and "mcp-server" in mcp_ps:
            mcp_server_running_at = time.time()
        time.sleep(1)
    assert crm_api_healthy_at is not None, "crm-api never reported healthy"
    assert mcp_server_running_at is not None, "mcp-server never started"
    assert crm_api_healthy_at <= mcp_server_running_at
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_compose_build_and_startup.py`
Expected: FAIL — `docker-compose.yml: no such file or directory` / `no configuration file provided`.

- [ ] **Implement**

```yaml
# docker-compose.yml
services:
  crm-api:
    build:
      context: .
      dockerfile: docker/crm-api/Dockerfile
    ports:
      - "127.0.0.1:${PORT:-8000}:${PORT:-8000}"
    environment:
      PORT: ${PORT:-8000}
      DB_PATH: /data/mock_salesforce.db
    volumes:
      - mock_salesforce_db:/data

  mcp-server:
    build:
      context: .
      dockerfile: docker/mcp-server/Dockerfile
    ports:
      - "127.0.0.1:${MCP_PORT:-8001}:${MCP_PORT:-8001}"
    environment:
      # Same PORT convention as crm-api, but a separate host-level override
      # variable (MCP_PORT) so remapping one service's published port never
      # collides with the other's.
      PORT: ${MCP_PORT:-8001}
      API_BASE_URL: http://crm-api:${PORT:-8000}
    depends_on:
      crm-api:
        condition: service_healthy

volumes:
  mock_salesforce_db:
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_compose_build_and_startup.py`
Expected: PASS. `docker compose down -v` after to clean up.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add docker-compose.yml tests/docker/test_compose_build_and_startup.py
git commit -m "feat(deployment): add docker-compose.yml wiring crm-api and mcp-server"
```

---

### Task 7: SQLite persistence across down/up [specialist: none]

**Charter capability:** deployment (BEH-3)
**Depends on:** Task 6
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/docker/test_volume_persistence.py`

**Tests:** `tests/docker/test_volume_persistence.py` (create)

**Context to load:**
- `docker-compose.yml` (named volume `mock_salesforce_db`)

- [ ] **Write failing test**

```python
import json
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_data_survives_down_and_up_without_dash_v():
    subprocess.run(["docker", "compose", "up", "-d", "crm-api"], check=True)
    _wait_healthy("crm-api", timeout=60)

    body = {"name": "Persistence Test Co"}
    req = urllib.request.Request(
        "http://localhost:8000/accounts",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        created = json.loads(resp.read())

    subprocess.run(["docker", "compose", "down"], check=True)  # no -v
    subprocess.run(["docker", "compose", "up", "-d", "crm-api"], check=True)
    _wait_healthy("crm-api", timeout=60)

    with urllib.request.urlopen(f"http://localhost:8000/accounts/{created['id']}") as resp:
        fetched = json.loads(resp.read())
    assert fetched["name"] == "Persistence Test Co"


def _wait_healthy(service, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        cid = subprocess.run(["docker", "compose", "ps", "-q", service], capture_output=True, text=True).stdout.strip()
        if cid:
            state = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid], capture_output=True, text=True).stdout.strip()
            if state == "healthy":
                return
        time.sleep(1)
    raise AssertionError(f"{service} never reported healthy")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_volume_persistence.py`
Expected: FAIL before Task 6 exists at all (no `docker-compose.yml`); once Task 6 is done, this is a genuinely new test proving persistence — run once to confirm the new file itself is exercised (it will already pass once the volume from Task 6 is in place, since persistence follows directly from a correctly-declared named volume; if it fails here, the volume mount or `DB_PATH` wiring in Task 6 is wrong).

- [ ] **Implement**

No production code change needed — Task 6's named volume already provides persistence. This task exists to prove it with a dedicated, traceable BEH-3 suite.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_volume_persistence.py`
Expected: PASS. `docker compose down -v` after to clean up.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add tests/docker/test_volume_persistence.py
git commit -m "test(deployment): verify SQLite persistence across docker compose down/up"
```

---

### Task 8: PORT/MCP_PORT override remaps host ports [specialist: none]

**Charter capability:** deployment (BEH-4)
**Depends on:** Task 6
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/docker/test_port_override.py`

**Tests:** `tests/docker/test_port_override.py` (create)

- [ ] **Write failing test**

```python
import os
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True, env={**os.environ, "PORT": "18080", "MCP_PORT": "18081"})


def test_port_env_vars_remap_published_host_ports():
    env = {**os.environ, "PORT": "18080", "MCP_PORT": "18081"}
    subprocess.run(["docker", "compose", "up", "-d"], check=True, env=env)
    ports = subprocess.run(["docker", "compose", "port", "crm-api", "18080"], capture_output=True, text=True, env=env).stdout
    assert "18080" in ports
    mcp_ports = subprocess.run(["docker", "compose", "port", "mcp-server", "18081"], capture_output=True, text=True, env=env).stdout
    assert "18081" in mcp_ports
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_port_override.py`
Expected: FAIL before `docker-compose.yml` interpolates `${PORT}`/`${MCP_PORT}` (n/a once Task 6 lands — run once standalone to confirm the override path genuinely changes the bound port rather than always matching the default, e.g. by first asserting it fails against the *default* ports 8000/8001 with these overridden values).

- [ ] **Implement**

No production code change needed — Task 6's `${PORT:-8000}` / `${MCP_PORT:-8001}` interpolation already implements this. This task exists to prove it with a dedicated, traceable BEH-4 suite.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_port_override.py`
Expected: PASS. `docker compose down -v` after (with the same env) to clean up.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add tests/docker/test_port_override.py
git commit -m "test(deployment): verify PORT/MCP_PORT overrides remap host ports"
```

---

### Task 9: docker compose logs combined output [specialist: none]

**Charter capability:** deployment (BEH-5)
**Depends on:** Task 6
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/docker/test_combined_logs.py`

**Tests:** `tests/docker/test_combined_logs.py` (create)

- [ ] **Write failing test**

```python
import shutil
import subprocess
import time

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_logs_shows_output_from_both_services():
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    time.sleep(5)  # let both services emit at least their startup log lines
    logs = subprocess.run(["docker", "compose", "logs"], capture_output=True, text=True).stdout
    assert "crm-api" in logs
    assert "mcp-server" in logs
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_combined_logs.py`
Expected: FAIL — no `docker-compose.yml` before Task 6; run standalone after Task 6 to confirm real log-prefix behavior (compose prefixes each line with its service name by default).

- [ ] **Implement**

No production code change needed — `docker compose logs`' service-name prefixing is a built-in compose behavior once both services are declared (Task 6). This task exists to prove it with a dedicated, traceable BEH-5 suite.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_combined_logs.py`
Expected: PASS. `docker compose down -v` after to clean up.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add tests/docker/test_combined_logs.py
git commit -m "test(deployment): verify docker compose logs shows combined output"
```

---

### Task 10: Written run instructions (README.md) [specialist: none]

**Charter capability:** deployment (Scope: "Written run instructions ... covering docker compose up, ports, health")
**Depends on:** Task 6
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `README.md`
- Test: `tests/test_readme_docker_instructions.py`

**Tests:** `tests/test_readme_docker_instructions.py` (create)

**Context to load:**
- `../mock-jira/README.md` ("Running with Docker" section — style reference only, not copied verbatim)

- [ ] **Write failing test**

```python
from pathlib import Path


def test_readme_documents_docker_run_instructions():
    text = Path("README.md").read_text()
    assert "docker compose up" in text
    assert "PORT" in text
    assert "MCP_PORT" in text
    assert "localhost" in text
    assert "docker compose logs" in text
    assert "docker compose down" in text
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_readme_docker_instructions.py`
Expected: FAIL — current `README.md` is a stub with none of these phrases.

- [ ] **Implement**

Append to `README.md` a `## Running with Docker` section covering: `docker compose up`; that it builds two images (`crm-api`, which also serves `crm-ui`'s static assets, and `mcp-server`) and starts them in dependency order; `crm-api` published at `http://localhost:8000` (override with `PORT=<port>`); `mcp-server` published at `http://localhost:8001` (override with `MCP_PORT=<port>`); neither port exposed beyond `localhost` by default; the SQLite database lives in the named volume `mock_salesforce_db` and survives `docker compose down` (without `-v`); confirm health via `docker compose ps` or `curl http://localhost:8000/health`; combined logs via `docker compose logs -f`; teardown via `docker compose down` (keep data) or `docker compose down -v` (wipe data).

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_readme_docker_instructions.py`
Expected: PASS.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add README.md tests/test_readme_docker_instructions.py
git commit -m "docs(deployment): document docker compose run instructions in README"
```

---

### Task 11: Clean-checkout acceptance sweep [specialist: none]

**Charter capability:** deployment (Postconditions: single-command bring-up, localhost-only ports)
**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9, Task 10
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/docker/test_clean_checkout_smoke.py`

**Tests:** `tests/docker/test_clean_checkout_smoke.py` (create)

**Context to load:**
- `docker-packaging.spec.md` — Postconditions section in full

- [ ] **Write failing test**

```python
import json
import shutil
import subprocess
import time
import urllib.request

import pytest

pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="docker CLI not available")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_clean_checkout_single_command_bring_up_and_localhost_only_ports():
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)

    _wait_for_http("http://localhost:8000/health", timeout=90)
    _wait_for_http("http://localhost:8001/health", timeout=90)

    config = json.loads(
        subprocess.run(["docker", "compose", "config", "--format", "json"], check=True, capture_output=True, text=True).stdout
    )
    for service in config["services"].values():
        for port in service.get("ports", []):
            host_ip = port.get("host_ip")
            assert host_ip in ("127.0.0.1", "localhost"), f"port not scoped to localhost: {port}"


def _wait_for_http(url, timeout):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - polling until the container is ready
            last_exc = exc
        time.sleep(1)
    raise AssertionError(f"{url} never returned 200: {last_exc}")
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/docker/test_clean_checkout_smoke.py`
Expected: FAIL until every one of Tasks 1-10 is complete (any missing piece breaks either the health polls or the port-scoping assertion).

- [ ] **Implement**

No new production code — this is the capstone acceptance test proving Tasks 1-10 together satisfy the spec's Postconditions. If it fails, the fix belongs in whichever earlier task's artifact is wrong (most likely `docker-compose.yml`'s port declarations if the localhost-scoping assertion fails).

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/docker/test_clean_checkout_smoke.py`
Expected: PASS. Then run the full split gate suite once more: `python3 -m pytest -q` (fast) and `python3 -m pytest -q tests/docker/` (integration) and `ruff check .` (lint) — all green.

- [ ] **Commit**

Branch: `feat/deployment/docker-packaging`

```bash
git add tests/docker/test_clean_checkout_smoke.py
git commit -m "test(deployment): add clean-checkout acceptance sweep for docker packaging"
```

---

## Quality Gates

`.context-index/governance/gates.yaml` exists, so its gate definitions apply (in place of the constitution's plain `Quality Gates` list) — with the `integration-test` gate as wired by Task 3:

| Gate | Tier | Command | Trigger |
|------|------|---------|---------|
| `test` | fast | `python3 -m pytest -q` | post-task, post-implement |
| `lint` | fast | `ruff check .` | post-task |
| `integration-test` | integration | `python3 -m pytest -q tests/docker` | post-implement |

After all 11 tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

- `python3 -m pytest -q` passes (fast gate — excludes `tests/docker/` per Task 3's `pyproject.toml` change)
- `python3 -m pytest -q tests/docker` passes (integration gate — requires Docker Engine running locally; skips gracefully via `pytest.mark.skipif(shutil.which("docker") is None, ...)` in an environment without Docker)
- `ruff check .` passes
- All acceptance criteria from `docker-packaging.spec.md` satisfied: BEH-1 through BEH-6 (Tasks 4-9), the two Error Cases (`DEPLOY_VOLUME_NOT_WRITABLE` in Task 1, `DEPLOY_UPSTREAM_UNREACHABLE` already covered by existing code per Plan Note 5), and both Postconditions (Task 11)
- No constitutional violations introduced: no new inbound repo dependency (only a public `python:3.12-slim` base image), no fixture/identifier changes, no HTTP contract changes (only new internal env vars `HOST` and the `DEPLOY_VOLUME_NOT_WRITABLE`/`DEPLOY_UPSTREAM_UNREACHABLE` error semantics, which are additive)


