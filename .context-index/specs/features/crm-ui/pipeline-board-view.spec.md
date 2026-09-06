---
partial_schema: implement@1
charter: crm-ui
status: implemented
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-06
kind: behavioral
source-manifest:
  sha: "7d18227"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/api.js
    - static/js/api.test.mjs
    - static/js/board-state.js
    - static/js/board-state.test.mjs
    - static/js/board.js
    - static/js/error-state.js
    - static/js/error-state.test.mjs
    - static/js/errors.js
    - static/js/errors.test.mjs
    - static/js/stages.js
    - static/js/stages.test.mjs
    - tests/test_ui_board_page.py
  computed-at: "2026-09-06T22:37:16.363Z"
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
  - .context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md
drift_detected: true
---

# Live Spec: Pipeline board view, account switcher

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Behavioral Contract

### Preconditions

- `crm-api`'s `account-and-contact-management` and `opportunity-lifecycle` specs are
  implemented and reachable — crm-ui is served by that same process, so its API calls are
  same-origin relative requests (`/accounts`, `/opportunities`), no base URL configuration
  needed.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the board page loads, **then** it fetches `GET /accounts` to populate the
  account switcher, defaults to "all accounts" (tracked client-side only, or the last one the
  viewer selected), and fetches `GET /opportunities` (optionally with `?account_id=<selected>`)
  to render the board.
- **BEH-2** — **When** Opportunities are fetched, **then** the board renders the ten fixed stage
  columns in the API's fixed order, with each Opportunity's card placed in the column matching
  its `stage_name`, showing `name`, the owning Account's `name`, `amount`, and `close_date`.
- **BEH-3** — **When** the viewer picks a specific Account from the switcher, **then** the board
  re-fetches Opportunities filtered to that Account and fully replaces what is shown — it never
  merges a stale set with a new one on screen at once. Picking "all accounts" clears the filter.
- **BEH-4** — **When** the viewer drags an Opportunity card to a different stage column (or
  uses an equivalent explicit control), **then** the UI calls `PATCH /opportunities/{id}` with
  the new `stage_name` and moves the card only after the API call succeeds — a failed call
  leaves the card in its original column.
- **BEH-5** — **When** any API request in this spec fails (network error or non-2xx response),
  **then** the UI shows a visible message naming what failed — it never fails silently or shows
  a blank screen.
- **BEH-6** — **When** `GET /opportunities` (filtered or unfiltered) returns zero Opportunities,
  **then** the board shows all ten columns empty, not an error and not a blank screen.

### Postconditions

- The board's visible state always matches the currently selected account filter — there is no
  stale render left over from a previous selection after a switch completes.
- A card only ever moves columns after its `PATCH /opportunities/{id}` call succeeds; on failure
  the card returns to (or remains in) its pre-drag column.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any API request fails (network error or 5xx) | Visible error message naming the failed action | `UI_FETCH_FAILED` |
| Stage-move `PATCH` fails (network error or non-2xx) | Card reverts to its original column; visible error message | `UI_STAGE_MOVE_FAILED` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec is itself an API consumer, subject to the exact same rule as any other track: every
  read/write goes through `crm-api`'s documented endpoints, never a direct database call.
- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint." — Applies
  because every request this spec makes stays on the same local origin.
- **Principle:** "No inbound dependencies." — Applies because crm-ui depends on crm-api, never
  the reverse; this spec introduces no new dependency direction.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Static board page shell | HTML/CSS layout: ten stage columns, account switcher | medium |
| Fetch and render | JS to call `GET /accounts`/`GET /opportunities` and render cards into columns | medium |
| Account switcher wiring | Selecting an Account (or "all") re-fetches and fully replaces the board | small |
| Drag-and-drop stage move | Drag handling + `PATCH /opportunities/{id}` call + revert-on-failure | medium |
| Empty-state handling | Render all-empty columns when there are zero matching Opportunities | small |

## Acceptance Criteria

- [x] Board load fetches Accounts, defaults a filter, fetches and renders Opportunities (BEH-1)
- [x] Opportunities render into the correct one of ten fixed columns with the right card fields (BEH-2)
- [x] Switching the account filter fully replaces the board, never merges two sets (BEH-3)
- [x] Dragging a card to a new column calls PATCH and only moves on success (BEH-4)
- [x] Any API failure shows a visible message, never a silent failure or blank screen (BEH-5)
- [x] Zero matching Opportunities shows all columns empty, not an error (BEH-6)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
