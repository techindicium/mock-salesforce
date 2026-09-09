---
partial_schema: spec@1
charter: crm-ui
status: implemented
mode: refactor
kind: refactor
milestone: mvp
revision: 2
charter-revision: 12
created: 2026-09-07
updated: 2026-09-09
source-manifest:
  sha: "pending"
  files:
    - static/css/board.css
    - static/index.html
    - static/deal.html
    - static/accounts.html
    - static/contacts.html
    - static/favicon.svg
    - tests/test_css_component_coverage.py
    - tests/test_css_design_tokens.py
  computed-at: "2026-09-09T00:00:00.000Z"
drift_detected: true
---

# Refactoring Spec: Restyle crm-ui from the mock-jira ledger theme to a Salesforce-Lightning-inspired theme

<!-- Refactoring spec within the crm-ui charter.
     Revision 2 supersedes revision 1's target state (the mock-jira "dispatch ledger" theme).
     Parent Charter: .context-index/specs/features/crm-ui/charter.md -->

## Current State

### Structure

| File | Role | Notes |
|------|------|-------|
| `static/css/board.css` | Single global stylesheet for all four pages | Revision 1's target state: a dark ink/rail/paper "dispatch ledger" theme ported from sibling `mock-jira`, with hard 2px offset shadows and a left-hand dark sidebar |
| `static/index.html`, `static/deal.html`, `static/accounts.html`, `static/contacts.html` | Page markup | Each links `css/board.css`; each has a `<nav class="sidebar">` with three `<a class="nav-item">` links, no page-level branding beyond a plain `<title>` |

### Problems

1. mock-salesforce is meant to read as a realistic stand-in for a Salesforce-shaped CRM to anyone browsing it (crm-ui charter, "Business Intent"), but its visual identity intentionally matched sibling tool `mock-jira` instead of evoking Salesforce's own Lightning Experience look — dark ink/rail palette, hard offset shadows, no header/branding, a vertical nav rail. Someone opening it does not get the "this looks like a CRM in the Salesforce family" impression the charter calls for.
2. No branded chrome exists at all — no logo, no product name, no global header — so the app reads as an internal tool rather than a product.

### Dependencies

