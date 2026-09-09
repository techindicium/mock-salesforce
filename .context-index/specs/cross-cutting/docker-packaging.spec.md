---
partial_schema: implement@1
affects: [crm-api, crm-ui, mcp-server]
status: validated
risk_level: low
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-07
kind: behavioral
mode: cross-cutting
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
  - .context-index/specs/features/crm-api/fixture-seeding.spec.md
  - .context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md
  - .context-index/specs/features/crm-ui/pipeline-board-view.spec.md
  - .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.spec.md
  - .context-index/specs/features/mcp-server/account-contact-tools.spec.md
  - .context-index/specs/features/mcp-server/opportunity-tools.spec.md
source-manifest:
  sha: "c8730d1"
  files:
    - .context-index/governance/gates.yaml
    - .dockerignore
    - README.md
    - docker-compose.yml
    - docker/crm-api/Dockerfile
    - docker/mcp-server/Dockerfile
    - mcp_server/app.py
    - pyproject.toml
    - src/mock_salesforce/db.py
    - tests/docker/test_clean_checkout_smoke.py
    - tests/docker/test_combined_logs.py
    - tests/docker/test_compose_build_and_startup.py
    - tests/docker/test_crm_api_image.py
    - tests/docker/test_gate_wiring.py
    - tests/docker/test_mcp_server_image.py
    - tests/docker/test_port_override.py
    - tests/docker/test_volume_persistence.py
    - tests/mcp_server/test_health_route.py
    - tests/test_db_path_not_writable.py
    - tests/test_readme_docker_instructions.py
  computed-at: "2026-09-07T05:02:00.076Z"
drift_detected: true
---

# Live Spec: Docker packaging and run instructions

<!-- Live Spec for the deployment cross-cutting concern.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/cross-cutting/deployment/charter.md -->

## Behavioral Contract

### Preconditions

- All three modules (`crm-api`, `crm-ui`, `mcp-server`) are implemented and pass their own
  specs' acceptance criteria before packaging is meaningful to test.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `docker compose build` is run, **then** it builds exactly two images:
  one for `crm-api` (which bundles `crm-ui`'s built static assets during the build step, not at
  runtime), and one for `mcp-server`.
- **BEH-2** — **When** `docker compose up` is run, **then** `crm-api` starts first and becomes
  healthy (`GET /health` returns `200`) before `mcp-server` starts, and `mcp-server` can reach
  it via `API_BASE_URL`.
- **BEH-3** — **When** the stack is running and `docker compose down` (without `-v`) is followed
  by `docker compose up` again, **then** the SQLite database file's contents persist unchanged —
  the named volume survives the down/up cycle.
- **BEH-4** — **When** a developer overrides `PORT` via environment variables, **then** compose
  remaps the exposed host ports with no code change in either module.
- **BEH-5** — **When** `docker compose logs` is run, **then** both containers' output appears in
  one combined stream.
- **BEH-6** — **When** `mcp-server`'s container starts, **then** it also exposes `GET /health`
  over its own Streamable HTTP listen port, so it can be probed the same way `crm-api` is.

### Postconditions

- Running `docker compose up` from a clean checkout (no prior containers, volumes, or images)
  brings up a fully working stack with no manual step beyond that one command.
- No port is exposed beyond localhost by default.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| The `DATABASE_PATH` volume mount is not writable | `crm-api` container fails startup with a clear error naming the path | `DEPLOY_VOLUME_NOT_WRITABLE` |
| `API_BASE_URL` is unset or unreachable for `mcp-server` | `mcp-server` container logs a clear connection error rather than crash-looping silently | `DEPLOY_UPSTREAM_UNREACHABLE` |

## Module Impact Map

| Module | Impact | Changes Required |
|--------|--------|-------------------|
| crm-api | high | Dockerfile; reads `DATABASE_PATH` and `PORT` from env; multi-stage build bundles crm-ui's static assets; exposes `GET /health` |
| crm-ui | low | No Dockerfile of its own — static build output copied into crm-api's image at build time |
| mcp-server | medium | Dockerfile; reads `API_BASE_URL` and `PORT` from env; runs Streamable HTTP transport with its own `GET /health` |

## Integration Points

1. `crm-api` ↔ compose: `GET /health` backs the healthcheck; `DATABASE_PATH` binds to a named volume.
2. `mcp-server` ↔ `crm-api`: `depends_on` the API's healthcheck; reads `API_BASE_URL` to reach it.
3. `crm-ui` ↔ `crm-api` (build-time only): static assets are copied into the API's image during `docker compose build`; there is no runtime integration point.

## System Constitution Reference

- **Principle:** "No inbound dependencies." — Applies because packaging must not introduce a
  dependency on another repo in the workspace. A public base image (e.g. `python:3.11-slim`)
  from a public registry is not an inbound repo dependency and is fine.
- **Principle:** "Fixture-backed, offline only." — Applies because no port is exposed beyond
  localhost by default, and the stack never reaches a real external network.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| `crm-api` Dockerfile | Multi-stage: build crm-ui's static assets, then the Python runtime image; reads `DATABASE_PATH`/`PORT` from env; exposes `GET /health` | medium |
| `mcp-server` Dockerfile | Python runtime image; Streamable HTTP transport; reads `API_BASE_URL`/`PORT` from env; exposes `GET /health` | small |
| `docker-compose.yml` | Wire both services, named volume for the SQLite file, healthchecks, `depends_on` | medium |
| Run instructions | Document `docker compose up`, exposed ports, and how to confirm the stack is healthy, in this repo's README/CLAUDE.md | small |

## Acceptance Criteria

- [x] `docker compose build` produces exactly two images (BEH-1)
- [x] `docker compose up` starts crm-api first, then mcp-server once healthy (BEH-2)
- [x] The SQLite file survives a `docker compose down`/`up` cycle (BEH-3)
- [x] `PORT` overrides remap host ports with no code change (BEH-4)
- [x] `docker compose logs` shows both containers' combined output (BEH-5)
- [x] `mcp-server` exposes its own health route on its own port (BEH-6)
- [x] No port is exposed beyond localhost by default
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
