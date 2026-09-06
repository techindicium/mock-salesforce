---
status: approved
kind: feature
revision: 9
updated: 2026-09-05
---

# Feature Charter: crm-ui

<!-- Feature Charter for the crm-ui module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

crm-ui gives `mock-salesforce` a Salesforce-like web interface — a sales pipeline kanban board,
a detailed opportunity ("deal") page, and full CRUD forms for Accounts, Contacts, and
Opportunities — so the mock reads and feels like a real CRM to anyone browsing it, not just to a
program calling its API. It is a pure client of `crm-api`: it owns no persisted data and never
touches the database directly. It ships as static assets (HTML/CSS/JS) served by `crm-api`'s own
HTTP process — same origin, same container — so its API calls are same-origin relative requests
with no separate server, no CORS configuration, and no runtime base-URL configuration to wire up.

## Scope and Boundaries

### In Scope

- A pipeline kanban board with one column per Opportunity stage (the ten fixed
  `crm-api` stages), showing every open and closed deal grouped by `stage_name`.
- Opportunity cards on the board showing name, account, amount, and close date.
- Moving an Opportunity between stage columns (drag-and-drop, or an equivalent explicit
  control), which calls the API's Opportunity update endpoint to change `stage_name`.
- A detailed deal (Opportunity) page: full field detail, the related Account's summary, and the
  related Account's Contacts as a read-only list, plus edit/delete actions.
- Create/edit/delete forms for Account, Contact, and Opportunity.
- An account switcher/list view listing all Accounts and filtering the board to the selected
  one's Opportunities (or showing all Accounts' Opportunities when none is selected).

### Out of Scope

- Authentication/login — there is no user model to log into.
- Real-time multi-user sync (websockets/live push). A page reload or simple polling is enough.
- Custom pipeline configuration — swimlanes, custom stages, or reordering columns.
- Complex search/filter beyond "which account" (no SOQL-style query builder).
- Mobile-responsive polish — a desktop-width browser is the target.
- Reports, dashboards, and forecasting views.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| crm-api | internal module | Sole source of data, and the process that serves this module's static assets. All reads and writes go through its HTTP API; this module never opens the SQLite file directly. |

## Domain Model

<!-- This module owns no persisted entities — it renders crm-api's Account, Contact, and
     Opportunity one-for-one. The one concept below is a pure view-side grouping, never
     persisted. -->

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| PipelineColumn | A fixed, client-side rendering grouping — not persisted, not an API resource | `stage_name`, `display_label`, `ordinal` |

### Relationships

- A PipelineColumn groups zero or more of `crm-api`'s Opportunity records by their `stage_name`
  field.

### Invariants

- The ten PipelineColumns are fixed and always rendered in the same order (matching the API's
  fixed stage sequence) — the UI never invents a stage value the API does not recognize.
- Every Opportunity shown on the board belongs to the currently selected Account filter (or all
  Accounts, when unfiltered); switching the Account filter fully replaces the visible set, never
  merges a stale set with a new one on screen at once.

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| Render pipeline board | Fetch Opportunities (optionally filtered by Account), group into the ten stage columns | must-have | mvp | planned |
| Move opportunity between stages | Change an Opportunity's `stage_name` via the board (drag-and-drop or equivalent control) | must-have | mvp | planned |
| Deal detail page | Full Opportunity detail, related Account summary, related Contacts list, edit/delete actions | must-have | mvp | review-passed |
| Create/edit/delete opportunity | Form/modal calling the API's Opportunity CRUD endpoints | must-have | mvp | review-passed |
| Create/edit/delete account | Form/modal calling the API's Account CRUD endpoints | must-have | mvp | review-passed |
| Create/edit/delete contact | Form/modal calling the API's Contact CRUD endpoints | must-have | mvp | review-passed |
| Account switcher | List Accounts, select one to filter the board and detail views | should-have | mvp | planned |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| Real-time multi-viewer sync | No multi-user requirement yet; polling/reload suffices | v2 | — |
| Reports/dashboards/forecasting views | No consumer requirement yet; crm-api has no forecasting model to render | v2 | crm-api forecasting support (not chartered) |
| Custom pipeline configuration | Fixed ten-stage model matches crm-api's fixed, permanent stage set | v2 | — |

## Interface Contracts

### Exposed APIs

None — this module is consumed directly by a human through a browser, not programmatically by
other modules.

### Consumed APIs

| Interface | Source Module | Description |
|-----------|-------------|-------------|
| `GET /accounts` | crm-api | Populate the account switcher |
| `POST /accounts` | crm-api | Create-account form |
| `GET /accounts/{id}` | crm-api | Load Account summary for the deal detail page |
| `PATCH /accounts/{id}` | crm-api | Save account edits |
| `DELETE /accounts/{id}` | crm-api | Delete-account action |
| `GET /contacts` | crm-api | Populate the related-contacts list on the deal detail page |
| `POST /contacts` | crm-api | Create-contact form |
| `GET /contacts/{id}` | crm-api | Load full detail for the edit form |
| `PATCH /contacts/{id}` | crm-api | Save contact edits |
| `DELETE /contacts/{id}` | crm-api | Delete-contact action |
| `GET /opportunities` | crm-api | Populate the pipeline board |
| `POST /opportunities` | crm-api | Create-opportunity form |
| `GET /opportunities/{id}` | crm-api | Load full detail for the deal detail page |
| `PATCH /opportunities/{id}` | crm-api | Save edits and stage-move changes |
| `DELETE /opportunities/{id}` | crm-api | Delete-opportunity action |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Board of a few dozen opportunities renders with no perceptible lag on a local connection. |
| Availability | No process of its own — availability is entirely crm-api's, since that is what serves these static assets. Restarting that process is an acceptable recovery path. |
| Security | No real auth. Bound to localhost only by default — never exposed to a real network. |
| Observability | API errors surface to the user as a visible message naming what failed; no structured logging required. |
