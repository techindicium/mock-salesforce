---
partial_schema: spec@1
charter: crm-ui
status: validated
kind: behavioral
milestone: v2
revision: 1
charter-revision: 15
created: 2026-09-09
updated: 2026-09-09
source-manifest:
  sha: "pending"
  files:
    - static/leads.html
    - static/js/leads.js
    - static/js/api.js
    - static/css/board.css
    - static/index.html
    - static/accounts.html
    - static/contacts.html
    - static/deal.html
    - tests/test_ui_leads_page.py
    - tests/test_ui_board_page.py
    - tests/test_ui_accounts_page.py
    - tests/test_ui_contacts_page.py
    - tests/test_ui_deal_page.py
    - tests/test_css_component_coverage.py
  computed-at: "2026-09-09T00:00:00.000Z"
depends-on:
  - .context-index/specs/features/crm-api/lead-lifecycle.spec.md
  - .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md
drift_detected: true
---

# Live Spec: Leads view

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `lead-lifecycle` spec is implemented and reachable at the same origin.
- The persistent sidebar/nav pattern from `sidebar-navigation-and-contacts-view` exists — this
  spec adds a fourth nav item to it, on every page, rather than inventing a new nav pattern.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `leads.html` loads, **then** it fetches and renders every Lead as a list
  row showing name, company, status, and rating, using the same list-row visual/DOM pattern as
  the standalone Contacts view.
- **BEH-2** — **When** the user submits the new-Lead form with at least `last_name` and
  `company`, **then** the UI calls `POST /leads`, hides the form on success, and refreshes the
  list to include the new Lead.
- **BEH-3** — **When** the user clicks "Edit" on a Lead row, **then** the form pre-fills with
  that Lead's current field values and submitting it calls `PATCH /leads/{id}`.
- **BEH-4** — **When** the user clicks "Delete" on a Lead row and confirms, **then** the UI calls
  `DELETE /leads/{id}` and removes it from the list on success; on a `409
  LEAD_ALREADY_CONVERTED` response, the UI shows that message inline and the row stays in the
  list (mirrors the Accounts view's 409-dependents handling).
- **BEH-5** — **When** the user clicks "Convert" on an unconverted Lead row, **then** the UI
  calls `POST /leads/{id}/convert` with no body (create-new-Account/-Contact path) and, on
  success, navigates to `accounts.html` (or, when the response's `converted_opportunity_id` is
  non-null, to `deal.html?id={converted_opportunity_id}`).
- **BEH-6** — **When** a Lead's `converted` is `true`, **then** its row renders without an Edit,
  Delete, or Convert action (mirroring the API's frozen-after-conversion invariant) and instead
  shows a "Converted" label.
- **BEH-7** — **When** any of the five pages (`index.html`, `deal.html`, `accounts.html`,
  `contacts.html`, `leads.html`) loads, **then** the persistent sidebar/nav renders four items
  (Opportunities, Accounts, Contacts, Leads) with exactly one marked active for the current page.

### Postconditions

- The Leads list always reflects the current server state after any create/edit/delete/convert
  action — no stale row lingers after a successful mutation.
- Navigating to any of the other four pages and back to `leads.html` re-fetches the list fresh;
  no client-side cache outlives a single page load.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `POST /leads` validation failure (e.g. missing `last_name`/`company`) | Inline form error naming the field, form stays open | `VALIDATION_ERROR` |
| `DELETE /leads/{id}` on an already-converted Lead | Inline error naming the conflict, row stays in the list | `LEAD_ALREADY_CONVERTED` |
| Any Lead API call fails with a network error or 5xx | Error banner shows a message naming the failed action | n/a |

## System Constitution Reference

- **Principle:** "Internal refactors that don't change the HTTP surface" / crm-ui's own charter
  scope — Applies because this spec adds a new page (`leads.html`) and a fourth nav item without
  altering any existing page's DOM contract that `static/js/*.js` or the Python UI tests already
  key on.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Add `GET /leads`/`POST /leads`/`PATCH /leads/{id}`/`DELETE /leads/{id}`/`POST /leads/{id}/convert` wrappers to `api.js` | Mirrors the existing `request`/`jsonRequest` helpers used for Account/Contact/Opportunity | small |
| Build `static/leads.html` | List container, new/edit form, matches the standalone Contacts page structure | small |
| Build `static/js/leads.js` | Fetch/render/CRUD/convert wiring, mirrors `contacts.js` | medium |
| Add a fourth "Leads" nav item to all five pages' sidebar | Purely additive `<a class="nav-item">`; no existing nav item's href/text changes | small |
| Extend `board.css` with `#leads-page`/`#leads-list`/`#lead-form` rules | Reuses the existing generic list-row/form/button rules by adding these selectors to the existing shared groups | small |

## Acceptance Criteria

- [x] `leads.html` lists every Lead with name/company/status/rating (BEH-1)
- [x] Create/edit/delete forms work against the Lead CRUD endpoints (BEH-2, BEH-3, BEH-4)
- [x] Convert action calls the convert endpoint and navigates to the resulting record (BEH-5)
- [x] A converted Lead's row hides its mutation actions (BEH-6)
- [x] All five pages render a four-item nav with exactly one active (BEH-7)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
