---
status: approved
kind: feature
revision: 8
updated: 2026-09-05
---

# Feature Charter: crm-api

<!-- Feature Charter for the crm-api module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

crm-api provides a Salesforce-shaped CRM domain (accounts, contacts, opportunities) backed by a
local SQLite database, exposed over an HTTP CRUD API. It exists so the adev-course tracks that
need a realistic upstream CRM have something concrete and offline to integrate against, without
any real Salesforce service involved. This is the core module of `mock-salesforce`: the crm-ui
and mcp-server modules are both clients of this API, never the other way around.

## Scope and Boundaries

### In Scope

- Account entity: a company/organization record — Salesforce's core "who we sell to" object.
- Contact entity: a person associated with exactly one Account.
- Opportunity entity: a sales deal associated with exactly one Account, tracked through
  Salesforce's standard ten-stage sales process (`Prospecting` through `Closed Won`/`Closed
  Lost`), mirroring the real Opportunity object's core fields (amount, close date, probability,
  type, lead source, next step).
- Full CRUD HTTP endpoints for Account, Contact, and Opportunity.
- SQLite persistence, a single local file, created fresh on first run; the file path is read
  from an environment variable rather than hardcoded, so it can be bound to a volume in
  deployment.
- Seed fixture data whose identifiers reconcile with `../course-shared/canon/identifiers.md`
  where an overlap exists.
- An OpenAPI-documented HTTP contract (auto-generated from the implementation, not
  hand-maintained).
- A basic liveness/health route, and — when `crm-ui`'s built static assets are present — serving
  them from this same HTTP process at the root path, so the two modules share one origin and one
  running process. Listen port is read from an environment variable rather than hardcoded.

### Out of Scope

- Authentication/authorization — there is no real user model; `owner`-style fields, if any, are
  free-text labels, not accounts with credentials.
- Leads, Cases, Campaigns, Products/Price Books, Quotes, Forecasting, and every other Salesforce
  standard object beyond Account/Contact/Opportunity.
- Custom/configurable sales processes or picklist values — the ten-stage default path is fixed.
- Person Accounts (a Contact with no Account) — every Contact belongs to exactly one Account.
- Multi-currency — `amount` is a plain decimal with no currency-conversion model.
- Multi-tenancy — one SQLite file serves the whole mock instance.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| `../course-shared/canon/identifiers.md` | shared reference (read-only) | Seed fixture identifiers must not collide with the canon's reserved ranges. Not a runtime/code dependency — this repo does not import or execute anything from `course-shared`. |

## Domain Model

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| Account | A company or organization — the entity being sold to | `id`, `name`, `account_type` (`Customer`\|`Prospect`\|`Partner`\|`Other`), `industry`, `website`, `phone`, `billing_street`, `billing_city`, `billing_state`, `billing_postal_code`, `billing_country`, `created_at`, `updated_at` |
| Contact | A person associated with exactly one Account | `id`, `account_id`, `first_name`, `last_name`, `email`, `phone`, `title`, `created_at`, `updated_at` |
| Opportunity | A sales deal associated with exactly one Account | `id`, `account_id`, `name`, `stage_name` (one of the ten fixed stages), `amount`, `close_date`, `probability`, `opportunity_type` (`New Business`\|`Existing Business`), `lead_source` (`Web`\|`Phone Inquiry`\|`Partner Referral`\|`Other`), `next_step`, `is_closed` (derived), `is_won` (derived), `created_at`, `updated_at` |

### Relationships

- Every Contact belongs to exactly one Account (`Contact.account_id` → `Account.id`). An Account
  has zero or more Contacts.
- Every Opportunity belongs to exactly one Account (`Opportunity.account_id` → `Account.id`). An
  Account has zero or more Opportunities.
- Contact and Opportunity are siblings under the same Account; neither references the other.

### Invariants

- An Opportunity's `stage_name` is always one of the ten fixed Salesforce default stages
  (`Prospecting`, `Qualification`, `Needs Analysis`, `Value Proposition`, `Id. Decision Makers`,
  `Perception Analysis`, `Proposal/Price Quote`, `Negotiation/Review`, `Closed Won`,
  `Closed Lost`); the API rejects any other value.
- `is_closed` is true if and only if `stage_name` is `Closed Won` or `Closed Lost`; `is_won` is
  true if and only if `stage_name` is `Closed Won`. Both are server-derived and never accepted as
  client input.
- An Account cannot be deleted while it still has any Contact or Opportunity referencing it (see
  Error Cases in the owning Live Spec) — mirrors Salesforce's own cascade-guard behavior on
  Account deletion.
- A Contact's and an Opportunity's `account_id` is immutable once created — reassigning either to
  a different Account is not supported this milestone (see Deferred Capabilities).

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| Account CRUD | Create, list, get, update, delete Account | must-have | mvp | validated |
| Contact CRUD | Create, list, get, update, delete Contact under an Account | must-have | mvp | validated |
| Opportunity CRUD | Create, list, get, update, delete Opportunity under an Account, including stage transitions | must-have | mvp | validated |
| Seed fixture data | Populate the database with realistic starting Accounts/Contacts/Opportunities on first run, reconciled with `course-shared/canon` identifiers | must-have | mvp | validated |
| OpenAPI contract | Auto-generated, browsable API documentation | should-have | mvp | validated |
| Health route and static asset hosting | Basic liveness route for deployment healthchecks; serve `crm-ui`'s built static assets at the root path when present | must-have | mvp | validated |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| Reassign Contact/Opportunity to a different Account | Not needed by either consuming track yet | v2 | — |
| Leads, Cases, Campaigns, and other standard objects | Out of scope for the initial mock surface | v2 | — |
| Delete Account with existing Contacts/Opportunities (cascade or reassignment) | Deferred until a real cascade/conflict rule is needed — no consumer requires it yet | v2 | — |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|-----------|------|-------------|
| `GET /accounts` | REST endpoint | List all Accounts |
| `POST /accounts` | REST endpoint | Create an Account |
| `GET /accounts/{id}` | REST endpoint | Fetch one Account |
| `PATCH /accounts/{id}` | REST endpoint | Update one or more Account fields |
| `DELETE /accounts/{id}` | REST endpoint | Delete one Account (rejected if it still has Contacts/Opportunities) |
| `GET /contacts` | REST endpoint | List Contacts, optional `account_id` query filter |
| `POST /contacts` | REST endpoint | Create a Contact under an Account |
| `GET /contacts/{id}` | REST endpoint | Fetch one Contact |
| `PATCH /contacts/{id}` | REST endpoint | Update one or more Contact fields |
| `DELETE /contacts/{id}` | REST endpoint | Delete one Contact |
| `GET /opportunities` | REST endpoint | List Opportunities, optional `account_id`/`stage_name` query filters |
| `POST /opportunities` | REST endpoint | Create an Opportunity under an Account |
| `GET /opportunities/{id}` | REST endpoint | Fetch one Opportunity |
| `PATCH /opportunities/{id}` | REST endpoint | Update one or more Opportunity fields, including `stage_name` (the kanban drag action) |
| `DELETE /opportunities/{id}` | REST endpoint | Delete one Opportunity |
| `GET /openapi.json` | REST endpoint | Auto-generated OpenAPI contract document |
| `GET /health` | REST endpoint | Basic liveness response; backs the deployment healthcheck |
| `GET /` and static asset paths | REST endpoint (static) | Serves `crm-ui`'s built static assets when present, so the UI and API share one origin and one process |

### Consumed APIs

None — this module has no inbound dependency on any other module or repo, per the project
constitution's first non-negotiable principle.

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Not a concern at course-fixture volume (dozens to low hundreds of records per entity); no explicit latency target. |
| Availability | Runs as a single local process; no HA requirement. Restarting it is an acceptable recovery path. |
| Security | No real auth. Bound to localhost only by default — never exposed to a real network. |
| Observability | Errors return JSON with a message naming what was rejected (e.g. invalid stage value) and why. No structured logging required beyond what aids local debugging. |
