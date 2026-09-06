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
  sha: "ff8096a"
  files:
    - .gitignore
    - pyproject.toml
    - requirements.txt
    - src/mock_salesforce/__init__.py
    - src/mock_salesforce/accounts.py
    - src/mock_salesforce/app.py
    - src/mock_salesforce/contacts.py
    - src/mock_salesforce/db.py
    - src/mock_salesforce/errors.py
    - src/mock_salesforce/models.py
    - tests/conftest.py
    - tests/test_accounts.py
    - tests/test_contacts.py
    - tests/test_db_schema.py
  computed-at: "2026-09-06T18:28:05.252Z"
drift_detected: true
---

# Live Spec: Account and Contact management

<!-- Live Spec within the crm-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-api/charter.md -->

## Behavioral Contract

### Preconditions

- The API process is running and its SQLite database file exists (created fresh on first run
  if absent — schema creation is idempotent).
- No authentication is required to reach any endpoint (per charter: no real auth in scope).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /accounts` request is sent with a non-empty `name` (and
  optionally `account_type`, `industry`, `website`, `phone`, and billing address fields),
  **then** the API creates a new Account row and responds `201` with the full created
  representation, including server-assigned `id`, `created_at`, and `updated_at`.
- **BEH-2** — **When** a `POST /accounts` request is missing `name`, **then** the API responds
  `422` naming the missing field, and creates no row.
- **BEH-3** — **When** a `POST /accounts` (or `PATCH /accounts/{id}`) request sets `account_type`
  to a value outside the fixed set (`Customer`, `Prospect`, `Partner`, `Other`), **then** the API
  responds `422` naming the invalid field and its allowed values, and persists no change.
- **BEH-4** — **When** a `GET /accounts` request is sent, **then** the API responds `200` with
  every existing Account as a JSON array, ordered by creation time.
- **BEH-5** — **When** a `GET /accounts/{id}` request is sent for an id that exists, **then**
  the API responds `200` with that Account's full representation.
- **BEH-6** — **When** a `GET /accounts/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-7** — **When** a `PATCH /accounts/{id}` request is sent with one or more mutable fields,
  **then** the API updates exactly those fields, bumps `updated_at`, and responds `200` with the
  full updated representation. `id`, `created_at` are never mutable and are silently ignored if
  present in the request body.
- **BEH-8** — **When** a `DELETE /accounts/{id}` request is sent for an Account that has no
  Contact and no Opportunity referencing it, **then** the API deletes it and responds `204` with
  an empty body.
- **BEH-9** — **When** a `DELETE /accounts/{id}` request is sent for an Account that still has
  at least one Contact or Opportunity referencing it, **then** the API responds `409` naming the
  dependent count, and deletes nothing.
- **BEH-10** — **When** a `POST /contacts` request is sent with a valid `account_id` and a
  non-empty `last_name` (and optionally `first_name`, `email`, `phone`, `title`), **then** the
  API creates a new Contact row and responds `201` with the full created representation.
- **BEH-11** — **When** a `POST /contacts` request names an `account_id` that does not exist,
  **then** the API responds `404` naming the missing account, and creates no Contact.
- **BEH-12** — **When** a `POST /contacts` request is missing `account_id` or `last_name`,
  **then** the API responds `422` naming the missing field, and creates no row.
- **BEH-13** — **When** a `GET /contacts` request is sent, optionally with an `account_id` query
  parameter, **then** the API responds `200` with the matching Contacts as a JSON array —
  unfiltered when no query parameter is given, narrowed to exactly the given account when it is.
- **BEH-14** — **When** a `GET /contacts/{id}` request is sent for an id that exists, **then**
  the API responds `200` with that Contact's full representation.