- Same dependency surface documented in revision 1 of this spec: `src/mock_salesforce/static.py` serves `static/` as plain files with no build step; JS (`board.js`/`deal.js`/`accounts.js`/`contacts.js`) toggles visibility only via the `hidden` DOM property and sets `className` only to fixed static values, never reading computed style; the JS unit tests and the Python `test_ui_*` tests assert on element `id`/`name`/existing `class` presence, never on CSS or added markup.
- `tests/test_ui_board_page.py`, `test_ui_deal_page.py`, `test_ui_accounts_page.py`, `test_ui_contacts_page.py` assert (a) `class="sidebar"` is present, (b) exactly 3 elements match `class="nav-item` (prefix match), and (c) exactly 1 matches `class="nav-item active"` — these counts constrain the nav to stay a 3-link structure with a `sidebar`/`nav-item`/`nav-item active` class contract, but do not constrain the nav's visual orientation (vertical rail vs. horizontal tab bar) since that is CSS-only.
- `tests/test_css_design_tokens.py` and `tests/test_css_component_coverage.py` (revision 1) asserted the mock-jira token names (`--ink`, `--rail`, `--paper`, `--stamp-red`, `--stamp-gold`, `--stamp-green`, `--ink-line`) and forbade the pre-mock-jira hardcoded literals. This revision retires those specific token-name assertions (the token *names* were never a contract for anything outside this spec's own theme) in favor of new SLDS-inspired token names, while preserving every structural/selector assertion in `test_css_component_coverage.py`.

## Target State

### Structure

| File | Role | Notes |
|------|------|-------|
| `static/css/board.css` | Single global stylesheet, restyled | New `:root` token block using an SLDS-inspired palette (`--brand: #0176d3` and derived shades, neutral surface/border/text tokens, status colors); `.sidebar`/`.nav-item` restyled from a dark vertical rail into a white horizontal tab bar (Lightning Experience's app-nav pattern) via `.app-shell { flex-direction: column }`, no DOM change; new rules for a global header (`.global-header`, `.brand`, `.brand-mark`, `.brand-name`, `.global-search`, `.header-utilities`, `.avatar`); Kanban-style stage columns/cards with a brand-colored top accent bar; brand-filled buttons on every `type="submit"` action and the three `#new-*-btn` primary actions, neutral bordered buttons elsewhere |
| `static/index.html`, `static/deal.html`, `static/accounts.html`, `static/contacts.html` | Page markup | Adds one new `<header class="global-header">` block (fake logo mark + "SalesStrength" wordmark, a disabled decorative search input, an avatar glyph) before the existing `<div class="app-shell">`, and a `<link rel="icon">` to the new favicon; `<title>` gains a "SalesStrength \| " prefix. No existing element, `id`, `name`, or `class` is renamed, removed, or repurposed — the `<nav class="sidebar">` with its three `<a class="nav-item">` links is untouched structurally |
| `static/favicon.svg` | New file | The fake "SalesStrength" cloud logomark (a hand-drawn cloud shape in the brand blue, evoking Salesforce's own cloud+wordmark logo lockup style without reusing Salesforce's name or mark), reused inline in every page's header and as the browser-tab favicon |

### Improvements

1. A `:root` token block with SLDS-derived names and values (brand blue `#0176d3`/`#014486`/`#1b96ff`, neutral surface/border/text grays, status red/gold/green) replaces the ledger palette — addresses Problem 1's color/surface mismatch.
2. A white global header with a fake logo, product name ("SalesStrength"), decorative search, and avatar, plus a horizontal Lightning-style tab bar (same `sidebar`/`nav-item` DOM, restyled via CSS only) replaces the dark vertical rail with no branding — addresses Problem 2 and the rest of Problem 1 (nav orientation, absence of chrome).
3. Buttons split into a brand-filled "primary action" treatment (submit buttons, the three `New …` actions) and a neutral bordered treatment (Edit/Delete/Cancel), matching SLDS's own primary/neutral button distinction, driven entirely by the `type="submit"` attribute and existing `id`s already on those buttons — no HTML changes required for this piece.
4. Stage columns and opportunity cards get a brand-colored top accent bar and a light Kanban-card surface treatment (white, subtle border, subtle shadow, small radius) in place of the ledger's paper-stock/hard-shadow cards — brings the board closer to Lightning Experience's Opportunity Kanban view.

## Changes Catalog

### ADDED

- `static/favicon.svg` — the fake brand's cloud logomark, used as both the inline header brand-mark and the browser favicon.
- `.global-header`, `.brand`, `.brand-mark`, `.brand-name`, `.global-search`, `.header-utilities`, `.avatar` rules in `board.css`, and the matching `<header class="global-header">` markup in all four pages — there was no branded chrome before this revision.
- `button[type="submit"]` / `#new-opportunity-btn` / `#new-account-btn` / `#new-contact-btn` brand-button rules — establishes the primary/neutral button distinction SLDS uses; no such distinction existed before.

### MODIFIED

- `:root` token block in `board.css` — token names and values replaced wholesale (ledger palette → SLDS-inspired palette); every existing consumer of a token (`body`, buttons, inputs, cards, list rows, forms, etc.) is repointed at the new names.
- `.app-shell`, `.sidebar`, `.nav-item`, `.nav-item:hover`, `.nav-item.active`, `.app-main` — same selectors, same elements; `.app-shell` becomes `flex-direction: column` and `.sidebar` becomes a horizontal flex row so the unchanged 3-link nav renders as a top tab bar instead of a left rail.
- `.stage-column`, `.opportunity-card`, `button`, `.form-error`, `#error-banner`, input/select rules, list-row rules (`#contacts-list li`/`#accounts-list li`/`#all-contacts-list li`), `#opportunity-section`/`#account-summary`/`#contacts-section`, `dl`/`dt`/`dd` — all repointed at new tokens and given SLDS-style surface/border/radius/shadow treatment in place of the ledger's paper-stock/hard-shadow look.
- `<title>` in all four pages — gains a `"SalesStrength | "` prefix.
- `tests/test_css_design_tokens.py` — asserts the new token names (`--brand`, `--brand-dark`, `--surface`, `--surface-alt`, `--border`, `--error`, `--success`) in place of the retired ledger-theme names.

### REMOVED

- The mock-jira-derived token names and their ledger-palette values (`--ink`, `--rail`, `--paper`, `--stamp-red`, `--stamp-gold`, `--stamp-green`, `--ink-line`, plus the derived `-light`/`-dim`/`-text-on-*` variants) — replaced by the new token set, not by new hardcoded literals.

### RENAMED

(none — no HTML element `id`, `name`, or existing `class` value is renamed)

## Migration Path

### Step 1: Replace the design-token block and repoint every existing rule

- **What:** Swap the `:root` block for the SLDS-inspired token set and repoint every rule already present in `board.css` (body, header, error banner, board/columns/cards, buttons, inputs, page containers, sections, lists, forms, details/summary, app-shell/sidebar/nav/app-main) at the new tokens and SLDS-style surface/border/radius/shadow values, without adding or removing any selector.
- **Why first:** Every later step (branding, nav re-orientation) builds visually on this; doing it as one pass keeps the diff a single, reviewable restyle.
- **Risk:** Low — same selectors, same elements, only property values and token names change.
- **Verification:** `python3 -m pytest -q` and `node --test static/js/*.test.mjs` both pass; `tests/test_css_design_tokens.py` and `tests/test_css_component_coverage.py` updated and passing.

### Step 2: Add the global header and favicon

- **What:** Add `<header class="global-header">` (brand mark + name, decorative search, avatar) and a `<link rel="icon">` to all four pages, plus `static/favicon.svg`.
- **Why next:** Purely additive markup with its own new CSS rules — safest to layer on once the token/repaint pass is verified.
- **Risk:** Low — new elements only; no existing `id`/`class`/`name` touched.
- **Verification:** Same test suites; manual/headless-browser check that the header renders on all four pages and the favicon loads.

### Step 3: Re-orient the nav from a vertical rail to a horizontal tab bar

- **What:** Change `.app-shell` to `flex-direction: column` and `.sidebar` to a horizontal flex row, so the existing unchanged `sidebar`/`nav-item` markup renders as a Lightning-style top tab bar.
- **Why last:** Purely a layout-direction change on already-restyled elements; ordering last isolates it as the smallest, most visually distinct diff to review on its own.
- **Risk:** Low — CSS-only; `class="sidebar"` and the `nav-item`/`nav-item active` counts the UI tests assert on are untouched.
- **Verification:** Same test suites, plus the `test_ui_*_page.py` sidebar/nav-item assertions (unchanged, still passing) and a manual/headless-browser visual check against Lightning Experience's app-nav pattern.

## Invariants

- [x] All existing tests continue to pass at every step (125 backend `pytest`, 48 frontend `node --test`)
- [x] Public API contracts do not change — this refactor touches no backend code
- [x] No data loss or corruption during migration — no database or fixture file is touched
- [x] No HTML element `id`, `name`, or `class` value already read by `static/js/*.js` or asserted on by `tests/test_ui_*.py` is renamed, removed, or repurposed
- [x] Every element that is currently shown/hidden via the `hidden` DOM property continues to be fully hidden when `hidden` is set

## Behavioral Contract

<!-- retired-behavior-ids: BEH-1 (redefined below, was scoped to the ledger-theme token names, not the concept of a shared token block) -->

### Behaviors

- **BEH-1** — **When** any of the four pages loads, **then** it renders using the shared SLDS-inspired `:root` design tokens — no page renders with a hardcoded color literal outside that token block.
- **BEH-2** — **When** a form is shown or hidden via its `hidden` DOM property (unchanged JS behavior), **then** it is fully hidden (`display: none`) while `hidden` is set and fully visible in its restyled form when it is not.
- **BEH-3** — **When** any button, text input, select, or `.form-error` element renders, **then** it renders with the shared component styling — `type="submit"` buttons and the three `New …` actions render brand-filled, all other buttons render neutral-bordered.
- **BEH-4** — **When** the pipeline board renders its ten stage columns and opportunity cards, **then** they render as light Kanban-style cards with a brand-colored top accent, preserving the existing column order and per-card field content unchanged.
- **BEH-5** — **When** any page renders, **then** the global header shows the fake "SalesStrength" brand mark and wordmark, and the persistent nav (still the same `sidebar`/`nav-item` DOM) renders as a horizontal tab bar rather than a vertical rail.
- **BEH-6** — **When** the JS test suite (`node --test static/js/*.test.mjs`) or the backend test suite (`python3 -m pytest -q`) is run after this refactor, **then** every test that passed before this refactor still passes (after the token-name assertions in `test_css_design_tokens.py` are updated to the new names).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| A new CSS rule's specificity overrides the `hidden` attribute's `display: none` on a form | The `[hidden] { display: none !important; }` guard (unchanged from revision 1) keeps the element hidden regardless of any other rule's specificity | n/a (presentation-only; no runtime error code) |

## System Constitution Reference

- **Principle:** "mirror Salesforce's own vocabulary (account, contact, opportunity, stage) so the mock reads as the thing it imitates" — This revision extends that intent from domain vocabulary to visual identity: the UI now also evokes Salesforce's actual Lightning Experience look, while the product name/logo shown in the UI ("SalesStrength" + an original cloud mark) is deliberately distinct from Salesforce's own name/trademark — the mock imitates the *category and visual language* of a Salesforce-shaped CRM, not Salesforce's brand identity itself.
- **Principle:** "No inbound dependencies." — This refactor reads Salesforce's publicly documented Lightning Design System color/typography/layout conventions only as a one-time visual reference during authoring; the shipped repo gains no runtime, build-time, or file dependency on Salesforce's actual SLDS CSS/assets or on `mock-jira`.
- **Principle:** "Internal refactors that don't change the HTTP surface" (Autonomous / Agent May Decide) — Applies directly: presentation-only refactor, zero HTTP surface or backend change.

## Acceptance Criteria

- [x] All four pages render using the shared SLDS-inspired `:root` design tokens, no hardcoded color literal outside the token block (BEH-1)
- [x] Every `hidden`-attribute form remains fully hidden/visible exactly as before (BEH-2)
- [x] Buttons split into brand-filled primary vs. neutral-bordered treatments (BEH-3)
- [x] The board's columns and cards render as light Kanban-style cards with a brand accent, column order and card content unchanged (BEH-4)
- [x] A global header with the fake "SalesStrength" logo/wordmark renders on every page, and the nav renders as a horizontal tab bar (BEH-5)
- [x] All 125 backend tests and 48 frontend JS tests pass (BEH-6)
- [x] No element `id`, `name`, or existing `class` value used by JS or Python tests is renamed, removed, or repurposed
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
