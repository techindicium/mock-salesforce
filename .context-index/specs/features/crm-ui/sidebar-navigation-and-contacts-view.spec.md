---
partial_schema: spec@1
charter: crm-ui
status: implemented
kind: behavioral
charter-extension: true
milestone: mvp
revision: 1
charter-revision: 12
created: 2026-09-07
updated: 2026-09-07
source-manifest:
  sha: "9ebbbdf"
  files:
    - static/accounts.html
    - static/contacts.html
    - static/css/board.css
    - static/deal.html
    - static/index.html
    - static/js/api.js
    - static/js/api.test.mjs
    - static/js/contacts.js
    - tests/test_css_component_coverage.py
    - tests/test_ui_accounts_page.py
    - tests/test_ui_board_page.py
    - tests/test_ui_contacts_page.py
    - tests/test_ui_deal_page.py
  computed-at: "2026-09-07T15:29:44.381Z"
---

# Live Spec: Sidebar navigation and standalone Contacts view

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md

     charter-extension: true — the charter's Capability Map lists an "Account switcher"
     (a dropdown filter on the board page) but not a persistent cross-page sidebar nor a
     standalone all-accounts Contacts list view. Both are natural extensions of the
     charter's stated Business Intent ("full CRUD forms for Accounts, Contacts, and
     Opportunities... so the mock reads and feels like a real CRM") and stay inside its
     Scope boundaries (no new backend behavior — GET /contacts already supports an
     unfiltered "all contacts" call with `account_id` omitted). This spec adds two rows
     to the Capability Map on review pass rather than requiring a fresh /adev:brainstorm
     charter negotiation. -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `account-and-contact-management` spec is implemented and reachable —
  `GET /contacts` (already implemented, no backend change) supports an unfiltered call
  (no `account_id` query parameter) returning every Contact across every Account.
- The `visual-design-system` spec is implemented — the sidebar's visual treatment reuses
  its `:root` tokens and mock-jira-derived component patterns.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** any of the four pages (`index.html`, `deal.html`, `accounts.html`,
  the new `contacts.html`) loads, **then** it renders a persistent sidebar with exactly
  three navigation items — "Opportunities" (links to `index.html`), "Accounts" (links to
  `accounts.html`), "Contacts" (links to `contacts.html`) — and the item matching the
  current page is visually marked as active (`aria-current="page"` and a distinct style).
- **BEH-2** — **When** the viewer clicks a sidebar navigation item, **then** the browser
  navigates to that item's page (a normal link, not a client-side route change) — page
  state (any open form, unsaved input) is not preserved across the navigation, matching
  this app's existing multi-page-navigation behavior on `accounts.html` → `deal.html`.
- **BEH-3** — **When** `contacts.html` loads, **then** it fetches `GET /contacts` (no
  `account_id` filter) and `GET /accounts`, and renders every Contact in a list showing
  the contact's name, email, title, and its owning Account's name (resolved via
  `account_id`), sorted in the order the API returns them.
- **BEH-4** — **When** the viewer creates, edits, or deletes a Contact from
  `contacts.html`, **then** the UI calls the matching `crm-api` Contact endpoint
  (`POST /contacts`, `PATCH /contacts/{id}`, `DELETE /contacts/{id}`) and the visible list
  reflects the change immediately on success — a failed call leaves the list unchanged
  and shows a visible error naming what failed.
- **BEH-5** — **When** creating a Contact from `contacts.html`, **then** the create form
  requires selecting an owning Account from a populated dropdown (sourced from
  `GET /accounts`) — a Contact cannot be created without a valid `account_id`, matching
  the API's own constraint.
- **BEH-6** — **When** `GET /contacts` (unfiltered) returns zero Contacts, **then**
  `contacts.html` shows an explicit empty-state message, not a blank screen or an error.
- **BEH-7** — **When** any API request on `contacts.html` fails (network error or
  non-2xx response), **then** the UI shows a visible message naming what failed — it
  never fails silently or shows a blank screen.

### Postconditions

- The sidebar's active-item indicator always matches the page currently loaded — there is
  no page on which zero or more than one nav item reads as active.
- `contacts.html`'s visible list always reflects the latest successful mutation — a
  Contact created, edited, or deleted through this page is immediately visible (or
  absent) on that same page without a manual reload, and is also visible (or absent) on
  a subsequent visit to `accounts.html`'s per-account contacts disclosure or `deal.html`'s
  contacts section for the same Account, since all three read from the same
  `GET /contacts`-backed source of truth with no client-side cache.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any `contacts.html` API request fails (network error or 5xx) | Visible error message naming the failed action | `UI_FETCH_FAILED` |
| Create-contact submitted with no Account selected | Client-side validation blocks submission before any HTTP request (the `<select>` is `required`) | n/a (browser-native validation) |
| API returns `404` (unknown Contact `id` on edit/delete) | Visible error message using the API's message verbatim | `UI_FETCH_FAILED` |
| API returns `422` (validation error, e.g. missing required field) | Visible inline error message using the API's message verbatim | `UI_FETCH_FAILED` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because `contacts.html`
  is itself an API consumer, subject to the same rule as every other view in this module:
  every read/write goes through `crm-api`'s documented endpoints, never a direct database
  call. `GET /contacts` unfiltered is an existing, documented endpoint capability — no new
  backend behavior is introduced.
- **Principle:** "Fixture-backed, offline only." — Applies because every request stays on
  the same local origin as the rest of `crm-ui`.
- **Principle:** "Internal refactors that don't change the HTTP surface" (Autonomous /
  Agent May Decide, from this repo's constitution's Architecture Boundaries) — Applies:
  this spec adds a new client-side view and a navigational element, zero backend/HTTP
  surface change.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Sidebar markup + CSS | Add `.app-shell`/`.sidebar`/`.nav-item` structure (ported from mock-jira) to all four pages, wrapping existing page content in `.app-main` | medium |
| Wire sidebar into index.html/deal.html/accounts.html | Add the sidebar to the three existing pages without altering their existing IDs/classes/behavior | small |
| `contacts.html` page + `contacts.js` | New page: fetch/render all contacts with owning-account name, create/edit/delete forms | large |
| Contacts empty-state and error handling | Empty-state message, error banner wiring matching the established `error-state.js`/`errors.js` pattern | small |

## Acceptance Criteria

- [ ] Sidebar renders on all four pages with exactly 3 nav items, current page marked active (BEH-1)
- [ ] Clicking a nav item navigates via a real link, no state preserved (BEH-2)
- [ ] `contacts.html` fetches and renders all contacts with owning-account name (BEH-3)
- [ ] Create/edit/delete on `contacts.html` calls the matching endpoint and updates the list on success, leaves it unchanged on failure (BEH-4)
- [ ] Contact creation requires a valid Account selection (BEH-5)
- [ ] Zero contacts shows an explicit empty state, not a blank screen (BEH-6)
- [ ] Any API failure on `contacts.html` shows a visible error message (BEH-7)
- [ ] No existing `id`/`class`/`name` used by `board.js`/`deal.js`/`accounts.js` or the Python UI tests is renamed, removed, or repurposed
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
