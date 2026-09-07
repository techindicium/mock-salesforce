---
partial_schema: spec@1
charter: crm-ui
status: review-passed
mode: refactor
kind: refactor
milestone: mvp
revision: 1
charter-revision: 12
created: 2026-09-07
updated: 2026-09-07
---

# Refactoring Spec: Port mock-jira's visual design system to crm-ui

<!-- Refactoring spec within the crm-ui charter.
     Extends the Live Spec format with current-state/target-state analysis and migration path.
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Current State

### Structure

| File | Role | Lines | Notes |
|------|------|-------|-------|
| `static/css/board.css` | Single global stylesheet for all three pages | 9 | Only defines rules for the board page's own elements (`header`, `#error-banner`, `#board`, `.stage-column`, `.cards`, `.opportunity-card`); no CSS custom properties, colors hardcoded inline |
| `static/index.html` | Pipeline board page markup | 44 | Loads `css/board.css`; account switcher, create-opportunity form, board columns |
| `static/deal.html` | Deal detail page markup | 58 | Loads `css/board.css` but none of its own elements (`dl`, edit/contact forms, buttons) have any matching rule |
| `static/accounts.html` | Accounts list page markup | 57 | Loads `css/board.css` but none of its own elements (account list items, three forms, buttons) have any matching rule |

### Problems

1. `board.css` styles only the board page. `deal.html` and `accounts.html` link the same stylesheet but render in unstyled browser defaults for everything except the shared `#error-banner` rule — no visual consistency across the three pages that make up this module.
2. No design tokens (CSS custom properties) exist anywhere — colors are hardcoded hex literals (`#f4f5f7`, `#ddd`, `#fdecea`, `#611a15`), so there is no single source of truth to reuse across the currently-unstyled forms and buttons.
3. Every `<button>`, text `<input>`, `<select>`, and `.form-error` element across all three pages renders with plain user-agent defaults — no consistent button, form-field, or inline-error styling exists.
4. mock-salesforce shares an adev-course workspace with the sibling `mock-jira` app, which has an established, deliberate visual identity (a "dispatch ledger" theme: dark ink/rail background, warm paper-stock surfaces, brick-red/brass-gold/pine-green accent colors, monospace accents on keys/meta text, hairline borders, flat 2px hard-edged offset shadows). mock-salesforce currently looks like an unstyled prototype with no relation to it, despite both being mock CRM/tracker apps meant to read as tools in the same family.

### Dependencies

- `src/mock_salesforce/static.py` serves `static/` as plain files via `FileResponse` with no build step or bundler — CSS/HTML changes take effect as-is, no compilation.
- All three pages link exactly one stylesheet each (`css/board.css`); there is no per-page stylesheet.
- `static/js/board.js`, `static/js/deal.js`, and `static/js/accounts.js` toggle visibility exclusively via the `hidden` DOM property/attribute (never via a CSS class), and set `className` only to fixed, static values used purely as styling hooks (e.g. `opportunity-card`, `edit-account-btn`) — never toggled at runtime for behavior. No JS logic reads computed style, class list membership, or any CSS-driven state. This means the stylesheet can be replaced or extended freely without touching JS, provided every existing `id`/`class` selector the JS assigns keeps a matching visual rule and the `[hidden]` rule remains unconditionally `display: none`.
- The 46 passing frontend JS unit tests (`static/js/*.test.mjs`) exercise only pure logic modules (`api.js`, `board-state.js`, `error-state.js`, `errors.js`, `form-errors.js`, `list-state.js`, `stages.js`) and never assert on computed CSS — a pure restyle cannot affect them by construction.
- `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`, `tests/test_ui_accounts_page.py` assert on served HTML content (element presence, IDs, form fields) — not on CSS — so a pure restyle cannot affect them by construction, provided no element `id`, `name`, or existing `class` value used as a JS/test selector is renamed or removed.

## Target State

### Structure

| File | Role | Notes |
|------|------|-------|
| `static/css/board.css` | Single global stylesheet, restyled | Adds a `:root` token block (palette + derived shades) ported from mock-jira's `static/css/board.css`, plus rules covering every element already present in all three pages: header/nav links, buttons, text inputs/selects, `.form-error`, the account/deal/opportunity list items and their per-item action buttons, the three `<details>`-nested account forms, and the existing board/column/card rules restyled to the new palette |
| `static/index.html`, `static/deal.html`, `static/accounts.html` | Page markup, unchanged structurally | No element is added, removed, or renamed; at most a purely-presentational `class` attribute may be added to an element that currently has none, solely as a new CSS styling hook — never replacing or altering an `id` or existing `class` any JS file or Python test already selects on |

