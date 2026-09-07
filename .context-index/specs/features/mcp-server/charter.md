---
status: approved
kind: feature
revision: 6
updated: 2026-09-05
---

# Feature Charter: mcp-server

<!-- Feature Charter for the mcp-server module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

mcp-server exposes `crm-api`'s CRUD operations as MCP tools, so an AI agent working in a
consuming course track can create, read, update, and delete Accounts, Contacts, and
Opportunities directly through the Model Context Protocol, without hand-rolling HTTP calls. Like
`crm-ui`, it is a pure client of `crm-api`: it owns no persisted data and never touches the
database directly.

## Scope and Boundaries

### In Scope

- MCP tool definitions mirroring every must-have capability of `crm-api`: full create/read/
  update/delete for Account, Contact, and Opportunity, including Opportunity stage transitions.
- A running MCP server process that translates each tool call into an HTTP call against
  `crm-api` and returns its result (or its error) back through the tool response.
- Structured, JSON-schema tool input/output definitions so any MCP client can discover the tools
  and their parameters without out-of-band documentation.
- Streamable HTTP transport (the MCP spec's transport for a network-reachable, long-running
  server process) so this module can run as its own container, be reached by a remote MCP
  client over the network, and expose a basic health route for deployment healthchecks —
  deliberately not stdio transport, which assumes a client-spawned local subprocess and has no
  listen port to containerize or health-check.
- Listen port and the `crm-api` base URL are both read from environment variables rather than
  hardcoded, so deployment can wire and remap them without a code change.

### Out of Scope

- MCP resources or prompts — only tools are in scope, matching "expose the same CRUD functions."
- Authentication — mirrors `crm-api`'s no-real-auth stance.
- Real-time subscriptions/streaming tool results.
- Any persistence of its own — every read and write is delegated to `crm-api`.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| crm-api | internal module | Sole source of data and sole executor of every write. This module never opens the SQLite file directly. |

## Domain Model

<!-- Like crm-ui, this module owns no persisted entities. The one concept below is a
     view/schema-side wrapper concept, never persisted. -->

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| McpTool | A single MCP tool definition wrapping one crm-api endpoint | `name`, `description`, `input_schema` (JSON Schema), `maps_to_endpoint` |

### Relationships

- Each McpTool maps to exactly one crm-api endpoint; no tool spans more than one endpoint call.

### Invariants

- Every McpTool's `input_schema` validates before the wrapped HTTP call is made — a request the
  schema rejects never reaches `crm-api`.
- A tool call's error response always carries the underlying API's error message verbatim; the
  MCP layer never swallows or rewrites it.

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| list_accounts / create_account / update_account / delete_account tools | Wrap the Account CRUD endpoints | must-have | mvp | implemented |
| get_account tool | Wraps `GET /accounts/{id}` | must-have | mvp | implemented |
| list_contacts / get_contact / create_contact / update_contact / delete_contact tools | Wrap the Contact CRUD endpoints, with `account_id` filtering on list | must-have | mvp | implemented |
| list_opportunities / get_opportunity / create_opportunity / update_opportunity / delete_opportunity tools | Wrap the Opportunity CRUD endpoints, including stage transitions, with `account_id`/`stage_name` filtering on list | must-have | mvp | review-passed |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| MCP resources exposing CRM data | Tools-only scope was explicit in the original request | v2 | — |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|-----------|------|-------------|
| `list_accounts` | MCP tool | List all Accounts |
| `get_account` | MCP tool | Fetch one Account |
| `create_account` | MCP tool | Create an Account |
| `update_account` | MCP tool | Update one or more Account fields |
| `delete_account` | MCP tool | Delete one Account |
| `list_contacts` | MCP tool | List Contacts, optional `account_id` filter |
| `get_contact` | MCP tool | Fetch one Contact |
| `create_contact` | MCP tool | Create a Contact under an Account |
| `update_contact` | MCP tool | Update one or more Contact fields |
| `delete_contact` | MCP tool | Delete one Contact |
| `list_opportunities` | MCP tool | List Opportunities, optional `account_id`/`stage_name` filters |
| `get_opportunity` | MCP tool | Fetch one Opportunity |
| `create_opportunity` | MCP tool | Create an Opportunity under an Account |
| `update_opportunity` | MCP tool | Update one or more Opportunity fields, including `stage_name` |
| `delete_opportunity` | MCP tool | Delete one Opportunity |
| `GET /health` | REST endpoint | Basic liveness response over the Streamable HTTP transport's listen port; backs the deployment healthcheck |

### Consumed APIs

| Interface | Source Module | Description |
|-----------|-------------|-------------|
| `GET /accounts`, `GET /accounts/{id}`, `POST /accounts`, `PATCH /accounts/{id}`, `DELETE /accounts/{id}` | crm-api | Back the Account tools |
| `GET /contacts`, `GET /contacts/{id}`, `POST /contacts`, `PATCH /contacts/{id}`, `DELETE /contacts/{id}` | crm-api | Back the Contact tools |
| `GET /opportunities`, `GET /opportunities/{id}`, `POST /opportunities`, `PATCH /opportunities/{id}`, `DELETE /opportunities/{id}` | crm-api | Back the Opportunity tools |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Tool-call round trip (MCP call → HTTP call → response) is not latency-sensitive at course scale. |
| Availability | Single local process; restarting it is an acceptable recovery path. |
| Security | No real auth. Not exposed beyond the local docker-compose network/host by default — despite being network-reachable (unlike crm-ui/crm-api, which have no reason to be reached off-host at all), it is never exposed to a real, non-local network. |
| Observability | Tool errors surface the underlying API error message unchanged; no structured logging required beyond what aids local debugging. |
