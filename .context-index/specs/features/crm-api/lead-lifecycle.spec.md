---
partial_schema: implement@1
charter: crm-api
status: validated
risk_level: medium
milestone: v2
revision: 1
charter-revision: 10
created: 2026-09-09
updated: 2026-09-09
kind: behavioral
source-manifest:
  sha: "pending"
  files:
    - src/mock_salesforce/app.py
    - src/mock_salesforce/db.py
    - src/mock_salesforce/models.py
    - src/mock_salesforce/leads.py
    - src/mock_salesforce/seed.py
    - tests/test_db_schema.py
    - tests/test_leads.py
    - tests/test_openapi.py
  computed-at: "2026-09-09T00:00:00.000Z"
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
drift_detected: true
---

# Live Spec: Lead lifecycle CRUD and conversion

<!-- Live Spec within the crm-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-api/charter.md -->

## Behavioral Contract

### Preconditions

- The API process is running and its SQLite database is available.
- The `account-and-contact-management` spec's Account/Contact endpoints exist — Lead conversion
  attaches to or creates records through those same tables.
- The `opportunity-lifecycle` spec's Opportunity endpoint exists — Lead conversion can optionally
  create an Opportunity through that same table.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /leads` request is sent with a non-empty `last_name` and
  `company`, **then** the API creates the Lead with `status` defaulting to `New` when not given,
  `converted` server-derived as `false`, all `converted_*` fields `null`, and responds `201` with
  the full representation.
- **BEH-2** — **When** a `POST /leads` request is missing `last_name` or `company`, **then** the
  API responds `422` naming the missing field, and creates no row.
- **BEH-3** — **When** a `POST /leads` or `PATCH /leads/{id}` request sets `status` to a value
  outside the four fixed values, or `rating` to a value outside `Hot`/`Warm`/`Cold`, **then** the
  API responds `422` naming the invalid field and its allowed values, and persists no change.
- **BEH-4** — **When** a `GET /leads` request is sent, optionally with `status` and/or
  `converted` query parameters, **then** the API responds `200` with the matching Leads as a JSON
  array — unfiltered when no query parameters are given, narrowed to exactly the given
  status/converted-state when they are.
- **BEH-5** — **When** a `GET /leads/{id}` request is sent for an id that exists, **then** the
  API responds `200` with that Lead's full representation.
- **BEH-6** — **When** a `GET /leads/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-7** — **When** a `PATCH /leads/{id}` request is sent with one or more mutable fields
  (`first_name`, `last_name`, `company`, `title`, `email`, `phone`, `lead_source`, `status`,
  `rating`) on a Lead that is not yet converted, **then** the API updates exactly those fields,
  bumps `updated_at`, and responds `200` with the full updated representation. `id`, `converted`,
  and every `converted_*` field are never mutable and are silently ignored if present.
- **BEH-8** — **When** a `PATCH /leads/{id}` or `DELETE /leads/{id}` request is sent for a Lead
  whose `converted` is already `true`, **then** the API responds `409` and persists no change —
  a converted Lead is frozen.
- **BEH-9** — **When** a `DELETE /leads/{id}` request is sent for an unconverted Lead that
  exists, **then** the API deletes it and responds `204` with an empty body.
- **BEH-10** — **When** a `POST /leads/{id}/convert` request is sent for an unconverted Lead with
  no `account_id`/`contact_id` in the body, **then** the API creates a new Account (`name` = the
  Lead's `company`) and a new Contact under it (`first_name`/`last_name`/`email`/`phone`/`title`
  copied from the Lead), sets the Lead's `converted_account_id`/`converted_contact_id` to the
  created records' ids, sets `converted_at` to now (so `converted` reads `true`), and responds
  `200` with the Lead's full updated representation.
- **BEH-11** — **When** a `POST /leads/{id}/convert` request body names an existing `account_id`,
  **then** the API attaches the conversion to that Account instead of creating a new one; when it
  additionally names an existing `contact_id` that belongs to that same Account, the API attaches
  to that Contact instead of creating a new one.
- **BEH-12** — **When** a `POST /leads/{id}/convert` request body sets `create_opportunity: true`,
  **then** the API also creates an Opportunity under the resolved Account — `name` defaults to
  the Lead's `company` when `opportunity_name` is not given, `close_date` comes from
  `opportunity_close_date` (required in this case), `stage_name` defaults to `Prospecting`, and
  `lead_source` copies the Lead's `lead_source` — and sets the Lead's `converted_opportunity_id`
  to the created Opportunity's id. When `create_opportunity` is not `true` (the default),
  `converted_opportunity_id` stays `null` and no Opportunity is created.
- **BEH-13** — **When** a `POST /leads/{id}/convert` request is sent for a Lead whose `converted`
  is already `true`, **then** the API responds `409` and creates/attaches nothing further.

