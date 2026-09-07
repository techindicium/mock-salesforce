---
partial_schema: implement@1
charter: mcp-server
status: validated
risk_level: low
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-06
kind: behavioral
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
source-manifest:
  sha: "b8e1843"
  files:
    - mcp_server/__init__.py
    - mcp_server/app.py
    - mcp_server/client.py
    - mcp_server/errors.py
    - mcp_server/requirements.txt
    - mcp_server/tools/__init__.py
    - mcp_server/tools/accounts.py
    - mcp_server/tools/contacts.py
    - pyproject.toml
    - tests/mcp_server/test_account_tools.py
    - tests/mcp_server/test_connection_handling.py
    - tests/mcp_server/test_contact_tools.py
    - tests/mcp_server/test_input_validation.py
  computed-at: "2026-09-07T01:46:15.261Z"
---

# Live Spec: Account and Contact MCP tools

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `account-and-contact-management` spec is implemented and reachable.
- The MCP server process has been configured with the API's base URL via `API_BASE_URL` and its
  own listen port via `PORT` (Streamable HTTP transport).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_accounts` is invoked, **then** it calls `GET /accounts` and returns
  the result as the tool's structured output unmodified.
- **BEH-2** — **When** `get_account` is invoked with a valid `id`, **then** it calls
  `GET /accounts/{id}` and returns the Account.
- **BEH-3** — **When** `create_account` is invoked with a non-empty `name`, **then** it calls
  `POST /accounts` and returns the created Account.
- **BEH-4** — **When** `update_account` is invoked with a valid `id` and one or more mutable
  fields, **then** it calls `PATCH /accounts/{id}` and returns the updated Account.
- **BEH-5** — **When** `delete_account` is invoked with a valid `id`, **then** it calls
  `DELETE /accounts/{id}` and returns a success confirmation, or the API's `409`/
  `ACCOUNT_HAS_DEPENDENTS` message verbatim if the Account still has Contacts or Opportunities.
- **BEH-6** — **When** `list_contacts` is invoked, optionally with an `account_id` filter,
  **then** it calls `GET /contacts` (with the filter as a query parameter when given) and
  returns the result unmodified.
- **BEH-7** — **When** `get_contact`, `create_contact`, `update_contact`, or `delete_contact` is
  invoked with valid input, **then** it calls the matching `crm-api` Contact endpoint and
  returns its result.
- **BEH-8** — **When** any tool in this spec is invoked with input that fails its declared input
  schema (e.g. a missing `name` on `create_account`), **then** the tool call errors before any
  HTTP request is made.
- **BEH-9** — **When** `crm-api` is unreachable, **then** every tool in this spec returns a
  clear connection-error message rather than hanging or failing silently.

### Postconditions

- An Account or Contact created, updated, or deleted through these tools is immediately visible
  (or absent) to a subsequent `list_accounts`/`list_contacts`/`get_account`/`get_contact` call —
  no caching layer sits between this module and the API.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Input fails the tool's input schema | Tool call errors immediately; no HTTP request made | `MCP_INPUT_INVALID` |
| API returns `404` (unknown id) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `409` (`ACCOUNT_HAS_DEPENDENTS`) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `422` (validation error that passed the tool's own schema but fails the API's) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
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
| Define Account/Contact tool schemas | JSON-schema input/output definitions for all 9 tools, registered with the MCP server | medium |
| Wire HTTP calls | Translate each tool call into the matching `crm-api` request | medium |
| Error passthrough + connection handling | Verbatim upstream error passthrough; clear message on unreachable API | small |

## Acceptance Criteria

- [x] `list_accounts` returns the API's account list unmodified (BEH-1)
- [x] `get_account` returns the Account for a valid id (BEH-2)
- [x] `create_account` creates and returns an Account on valid input (BEH-3)
- [x] `update_account` updates and returns the Account (BEH-4)
- [x] `delete_account` deletes, or errors with 409/ACCOUNT_HAS_DEPENDENTS verbatim (BEH-5)
- [x] `list_contacts` supports the `account_id` filter (BEH-6)
- [x] `get_contact`/`create_contact`/`update_contact`/`delete_contact` call the matching endpoint (BEH-7)
- [x] Schema-invalid input errors before any HTTP request (BEH-8)
- [x] An unreachable API produces a clear connection-error message (BEH-9)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