### Improvements

1. A shared `:root` token block (named CSS custom properties for the palette, ported verbatim in spirit from mock-jira's `board.css`) becomes the single source of truth for color, replacing every hardcoded hex literal — addresses Problem 2.
2. Every element type present on `deal.html` and `accounts.html` (`dl`/`dt`/`dd`, list items and their action buttons, the three additional forms) gets a matching rule in `board.css`, bringing all three pages to the same level of visual finish — addresses Problem 1.
3. `button`, text `input`/`select`, and `.form-error` get consistent, deliberate styling applied globally (not per-page), matching mock-jira's flat/bordered/hard-shadow button and form-field treatment — addresses Problem 3.
4. The board's columns and cards, the account/deal list rows, and the error banner adopt mock-jira's ink/rail/paper palette, monospace meta accents, hairline borders, and flat offset shadows — addresses Problem 4 by giving mock-salesforce a visual identity that reads as a sibling of mock-jira rather than an unrelated unstyled prototype.

## Changes Catalog

### ADDED

- `:root` CSS custom properties in `board.css` (palette tokens + derived shades) — establishes the single source of truth mock-jira already has.
- New CSS rules in `board.css` for every currently-unstyled `deal.html`/`accounts.html` element (definition lists, list items and their action buttons, the three additional forms, `<details>`/`<summary>`) — these elements exist today but have no rule.
- `[hidden] { display: none !important; }` — guards every form's existing `hidden`-attribute show/hide against being overridden by a more specific new display rule (mock-jira's stylesheet carries the same guard for the same reason).

### MODIFIED

- Existing selectors in `board.css` (`body`, `header`, `#error-banner`, `#board`, `.stage-column`, `.cards`, `.opportunity-card`) — colors and surface treatment repointed at the new `:root` tokens and mock-jira's component look; selector names and the elements they target are unchanged.
- `static/index.html`, `static/deal.html`, `static/accounts.html` — no structural change; a purely-presentational `class` attribute may be added to an element that currently carries none, strictly as a new styling hook.

### REMOVED

- The hardcoded inline hex literals currently in `board.css` (`#f4f5f7`, `#ddd`, `#fdecea`, `#611a15`, `#fff`) — replaced by `:root` token references, not by new inline literals.

### RENAMED

(none — no identifier, `id`, or existing `class` value is renamed)

## Migration Path

### Step 1: Port the design-token block

- **What:** Add a `:root` block to `static/css/board.css` defining the same named custom properties mock-jira's `static/css/board.css` defines (ink/rail/paper/stamp-red/stamp-gold/stamp-green/ink-line plus derived shades), and add the `[hidden] { display: none !important; }` guard and `* { box-sizing: border-box; }` reset alongside it.
- **Why first:** Every later step consumes these tokens; adding them first with zero other changes keeps the diff reviewable and verifiable in isolation.
- **Risk:** None — additive only, no existing selector is touched yet.
- **Verification:** `python3 -m pytest -q` and `node --test static/js/*.test.mjs` both still pass (both suites are blind to a pure CSS addition).

### Step 2: Restyle the existing board-page rules

- **What:** Repoint `body`, `header`, `#error-banner`, `#board`, `.stage-column`, `.cards`, `.opportunity-card` at the new tokens and mock-jira's component treatment (paper-stock cards with a colored left border by data attribute is out of scope — this module has no priority field to key off of; port the surface/border/shadow/typography treatment instead).
- **Why next:** The board page is the module's primary view and already has full-coverage rules — restyling in place, one file, is the lowest-risk change that produces a visible result to check against mock-jira before extending coverage to the other two pages.
- **Risk:** Low — same selectors, same elements, only property values change.
- **Verification:** Same test suites as Step 1, plus a manual/headless-browser visual check of `index.html` against mock-jira's board page for consistency of palette and component treatment.

### Step 3: Add coverage for deal.html's elements

- **What:** Add rules for `#deal-detail`, `#opportunity-section`, `#account-summary`, `#contacts-section`, `dl`/`dt`/`dd`, `#contacts-list` and its `li`/action buttons, and the edit-opportunity and contact forms (labels, inputs, submit/cancel buttons, `.form-error`).
- **Why next:** Deal detail is the module's second-most-visited view (per the `crm-ui` charter) and currently has zero page-specific styling.
- **Risk:** Low — new rules only, no existing selector touched.
- **Verification:** Same test suites, plus a headless-browser DOM dump of `deal.html?id=<seeded id>` to confirm every element from Dependencies still renders and no `id`/`class` used by `static/js/deal.js` or `tests/test_ui_deal_page.py` was altered.

