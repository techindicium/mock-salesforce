---
status: approved
kind: cross-cutting
revision: 2
updated: 2026-09-05
---

# Cross-Cutting Charter: deployment

<!-- Cross-Cutting Charter for the deployment concern. Cross-cutting charters
     describe a concern that touches multiple modules. They live under
     specs/cross-cutting/, NOT specs/features/. -->

## Business Intent

deployment packages `mock-salesforce` into a single Docker-based, one-command local runtime with
written run instructions, so a student, instructor, or another track's agent can start the whole
stack without manually managing two separate processes (`crm-api`, which also serves `crm-ui`'s
static assets, and `mcp-server`) or a Python environment.

## Scope

### In Scope

- A Dockerfile for each module that runs its own process: crm-api (which also serves crm-ui's
  static assets) and mcp-server. crm-ui has no Dockerfile of its own — its build output is
  copied into crm-api's image.
- A `docker-compose.yml` wiring both modules together, including a named volume so the SQLite
  file survives container restarts.
- An environment-variable convention each module follows so compose can wire them without code
  changes (e.g. a port, and the API base URL the UI and MCP server call).
- Written run instructions (in this repo's README/CLAUDE.md) covering `docker compose up`, which
  ports are exposed, and how to confirm the stack is healthy.

### Out of Scope

- Cloud deployment or any hosted target — this is a local-only course fixture.
- CI/CD pipeline automation.
- Multi-instance scaling or production-grade orchestration (Kubernetes, etc.).
- Publishing images to a registry — local `docker compose build` is sufficient.

## Affected Modules

| Module | Impact (high / medium / low) | Changes Required |
|---|---|---|
| crm-api | high | Dockerfile; must read its SQLite path from an env var so compose can mount a named volume at that path; also serves crm-ui's static assets, so its image build includes them. |
| crm-ui | low | No separate container — built as static assets and copied into crm-api's image/build step. No env var needed: API calls are same-origin relative requests. |
| mcp-server | medium | Dockerfile; runs Streamable HTTP transport (not stdio), so it has its own listen port and `GET /health` route, and can be containerized and health-checked like crm-api; must read the API's base URL from an env var, since it runs as a separate process/container from crm-api. |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|---|---|---|
| `PORT` env var convention | convention | crm-api and mcp-server both read their listen port from `PORT` rather than hardcoding one, so compose can remap freely. crm-ui has no listen port of its own — it has no process. |
| `API_BASE_URL` env var convention | convention | mcp-server reads the crm-api base URL from this variable instead of hardcoding `localhost`. crm-ui does not need it — its calls are same-origin. |
| `DATABASE_PATH` env var convention | convention | crm-api reads its SQLite file path from this variable so compose can bind it to a named volume. |

### Consumed APIs

| Interface | Source Module | Description |
|---|---|---|
| `GET /health` returning `200` | crm-api | Used by compose's healthcheck so the `mcp-server` container can `depends_on` a healthy API. crm-ui has no runtime dependency here — it is built into crm-api's image, not started as its own container. |

## Quality Attributes

| Attribute | Requirement |
|---|---|
| Performance | Not a concern — this is packaging, not a runtime path. |
| Availability | `docker compose up` brings up both containers (crm-api — which already carries crm-ui's built assets — then mcp-server) in dependency order; restarting the stack is an acceptable recovery path. |
| Security | No ports exposed beyond localhost by default in `docker-compose.yml`. |
| Observability | `docker compose logs` surfaces both containers' output (crm-ui has no separate log stream — its assets are served from within crm-api's process); no additional log aggregation required. |