- **BEH-15** — **When** a `GET /contacts/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-16** — **When** a `PATCH /contacts/{id}` request is sent with one or more mutable fields
  (`first_name`, `last_name`, `email`, `phone`, `title`), **then** the API updates exactly those
  fields, bumps `updated_at`, and responds `200` with the full updated representation. `id`,
  `account_id`, and `created_at` are never mutable and are silently ignored if present in the
  request body — a Contact's owning Account never changes after creation (see Postconditions).
- **BEH-17** — **When** a `DELETE /contacts/{id}` request is sent for an id that exists, **then**
  the API deletes it and responds `204` with an empty body.

### Postconditions

- Every Account or Contact created is immediately retrievable via both its list and get-by-id
  endpoint — no eventual consistency window.
- A deleted Account or Contact no longer appears in any subsequent list or get-by-id call for
  that id (the id is not reused for a future record).
- A Contact's `account_id` never changes once assigned, including across `PATCH` updates —
  there is no move-contact-to-another-account operation in this milestone.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Missing `name` on Account create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Invalid `account_type` on Account create/patch | `422 Unprocessable Entity`, JSON body naming the field and its allowed values | `VALIDATION_ERROR` |
| Unknown Account `id` on get/patch/delete | `404 Not Found`, JSON body naming the missing id | `ACCOUNT_NOT_FOUND` |
| Delete an Account with existing Contacts/Opportunities | `409 Conflict`, JSON body naming the dependent count | `ACCOUNT_HAS_DEPENDENTS` |
| Unknown `account_id` on Contact create | `404 Not Found`, JSON body naming the missing account | `CONTACT_ACCOUNT_NOT_FOUND` |
| Missing `account_id` or `last_name` on Contact create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Unknown Contact `id` on get/patch/delete | `404 Not Found`, JSON body naming the missing id | `CONTACT_NOT_FOUND` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines the Account and Contact CRUD surface, the master-data foundation the rest of
  the CRM builds on.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because these are
  among the first live endpoints; their shapes become the baseline every later change must be
  coordinated against.
- **Principle:** "Fixture-backed, offline only." — Applies because all Account/Contact
  persistence is local SQLite; nothing in this spec reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define the Account and Contact tables | SQLite tables; Contact's `account_id` is a foreign key with a dependent-count check available for delete-guard logic | medium |
| Implement `POST /accounts` and `PATCH /accounts/{id}` | Validation (`name` required, `account_type` enum), insert/update, `updated_at` bump on patch | medium |
| Implement `GET /accounts` and `GET /accounts/{id}` | List ordered by creation time; get-by-id with 404 handling | small |
| Implement `DELETE /accounts/{id}` | Dependent-count check against Contact/Opportunity tables before delete; 409 if any exist | medium |
| Implement `POST /contacts`, `PATCH /contacts/{id}` | Validation (`account_id` existence, `last_name` required), immutable `account_id` enforcement on patch | medium |
| Implement `GET /contacts` with `account_id` filter, `GET /contacts/{id}`, `DELETE /contacts/{id}` | Query builder, get-by-id, delete, all with 404 handling | small |

## Acceptance Criteria

- [x] `POST /accounts` creates an Account and returns 201 with the full representation (BEH-1)
- [x] `POST /accounts` with a missing `name` returns 422 (BEH-2)
- [x] `POST`/`PATCH` with an invalid `account_type` returns 422 and persists no change (BEH-3)
- [x] `GET /accounts` returns all Accounts as a JSON array, ordered by creation time (BEH-4)
- [x] `GET /accounts/{id}` returns 200 for a valid id (BEH-5)
- [x] `GET /accounts/{id}` returns 404 for an unknown id (BEH-6)
- [x] `PATCH /accounts/{id}` updates the given fields and returns 200 (BEH-7)
- [x] `DELETE /accounts/{id}` deletes an Account with no dependents and returns 204 (BEH-8)
- [x] `DELETE /accounts/{id}` with existing Contacts/Opportunities returns 409 and deletes nothing (BEH-9)
- [x] `POST /contacts` creates a Contact under a valid Account and returns 201 (BEH-10)
- [x] `POST /contacts` with an unknown `account_id` returns 404 and creates nothing (BEH-11)
- [x] `POST /contacts` with a missing required field returns 422 (BEH-12)
- [x] `GET /contacts` supports the `account_id` filter, unfiltered when omitted (BEH-13)
- [x] `GET /contacts/{id}` returns 200 for a valid id (BEH-14)
- [x] `GET /contacts/{id}` returns 404 for an unknown id (BEH-15)
- [x] `PATCH /contacts/{id}` updates the given fields, ignores `account_id`, and returns 200 (BEH-16)
- [x] `DELETE /contacts/{id}` deletes an existing Contact and returns 204 (BEH-17)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
