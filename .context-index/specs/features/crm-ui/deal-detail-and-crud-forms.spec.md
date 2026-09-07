---
partial_schema: implement@1
charter: crm-ui
status: implemented
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-07
kind: behavioral
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
  - .context-index/specs/features/crm-ui/pipeline-board-view.spec.md
source-manifest:
  sha: "6a4c2f4"
  files:
    - static/accounts.html
    - static/deal.html
    - static/index.html
    - static/js/accounts.js
    - static/js/api.js
    - static/js/api.test.mjs
    - static/js/board.js
    - static/js/deal.js
    - static/js/form-errors.js
    - static/js/form-errors.test.mjs
    - static/js/list-state.js
    - static/js/list-state.test.mjs
    - tests/test_ui_accounts_page.py
    - tests/test_ui_board_page.py
    - tests/test_ui_deal_page.py
  computed-at: "2026-09-07T00:32:49.365Z"
---

# Live Spec: Deal detail page and CRUD forms

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Behavioral Contract

### Preconditions

- The `pipeline-board-view` spec's board and account switcher exist — the deal detail page is
  reached by opening an Opportunity card from the board.
- `crm-api`'s full CRUD surface for Account, Contact, and Opportunity is implemented and
  reachable.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the viewer opens an Opportunity card, **then** the UI fetches
  `GET /opportunities/{id}` and `GET /accounts/{account_id}` and renders a deal detail page
  showing every Opportunity field, the related Account's summary (name, industry, phone), and
  edit/delete actions.
- **BEH-2** — **When** the deal detail page renders, **then** it also fetches
  `GET /contacts?account_id=<the Opportunity's account_id>` and shows the related Account's
  Contacts as a read-only list (name, title, email) — the deal detail page never edits a Contact
  directly; that happens through the Contact CRUD form (BEH-6).
- **BEH-3** — **When** the viewer submits the edit-opportunity form with one or more changed
  fields, **then** the UI calls `PATCH /opportunities/{id}` and re-renders the page with the
  updated representation on success.
- **BEH-4** — **When** the viewer confirms delete-opportunity, **then** the UI calls
  `DELETE /opportunities/{id}` and navigates back to the pipeline board on success.
- **BEH-5** — **When** the viewer submits the create-opportunity form (from the board or an
  Account's page) with a non-empty `name`, a valid `account_id`, and a `close_date`, **then** the
  UI calls `POST /opportunities` and navigates to the new deal's detail page on success.
- **BEH-6** — **When** the viewer submits a create/edit/delete Contact form (reached from the
  deal detail page's related-Contacts list, or an Account's page), **then** the UI calls the
  matching `crm-api` Contact endpoint (`POST`/`PATCH`/`DELETE /contacts`) and refreshes the
  related-Contacts list on success.
- **BEH-7** — **When** the viewer submits a create/edit/delete Account form, **then** the UI
  calls the matching `crm-api` Account endpoint (`POST`/`PATCH`/`DELETE /accounts`) and, for
  delete, is shown the API's `409`/`ACCOUNT_HAS_DEPENDENTS` message inline rather than a generic
  failure when the Account still has Contacts or Opportunities.
- **BEH-8** — **When** any API request in this spec fails (network error or non-2xx response),
  **then** the UI shows a visible message naming what failed — it never fails silently or shows
  a blank screen.

### Postconditions

- The deal detail page's visible state always reflects the Opportunity's and its Account's
  current server-side representation after any successful edit — no stale field is shown once a
  `PATCH`/`GET` round trip completes.
- A deleted Opportunity or Contact no longer appears in any subsequent list or detail view.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any API request fails (network error or 5xx) | Visible error message naming the failed action | `UI_FETCH_FAILED` |
| Edit/create form submits invalid data (API returns 422) | Form shows the error inline naming the field; input is not cleared | `UI_VALIDATION_ERROR` |
| Delete-account attempted while Contacts/Opportunities still exist (API returns 409) | Inline message naming the dependent count; Account is not removed from the UI | `UI_ACCOUNT_HAS_DEPENDENTS` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  every read/write in this spec goes through `crm-api`'s documented endpoints, never a direct
  database call.
- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint." — Applies
  because every request this spec makes stays on the same local origin.
- **Principle:** "No inbound dependencies." — Applies because crm-ui depends on crm-api, never
  the reverse; this spec introduces no new dependency direction.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Deal detail page shell | HTML/CSS layout: Opportunity fields, Account summary panel, related-Contacts list | medium |
| Fetch and render detail | JS to call `GET /opportunities/{id}`, `GET /accounts/{id}`, `GET /contacts?account_id=` | medium |
| Edit/delete opportunity forms | Form + `PATCH`/`DELETE /opportunities/{id}` calls + inline error handling | medium |
| Create opportunity form | Form + `POST /opportunities` call + navigate-on-success | small |
| Account and Contact CRUD forms | Forms + matching Account/Contact endpoint calls, including the 409-dependents case | medium |

## Acceptance Criteria

- [x] Opening a card renders the deal detail page with Opportunity + Account summary (BEH-1)
- [x] Deal detail page shows the related Account's Contacts as a read-only list (BEH-2)
- [x] Edit-opportunity form calls PATCH and re-renders with updated data (BEH-3)
- [x] Delete-opportunity calls DELETE and navigates back to the board (BEH-4)
- [x] Create-opportunity form calls POST and navigates to the new detail page (BEH-5)
- [x] Contact CRUD forms call the matching endpoint and refresh the related list (BEH-6)
- [x] Account CRUD forms call the matching endpoint, surfacing 409/ACCOUNT_HAS_DEPENDENTS inline (BEH-7)
- [x] Any API failure shows a visible message, never a silent failure or blank screen (BEH-8)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
