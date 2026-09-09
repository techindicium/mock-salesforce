---
partial_schema: spec@1
charter: crm-ui
status: validated
kind: behavioral
milestone: v2
revision: 1
charter-revision: 16
created: 2026-09-09
updated: 2026-09-09
source-manifest:
  sha: "pending"
  files:
    - static/js/help-content.js
    - static/js/help-content.test.mjs
    - static/js/help.js
    - static/css/board.css
    - static/index.html
    - static/deal.html
    - static/accounts.html
    - static/contacts.html
    - static/leads.html
    - tests/test_ui_board_page.py
    - tests/test_ui_accounts_page.py
    - tests/test_ui_contacts_page.py
    - tests/test_ui_deal_page.py
    - tests/test_ui_leads_page.py
    - tests/test_css_component_coverage.py
  computed-at: "2026-09-09T00:00:00.000Z"
depends-on:
  - .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md
  - .context-index/specs/features/crm-ui/leads-view.spec.md
drift_detected: true
---

# Live Spec: In-app contextual help

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Behavioral Contract

### Preconditions

- The persistent global header (added by the visual-design-system refactor) renders on all five
  pages: `index.html`, `deal.html`, `accounts.html`, `contacts.html`, `leads.html`.
- Each page's primary content lives in a `<main>` element with a fixed, unique id already used
  elsewhere in the codebase as a styling/selector hook: `board`, `deal-detail`, `accounts-page`,
  `contacts-page`, `leads-page`.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** any of the five pages loads, **then** a "?" help button renders in the
  global header's utility area (next to the avatar), with `aria-haspopup="true"` and
  `aria-expanded="false"`.
- **BEH-2** — **When** the help button is clicked while the panel is closed, **then** the panel
  becomes visible, the button's `aria-expanded` becomes `"true"`, and focus is not stolen from
  the button (so a keyboard user can immediately toggle it closed again).
- **BEH-3** — **When** the help button is clicked while the panel is open, **or** the `Escape`
  key is pressed while it is open, **or** a click lands outside both the panel and the button
  while it is open, **then** the panel closes and `aria-expanded` returns to `"false"`.
- **BEH-4** — **When** the panel opens, **then** it shows content for the *current* page, keyed
  off that page's `<main>` id against a single central content map (`help-content.js`) — never
  per-page-duplicated text — so every page's help content has exactly one place to update.
- **BEH-5** — **When** the panel opens on a page whose `<main>` id has no entry in the content
  map (a defensive case, not expected to occur for any of the five shipped pages), **then** it
  falls back to a generic "Use the nav above to get around SalesStrength" message rather than
  rendering blank or throwing.
- **BEH-6** — **When** the panel is open, **then** it always additionally shows a fixed
  "Navigating SalesStrength" section listing all four nav sections (Opportunities, Accounts,
  Contacts, Leads) with a one-line description each, regardless of which page-specific content is
  showing above it.

### Postconditions

- The help panel's open/closed state is not persisted anywhere (no localStorage, no server
  round-trip) — every fresh page load starts with the panel closed, matching Salesforce's own
  header help menu.
- Opening/closing the panel never triggers a network request and never mutates any Account/
  Contact/Opportunity/Lead data — this capability is entirely static and client-side.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Current page's `<main>` id is not in the content map | Generic fallback message renders instead of blank content or a thrown error (BEH-5) | n/a (presentation-only; no runtime error code) |

## System Constitution Reference

- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint." — Applies
  directly: this capability's content is a static, bundled JS object; nothing here ever performs
  a `fetch()`.
- **Principle:** "Internal refactors that don't change the HTTP surface" (Autonomous / Agent May
  Decide) — Applies: no new `crm-api` endpoint, no persisted entity, purely additive markup/CSS/JS
  on top of the existing global header.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| `static/js/help-content.js` | Pure module: a `HELP_CONTENT` map keyed by `<main>` id, a fixed `NAV_OVERVIEW` array, and a pure `getPageHelp(mainId)` function with the BEH-5 fallback — the single source of truth the reviewer's own recommendation asked for | small |
| `static/js/help-content.test.mjs` | `node --test` coverage for `getPageHelp` (known id, unknown id, and the fallback shape) | small |
| `static/js/help.js` | DOM wiring only: toggle open/closed, `Escape`/outside-click handling, calls `getPageHelp(document.querySelector('main').id)` and renders it plus `NAV_OVERVIEW` into the panel | medium |
| Add the "?" button + panel markup to all five pages' global header | Purely additive; no existing element/id/class renamed | small |
| `board.css` rules for `.help-btn`/`.help-panel` and its children | New selectors only; reuses existing tokens | small |

## Acceptance Criteria

- [x] A "?" help button renders in the header on all five pages (BEH-1)
- [x] Clicking it opens the panel; clicking again, `Escape`, or an outside click closes it (BEH-2, BEH-3)
- [x] Panel content is page-specific, sourced from one central map (BEH-4)
- [x] An unmapped page id falls back to a generic message rather than breaking (BEH-5)
- [x] The nav overview section always renders regardless of page (BEH-6)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
