---
partial_schema: spec@1
charter: crm-ui
status: validated
kind: behavioral
milestone: v2
revision: 1
charter-revision: 17
created: 2026-09-09
updated: 2026-09-09
source-manifest:
  sha: "pending"
  files:
    - static/help.html
    - static/js/faq-content.js
    - static/js/faq-content.test.mjs
    - static/js/help-center.js
    - static/js/help-content.js
    - static/css/board.css
    - static/index.html
    - static/deal.html
    - static/accounts.html
    - static/contacts.html
    - static/leads.html
    - tests/test_ui_help_panel.py
    - tests/test_ui_help_center_page.py
    - tests/test_css_component_coverage.py
  computed-at: "2026-09-09T00:00:00.000Z"
depends-on:
  - .context-index/specs/features/crm-ui/in-app-help.spec.md
drift_detected: true
---

# Live Spec: Help Center FAQ page

<!-- Live Spec within the crm-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Behavioral Contract

### Preconditions

- The header help panel from `in-app-help.spec.md` exists on all pages and is the entry point
  into this page (a "Visit the Help Center" link inside it).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `help.html` loads, **then** it renders every FAQ category
  (General, Opportunities, Accounts, Contacts, Leads) as a labeled group, and every question
  within a category as a collapsed `<details>`/`<summary>` entry (closed by default) whose answer
  text is revealed on click — matching the disclosure pattern already used elsewhere in this app
  (e.g. the Accounts page's per-account Contacts list).
- **BEH-2** — **When** text is typed into the search box, **then** only FAQ entries whose
  question or answer text case-insensitively contains that text remain visible; categories with
  zero matching entries are hidden entirely (not shown as an empty heading).
- **BEH-3** — **When** the search box is cleared, **then** every category and every entry
  reappears, matching the unfiltered BEH-1 state.
- **BEH-4** — **When** no entry matches the current search text, **then** a visible
  "No matching help topics." message renders in place of the (now-empty) category list.
- **BEH-5** — **When** the header help panel (from `in-app-help.spec.md`) is opened on any page,
  **then** it includes a "Visit the Help Center" link to `help.html`, in addition to its existing
  page-specific content and nav overview.
- **BEH-6** — **When** `help.html` itself is opened, **then** its own header help panel's
  page-specific content (keyed by this page's `<main id="help-center-page">`) explains that the
  user is already in the Help Center, rather than falling back to the generic message.

### Postconditions

- Filtering the FAQ is a pure client-side text match against a static, bundled content module
  (`faq-content.js`) — no network request, no persisted state, and the underlying content array
  is never mutated by filtering (each keystroke re-filters from the full set, not the
  previously-filtered subset — so backspacing always correctly reveals previously-hidden entries).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Search text matches no FAQ entry | "No matching help topics." message renders (BEH-4) | n/a (presentation-only; no runtime error code) |

## System Constitution Reference

- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint." — Applies
  directly: FAQ content is a static, bundled JS array; search is a pure in-memory filter.
- **Principle:** "Internal refactors that don't change the HTTP surface" (Autonomous / Agent May
  Decide) — Applies: no new `crm-api` endpoint, no persisted entity, one new static page plus
  purely-additive markup (the header panel's new link) on the existing five pages.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| `static/js/faq-content.js` | `FAQ_CATEGORIES` (category name → array of `{question, answer}`) and a pure `filterFaqs(categories, query)` function implementing BEH-2/BEH-3 | small |
| `static/js/faq-content.test.mjs` | `node --test` coverage: empty query returns everything unchanged, a matching query narrows correctly, an all-miss query returns empty categories, matching is case-insensitive and checks both question and answer text | small |
| `static/help.html` | New page: same app shell (header incl. help panel, persistent sidebar nav, no item marked active), a search input, and an FAQ container | small |
| `static/js/help-center.js` | Renders `FAQ_CATEGORIES` as `<details>`/`<summary>` groups; wires the search input to `filterFaqs` and re-renders on every keystroke; shows the BEH-4 empty state | medium |
| Add a "Visit the Help Center" link inside the shared `#help-panel` markup on all six pages | Purely additive; static `<a href="help.html">` | small |
| Add a `help-center-page` entry to `help-content.js`'s `HELP_CONTENT` map | Satisfies BEH-6 | small |
| `board.css`: add `#help-center-page` to the shared page-container rule, style `.help-center-link`/`#faq-search`/`.faq-empty-state` | Reuses existing `details`/`summary`/`input` rules for the FAQ entries themselves — no new per-entry selectors needed | small |

## Acceptance Criteria

- [x] `help.html` renders every category and every question as a closed disclosure (BEH-1)
- [x] Typing in the search box narrows to matching entries and hides empty categories (BEH-2)
- [x] Clearing the search box restores the full unfiltered view (BEH-3)
- [x] A no-match search shows an explicit empty-state message (BEH-4)
- [x] The header help panel links to the Help Center on every page (BEH-5)
- [x] The Help Center page's own header help panel shows page-aware content, not the fallback (BEH-6)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