### Step 4: Add coverage for accounts.html's elements

- **What:** Add rules for `#accounts-page`, `#accounts-list` and its `li`/action buttons/`.account-delete-error`, the `<details>`/`<summary>` contacts disclosure and its nested list/button, and the three forms (`account-form`, `account-new-opportunity-form`, `account-contact-form`).
- **Why next:** Completes page-parity; ordered last because it has the most distinct form/list combinations to cover.
- **Risk:** Low — new rules only, no existing selector touched.
- **Verification:** Same test suites, plus a headless-browser DOM dump of `accounts.html` to confirm every element from Dependencies still renders and no `id`/`class` used by `static/js/accounts.js` or `tests/test_ui_accounts_page.py` was altered.

## Invariants

- [ ] All existing tests continue to pass at every step (111 backend `pytest`, 46 frontend `node --test`)
- [ ] Public API contracts do not change — this refactor touches no backend code
- [ ] No data loss or corruption during migration — no database or fixture file is touched
- [ ] No HTML element `id`, `name`, or `class` value already read by `static/js/*.js` or asserted on by `tests/test_ui_*.py` is renamed, removed, or repurposed
- [ ] Every element that is currently shown/hidden via the `hidden` DOM property continues to be fully hidden when `hidden` is set, at every migration step

## Behavioral Contract

<!-- retired-behavior-ids: (none) -->

### Behaviors

- **BEH-1** — **When** any of the three pages (`index.html`, `deal.html`, `accounts.html`) loads, **then** it renders using the shared `:root` design tokens ported from mock-jira's `static/css/board.css` — no page renders with a hardcoded color literal outside that token block.
- **BEH-2** — **When** a form is shown or hidden via its `hidden` DOM property (unchanged JS behavior from `board.js`/`deal.js`/`accounts.js`), **then** it is fully hidden (`display: none`) while `hidden` is set and fully visible in its restyled form when it is not, regardless of any other CSS rule added by this refactor.
- **BEH-3** — **When** any button, text input, select, or `.form-error` element renders on any of the three pages, **then** it renders with the shared component styling (consistent border, padding, typography, and — for `.form-error` — the shared error-color treatment) rather than a browser user-agent default.
- **BEH-4** — **When** the pipeline board renders its ten stage columns and opportunity cards, **then** they render with mock-jira's ported surface/border/shadow treatment while preserving the existing column order and per-card field content unchanged.
- **BEH-5** — **When** the JS test suite (`node --test static/js/*.test.mjs`) or the backend test suite (`python3 -m pytest -q`) is run after this refactor, **then** every test that passed before this refactor still passes, unmodified.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| A new CSS rule's specificity overrides the `hidden` attribute's `display: none` on a form | The `[hidden] { display: none !important; }` guard added in Step 1 keeps the element hidden regardless of any other rule's specificity | n/a (presentation-only; no runtime error code) |

## System Constitution Reference

- **Principle:** "Coupling the mock's internals to one specific consuming track's implementation" (Anti-Pattern to Avoid) — Not applicable/violated: this refactor changes only static presentation assets served to a browser, introduces no new dependency, and does not couple `crm-ui` to any consuming track's implementation.
- **Principle:** "No inbound dependencies." — This refactor reads mock-jira's `static/css/board.css` only as a one-time visual reference during authoring; the shipped `mock-salesforce` repo gains no runtime, build-time, or file dependency on `mock-jira` — the ported CSS is copied and adapted, not imported or linked.
- **Principle:** "Internal refactors that don't change the HTTP surface" (Autonomous / Agent May Decide) — Applies directly: this is a presentation-only refactor with zero HTTP surface or backend change, squarely inside the charter's autonomous scope.

## Acceptance Criteria

- [ ] All three pages render using the shared `:root` design tokens, no hardcoded color literals remain outside the token block (BEH-1)
- [ ] Every `hidden`-attribute form remains fully hidden/visible exactly as before at every migration step (BEH-2)
- [ ] Buttons, text inputs, selects, and `.form-error` elements render with consistent shared styling on all three pages (BEH-3)
- [ ] The board's columns and cards render with the ported surface/border/shadow treatment, column order and card content unchanged (BEH-4)
- [ ] All 111 backend tests and 46 frontend JS tests pass unmodified after the refactor (BEH-5)
- [ ] No element `id`, `name`, or existing `class` value used by JS or Python tests is renamed, removed, or repurposed
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
