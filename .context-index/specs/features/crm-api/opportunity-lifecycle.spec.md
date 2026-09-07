---
partial_schema: implement@1
charter: crm-api
status: validated
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-06
kind: behavioral
source-manifest:
  sha: "1a4d668"
  files:
    - src/mock_salesforce/app.py
    - src/mock_salesforce/db.py
    - src/mock_salesforce/models.py
    - src/mock_salesforce/opportunities.py
    - tests/test_db_schema.py
    - tests/test_opportunities.py
  computed-at: "2026-09-06T19:30:20.200Z"
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
drift_detected: true
---

# Live Spec: Opportunity lifecycle CRUD

<!-- Live Spec within the crm-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-api/charter.md -->

## Behavioral Contract

### Preconditions

- The `account-and-contact-management` spec's endpoints exist — Opportunities cannot be created
  without an Account to attach to.
- The API process is running and its SQLite database is available.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /opportunities` request is sent with a valid `account_id`, a
  non-empty `name`, and a `close_date`, **then** the API creates the Opportunity with
  `stage_name` defaulting to `Prospecting` when not given, `is_closed`/`is_won` server-derived
  from the effective `stage_name`, and responds `201` with the full representation.
- **BEH-2** — **When** a `POST /opportunities` request names an `account_id` that does not
  exist, **then** the API responds `404` naming the missing account, and creates no Opportunity.
- **BEH-3** — **When** a `POST /opportunities` request is missing `name`, `account_id`, or
  `close_date`, **then** the API responds `422` naming the missing field, and creates no row.
- **BEH-4** — **When** a `GET /opportunities` request is sent, optionally with `account_id`
  and/or `stage_name` query parameters, **then** the API responds `200` with the matching
  Opportunities as a JSON array — unfiltered when no query parameters are given, narrowed to
  exactly the given account/stage when they are.
- **BEH-5** — **When** a `GET /opportunities/{id}` request is sent for an id that exists,
  **then** the API responds `200` with that Opportunity's full representation.
- **BEH-6** — **When** a `GET /opportunities/{id}` request is sent for an id that does not
  exist, **then** the API responds `404` naming the missing id.
- **BEH-7** — **When** a `PATCH /opportunities/{id}` request is sent with one or more mutable
  fields (`name`, `stage_name` — the kanban drag action —, `amount`, `close_date`, `probability`,
  `opportunity_type`, `lead_source`, `next_step`), **then** the API updates exactly those
  fields, recomputes `is_closed`/`is_won` from the resulting `stage_name`, bumps `updated_at`,
  and responds `200` with the full updated representation. `id`, `account_id`, `is_closed`,
  `is_won`, and `created_at` are never mutable and are silently ignored if present in the
  request body — an Opportunity's owning Account never changes after creation (see
  Postconditions).
- **BEH-8** — **When** a `POST /opportunities` or `PATCH /opportunities/{id}` request sets
  `stage_name` to a value outside the ten fixed stages, **then** the API responds `422` naming
  the invalid field and its allowed values, and persists no change.
- **BEH-9** — **When** a `DELETE /opportunities/{id}` request is sent for an id that exists,
  **then** the API deletes it and responds `204` with an empty body.

### Postconditions

- Every Opportunity created via `POST /opportunities` is immediately retrievable via
  `GET /opportunities`, `GET /opportunities?account_id=...`, `GET /opportunities?stage_name=...`,
  and `GET /opportunities/{id}` — no eventual consistency window.
- A deleted Opportunity no longer appears in any subsequent `GET /opportunities` or
  `GET /opportunities/{id}` call for that id (the id is not reused for a future Opportunity).
- An Opportunity's `account_id` never changes once assigned, including across `PATCH` updates —
  there is no move-opportunity-to-another-account operation in this milestone.
- `is_closed` and `is_won` are always consistent with the Opportunity's current `stage_name`
  (see charter Invariants) — they are never independently stale after any successful `PATCH`.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Unknown `account_id` on create | `404 Not Found`, JSON body naming the missing account | `OPPORTUNITY_ACCOUNT_NOT_FOUND` |
| Missing `name`, `account_id`, or `close_date` on create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Unknown Opportunity `id` on get/patch/delete | `404 Not Found`, JSON body naming the missing id | `OPPORTUNITY_NOT_FOUND` |
| Invalid `stage_name` value on create/patch | `422 Unprocessable Entity`, JSON body naming the invalid field and its allowed values | `VALIDATION_ERROR` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines the full Opportunity CRUD surface, including the stage-transition endpoint
  that `crm-ui`'s pipeline board depends on entirely.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because
  `PATCH /opportunities/{id}` (the stage-transition endpoint) is the single most consumer-visible
  behavior in the whole module; its field/stage semantics are the baseline every later change
  must be coordinated against.
- **Principle:** "Fixture-backed, offline only." — Applies because all Opportunity persistence
  is local SQLite; nothing in this spec reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define the Opportunity table | SQLite table with an `account_id` foreign key, `stage_name` enum column, and derived `is_closed`/`is_won` computed at read/write time | medium |
| Implement `POST /opportunities` | Validation, account-existence check, `stage_name` default and enum validation, insert, return 201 | medium |
| Implement `GET /opportunities` with filters | Query builder supporting optional `account_id`/`stage_name` params | small |
| Implement `GET /opportunities/{id}` | Query by id, 404 if missing | small |
| Implement `PATCH /opportunities/{id}` | Partial update, `stage_name` enum validation, `is_closed`/`is_won` recomputation, `updated_at` bump | medium |
| Implement `DELETE /opportunities/{id}` | Delete by id, 404 if missing, 204 on success | small |

## Acceptance Criteria

- [x] `POST /opportunities` creates an Opportunity defaulting to `Prospecting`, returns 201 (BEH-1)
- [x] `POST /opportunities` with an unknown `account_id` returns 404 and creates nothing (BEH-2)
- [x] `POST /opportunities` with a missing required field returns 422 (BEH-3)
- [x] `GET /opportunities` supports `account_id` and `stage_name` filters, unfiltered when omitted (BEH-4)
- [x] `GET /opportunities/{id}` returns 200 for a valid id (BEH-5)
- [x] `GET /opportunities/{id}` returns 404 for an unknown id (BEH-6)
- [x] `PATCH /opportunities/{id}` updates the given fields (including stage) and returns 200 (BEH-7)
- [x] `PATCH`/`POST` with an invalid `stage_name` returns 422 and persists no change (BEH-8)
- [x] `DELETE /opportunities/{id}` deletes an existing Opportunity and returns 204 (BEH-9)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
