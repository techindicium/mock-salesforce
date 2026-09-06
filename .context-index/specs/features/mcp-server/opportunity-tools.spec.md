---
partial_schema: spec@1
charter: mcp-server
status: review-passed
risk_level: low
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-05
kind: behavioral
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
  - .context-index/specs/features/mcp-server/account-contact-tools.spec.md
---

# Live Spec: Opportunity MCP tools

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `opportunity-lifecycle` spec is implemented and reachable.
- The `account-contact-tools` spec's tools exist — an Opportunity cannot be created without a
  valid `account_id`, which `get_account`/`list_accounts` can supply.
- The MCP server process has been configured with the API's base URL via `API_BASE_URL` and its
  own listen port via `PORT` (Streamable HTTP transport).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_opportunities` is invoked, optionally with `account_id` and/or
  `stage_name` filters, **then** it calls `GET /opportunities` (with the filters as query
  parameters when given) and returns the result as the tool's structured output unmodified.
- **BEH-2** — **When** `get_opportunity` is invoked with a valid `id`, **then** it calls
  `GET /opportunities/{id}` and returns the Opportunity.
- **BEH-3** — **When** `create_opportunity` is invoked with a valid `account_id`, a non-empty
  `name`, and a `close_date`, **then** it calls `POST /opportunities` and returns the created
  Opportunity, `stage_name` defaulting to `Prospecting` when not given.
- **BEH-4** — **When** `create_opportunity` is invoked with an `account_id` that does not exist,
  **then** the tool call errors with the API's `404` message passed through verbatim.
- **BEH-5** — **When** `update_opportunity` is invoked with a valid `id` and one or more mutable
  fields (including `stage_name`), **then** it calls `PATCH /opportunities/{id}` and returns the
  updated Opportunity.
- **BEH-6** — **When** `update_opportunity` or `create_opportunity` is invoked with a
  `stage_name` outside the ten fixed values, **then** the tool call errors with the API's `422`
  message passed through verbatim.
- **BEH-7** — **When** `delete_opportunity` is invoked with a valid `id`, **then** it calls
  `DELETE /opportunities/{id}` and returns a success confirmation.
- **BEH-8** — **When** any tool in this spec is invoked with input that fails its declared input
  schema (e.g. a missing `close_date` on `create_opportunity`), **then** the tool call errors
  before any HTTP request is made.
- **BEH-9** — **When** `crm-api` is unreachable, **then** every tool in this spec returns a
  clear connection-error message rather than hanging or failing silently.

### Postconditions

- An Opportunity created, updated, or deleted through these tools is immediately visible (or
  absent) to a subsequent `list_opportunities`/`get_opportunity` call — no caching layer sits
  between this module and the API.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Input fails the tool's input schema | Tool call errors immediately; no HTTP request made | `MCP_INPUT_INVALID` |
| API returns `404` (unknown `account_id` or Opportunity `id`) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `422` (invalid `stage_name` or missing required field) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API unreachable | Tool call errors with a clear connection message | `MCP_UPSTREAM_UNREACHABLE` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because these tools are thin
  wrappers over `crm-api`'s documented endpoints, never a direct database access.
- **Principle:** "No inbound dependencies." — Applies because mcp-server depends on crm-api,
  never the reverse.
- **Principle:** "Fixture-backed, offline only." — Applies because every call stays within the
  local `mock-salesforce` stack.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define Opportunity tool schemas | JSON-schema input/output definitions for all 5 tools, registered with the MCP server | medium |
| Wire HTTP calls | Translate each tool call into the matching `crm-api` request | medium |
| Error passthrough + connection handling | Verbatim upstream error passthrough; clear message on unreachable API | small |

## Acceptance Criteria

- [ ] `list_opportunities` supports `account_id`/`stage_name` filters (BEH-1)
- [ ] `get_opportunity` returns the Opportunity for a valid id (BEH-2)
- [ ] `create_opportunity` creates and returns an Opportunity, defaulting stage (BEH-3)
- [ ] `create_opportunity` on an unknown `account_id` errors with the API's message verbatim (BEH-4)
- [ ] `update_opportunity` updates and returns the Opportunity, including stage moves (BEH-5)
- [ ] Invalid `stage_name` on create/update errors with the API's message verbatim (BEH-6)
- [ ] `delete_opportunity` deletes and confirms (BEH-7)
- [ ] Schema-invalid input errors before any HTTP request (BEH-8)
- [ ] An unreachable API produces a clear connection-error message (BEH-9)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
