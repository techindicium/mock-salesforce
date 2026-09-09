---
partial_schema: implement@1
charter: mcp-server
status: validated
risk_level: low
milestone: v2
revision: 1
charter-revision: 8
created: 2026-09-09
updated: 2026-09-09
depends-on:
  - .context-index/specs/features/crm-api/lead-lifecycle.spec.md
kind: behavioral
source-manifest:
  sha: "pending"
  files:
    - mcp_server/app.py
    - mcp_server/tools/leads.py
    - tests/mcp_server/test_lead_tools.py
  computed-at: "2026-09-09T00:00:00.000Z"
drift_detected: true
---

# Live Spec: Lead MCP tools

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `lead-lifecycle` spec is implemented and reachable.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_leads` is called, optionally with `status` and/or `converted`,
  **then** it returns the JSON array from `GET /leads` with the same filters applied.
- **BEH-2** — **When** `get_lead(id)` is called for an id that exists, **then** it returns that
  Lead's full representation from `GET /leads/{id}`.
- **BEH-3** — **When** `create_lead` is called with at least `last_name` and `company`, **then**
  it returns the created Lead from `POST /leads`, with every other optional parameter omitted
  from the request body when not given (never sent as an explicit `null`).
- **BEH-4** — **When** `update_lead(id, ...)` is called with one or more fields, **then** it
  returns the updated Lead from `PATCH /leads/{id}`, sending only the fields the caller actually
  provided.
- **BEH-5** — **When** `delete_lead(id)` is called, **then** it calls `DELETE /leads/{id}` and
  returns `{"deleted": true, "id": id}` on success — mirrors `delete_account`'s tool contract.
- **BEH-6** — **When** `convert_lead(id, ...)` is called, **then** it calls
  `POST /leads/{id}/convert` with `account_id`, `contact_id`, `create_opportunity`,
  `opportunity_name`, and `opportunity_close_date` forwarded exactly as given (only the
  non-`None` ones included in the request body), and returns the updated Lead representation.
- **BEH-7** — **When** any Lead tool's underlying HTTP call fails (4xx or 5xx, or the upstream is
  unreachable), **then** the tool call raises with the underlying API's error code/message
  verbatim (or the unreachable-upstream message) — never swallowed or rewritten, matching every
  other tool in this module.

### Postconditions

- Every Lead tool call is a single HTTP round trip to `crm-api` — no tool caches or re-derives
  Lead state locally between calls.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any Lead tool called with an unknown `id` | Tool call raises with `crm-api`'s `404 LEAD_NOT_FOUND` passed through verbatim | `LEAD_NOT_FOUND` |
| `convert_lead` on an already-converted Lead | Tool call raises with `crm-api`'s `409 LEAD_ALREADY_CONVERTED` passed through verbatim | `LEAD_ALREADY_CONVERTED` |
| `crm-api` unreachable | Tool call raises `McpUpstreamUnreachableError` naming the base URL | n/a |

## System Constitution Reference

- **Principle:** "mcp-server... never touches the database directly" (charter Business Intent) —
  Applies because every Lead tool is a thin wrapper delegating to `CrmApiClient`, identical in
  shape to the existing Account/Contact/Opportunity tools.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Add `mcp_server/tools/leads.py` | `list_leads`/`get_lead`/`create_lead`/`update_lead`/`delete_lead`/`convert_lead` wrapper functions mirroring `tools/accounts.py` | small |
| Wire `@mcp.tool()` definitions into `mcp_server/app.py` | One decorated function per wrapper, matching the existing Account/Contact/Opportunity tool style | small |
| Add `tests/mcp_server/test_lead_tools.py` | Mirrors `test_account_tools.py`'s fake-transport test pattern | small |

## Acceptance Criteria

- [x] All six Lead tools round-trip correctly against a faked `crm-api` transport (BEH-1..BEH-6)
- [x] Tool errors surface the underlying API error verbatim (BEH-7)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