### Postconditions

- Every Lead created via `POST /leads` is immediately retrievable via `GET /leads`,
  `GET /leads?status=...`, `GET /leads?converted=...`, and `GET /leads/{id}` — no eventual
  consistency window.
- A deleted Lead no longer appears in any subsequent `GET /leads` or `GET /leads/{id}` call for
  that id (the id is not reused for a future Lead).
- Conversion is atomic: either the Account/Contact/Opportunity are created (or attached) and the
  Lead is marked converted all together, or — on any error partway through (e.g. an
  `account_id`/`contact_id` that turns out not to exist) — none of it happens and the Lead
  remains unconverted.
- Once `converted` is `true` for a Lead, it stays `true` forever — there is no unconvert
  operation in this milestone (see charter Deferred Capabilities / Invariants).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Missing `last_name` or `company` on create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Invalid `status` or `rating` value on create/patch | `422 Unprocessable Entity`, JSON body naming the invalid field and its allowed values | `VALIDATION_ERROR` |
| Unknown Lead `id` on get/patch/delete/convert | `404 Not Found`, JSON body naming the missing id | `LEAD_NOT_FOUND` |
| `PATCH`/`DELETE`/`convert` on an already-converted Lead | `409 Conflict` | `LEAD_ALREADY_CONVERTED` |
| `convert` body names an `account_id` that does not exist | `404 Not Found`, JSON body naming the missing account | `LEAD_CONVERT_ACCOUNT_NOT_FOUND` |
| `convert` body names a `contact_id` that does not exist | `404 Not Found`, JSON body naming the missing contact | `LEAD_CONVERT_CONTACT_NOT_FOUND` |
| `convert` body names a `contact_id` that exists but does not belong to the resolved `account_id` | `422 Unprocessable Entity` | `LEAD_CONVERT_CONTACT_ACCOUNT_MISMATCH` |
| `convert` body sets `create_opportunity: true` without `opportunity_close_date` | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines the full Lead CRUD surface plus the conversion endpoint that a
  marketing-automation exercise would drive end-to-end.
- **Principle:** "Adding new mock endpoints that extend (not break) the existing contract"
  (Autonomous / Agent May Decide) — Applies directly: every endpoint here is new; no existing
  Account/Contact/Opportunity endpoint's path, request, or response shape changes.
- **Principle:** "Fixture-backed, offline only." — Applies because all Lead persistence and
  conversion logic is local SQLite; nothing in this spec reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define the Lead table | SQLite table with fixed `status` values, optional `rating`, and nullable `converted_at`/`converted_account_id`/`converted_contact_id`/`converted_opportunity_id` | small |
| Implement `POST /leads` | Validation (`last_name`/`company` required), `status` default and enum validation, insert, return 201 | small |
| Implement `GET /leads` with filters | Query builder supporting optional `status`/`converted` params | small |
| Implement `GET /leads/{id}` | Query by id, 404 if missing | small |
| Implement `PATCH /leads/{id}` | Partial update, enum validation, 409 guard on already-converted, `updated_at` bump | medium |
| Implement `DELETE /leads/{id}` | 409 guard on already-converted, delete by id, 404 if missing, 204 on success | small |
| Implement `POST /leads/{id}/convert` | Resolve/create Account, resolve/create Contact, optional Opportunity creation, mark Lead converted — all in one transaction | large |
| Seed a handful of demo Leads | Extend `seed.py` with realistic unconverted (and one pre-converted) Lead rows | small |

## Acceptance Criteria

- [x] `POST /leads` creates a Lead defaulting `status` to `New`, returns 201 (BEH-1)
- [x] `POST /leads` with a missing required field returns 422 (BEH-2)
- [x] Invalid `status`/`rating` on create/patch returns 422 (BEH-3)
- [x] `GET /leads` supports `status` and `converted` filters, unfiltered when omitted (BEH-4)
- [x] `GET /leads/{id}` returns 200 for a valid id (BEH-5)
- [x] `GET /leads/{id}` returns 404 for an unknown id (BEH-6)
- [x] `PATCH /leads/{id}` updates the given fields on an unconverted Lead and returns 200 (BEH-7)
- [x] `PATCH`/`DELETE`/`convert` on an already-converted Lead returns 409 (BEH-8, BEH-13)
- [x] `DELETE /leads/{id}` deletes an unconverted Lead and returns 204 (BEH-9)
- [x] `POST /leads/{id}/convert` with no body creates a new Account+Contact and marks the Lead converted (BEH-10)
- [x] `POST /leads/{id}/convert` attaches to an existing `account_id`/`contact_id` when given (BEH-11)
- [x] `POST /leads/{id}/convert` with `create_opportunity: true` also creates an Opportunity (BEH-12)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
