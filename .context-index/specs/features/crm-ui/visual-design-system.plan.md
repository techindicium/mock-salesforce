<!-- partial_schema: plan@1 -->

# Implementation Plan: Port mock-jira's visual design system to crm-ui

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-ui/charter.md
> **Spec:** .context-index/specs/features/crm-ui/visual-design-system.spec.md
> **Review:** PASS (2026-09-07) — skipped per risk policy (`require_review: false`)
> **Platform:** FastAPI (Python 3.11), stdlib sqlite3, vanilla HTML/CSS/JS, no build step

**Goal:** Restyle all three `crm-ui` pages (board, deal detail, accounts) to use mock-jira's ported
design tokens and component treatment, with zero change to HTML structure, JS behavior, or the
backend.

**Architecture:** Single-file change: `static/css/board.css` grows from 9 lines of ad hoc,
hardcoded-color rules covering only the board page into a token-driven stylesheet covering all
three pages' existing elements. No HTML file gains, loses, or renames an `id`/`class`/`name` — at
most a purely-presentational `class` is added to an element that has none today. No JS file
changes. Migration proceeds in the same four steps as the spec's Migration Path: tokens first,
then board-page restyle, then deal.html coverage, then accounts.html coverage — each step leaves
all 111 backend + 46 frontend tests passing.

---

## File Structure

**Create:**
- `tests/test_css_design_tokens.py` — asserts the `:root` token block and `[hidden]` guard exist in `static/css/board.css`
- `tests/test_css_component_coverage.py` — asserts board.css carries rules for every button/input/select/`.form-error` and for the board/deal/accounts page-specific selectors

**Modify:**
- `static/css/board.css` — the entire restyle; see Migration Path in the spec for the four-step breakdown

**Reference (read, do not modify):**
- `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` — source of the ported design tokens and component treatment
- `static/index.html`, `static/deal.html`, `static/accounts.html` — the fixed set of selectors every new/modified rule must target
- `static/js/board.js`, `static/js/deal.js`, `static/js/accounts.js` — confirms every `id`/`class` this plan's rules target, and confirms `hidden` (not a CSS class) drives all show/hide
- `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`, `tests/test_ui_accounts_page.py` — existing structural regression tests, re-run unmodified after every task

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/crm-ui/visual-design-system.spec.md` (Migration Path Step 1, BEH-1, BEH-2)
- Charter: `.context-index/specs/features/crm-ui/charter.md`
- Source files: `static/css/board.css` (full, current 9 lines), `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` (full, reference only — read, never imported)
- Existing test pattern: `tests/test_ui_board_page.py::test_board_css_is_served_with_css_content_type` (TestClient + `STATIC_ASSETS_PATH` pattern to follow for the new CSS tests)

### Task 2 Context
- Spec: `.context-index/specs/features/crm-ui/visual-design-system.spec.md` (Migration Path Step 2, BEH-1, BEH-3, BEH-4)
- Source files: `static/css/board.css` (as left by Task 1), `static/index.html` (full — every selector this task must cover), mock-jira `board.css` (component reference: `button`, `.column`, `.card`, `.switcher-plate`)

### Task 3 Context
- Spec: `.context-index/specs/features/crm-ui/visual-design-system.spec.md` (Migration Path Step 3, BEH-1, BEH-3)
- Source files: `static/css/board.css` (as left by Task 2), `static/deal.html` (full — every selector this task must cover: `#opportunity-fields`/`#account-fields` `dl`, `#contacts-list` + `li` + `.edit-contact-btn`/`.delete-contact-btn`, `#edit-opportunity-form`, `#contact-form`)

### Task 4 Context
- Spec: `.context-index/specs/features/crm-ui/visual-design-system.spec.md` (Migration Path Step 4, BEH-1, BEH-3)
- Source files: `static/css/board.css` (as left by Task 3), `static/accounts.html` (full — every selector this task must cover: `#accounts-list` + `li` + `.edit-account-btn`/`.delete-account-btn`/`.account-delete-error`/`.account-new-opportunity-btn`, `<details>`/`<summary>`/`.account-contacts-list`, `#account-form`, `#account-new-opportunity-form`, `#account-contact-form`)

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 (all four tasks modify the same single file, `static/css/board.css`, in the exact order the spec's Migration Path requires — each step's rules build on the tokens/reset the prior step added)

No task in this plan can run in parallel with another — this is a deliberate consequence of restyling one shared stylesheet in dependency order, not a planning gap.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Port design tokens + `[hidden]` guard | small | unit | — | 0 create, 1 modify (+1 test create) |
| 2 | Restyle board-page rules + global button/input treatment | medium | unit | Task 1 | 0 create, 1 modify (+1 test create) |
| 3 | Add coverage for deal.html elements | medium | unit | Task 2 | 0 create, 1 modify (test: extend) |
| 4 | Add coverage for accounts.html elements | medium | unit | Task 3 | 0 create, 1 modify (test: extend) |

## Strategy Summary

| Strategy | Tasks | Source |
|----------|-------|--------|
| unit | 4 | detected (high confidence — `lib/test-strategies/detection.mjs` on `static/css/*.css` paths) |

Granularity: `per-behavior` (source: `manifest.yaml` `test_policy.granularity`). BEH-1/BEH-2 get
their own suite (`tests/test_css_design_tokens.py`, created in Task 1); BEH-3/BEH-4 share one
suite (`tests/test_css_component_coverage.py`, created in Task 2, extended in Tasks 3-4). BEH-5
("every previously-passing test still passes") has no suite of its own — it is verified by
re-running the full existing suites (`python3 -m pytest -q`, `node --test static/js/*.test.mjs`)
at the end of every task, per the Quality Gates section.

---

## Task 1: Port design tokens + `[hidden]` guard [specialist: none]

**Charter capability:** n/a — this is a refactor spec (`kind: refactor`), not a new charter capability; see `mode: refactor` frontmatter.
**Strategy:** unit (source: detected, confidence: high)
**Files:**
- Modify: `static/css/board.css` (add `:root` block, `[hidden]` guard, `* { box-sizing: border-box; }` reset — additive only, no existing rule touched)
- Test: `tests/test_css_design_tokens.py`

**Tests:** `tests/test_css_design_tokens.py` — new suite, covers BEH-1 (design tokens exist) and BEH-2 (`[hidden]` guard survives any later rule's specificity).

**Context to load:**
- `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` (lines 1-21: the `:root` block and its comments)

- [ ] **Write failing test**

```python
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_board_css_defines_design_tokens(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert ":root" in css
    for token in ("--ink", "--rail", "--paper", "--stamp-red", "--stamp-gold", "--stamp-green", "--ink-line"):
        assert token in css


def test_board_css_hidden_guard_is_important(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "[hidden]" in css
    # Must be !important so no later, more-specific display rule can defeat it —
    # every form on all three pages is shown/hidden via the `hidden` attribute (see
    # static/js/board.js, deal.js, accounts.js), never via a CSS class.
    hidden_rule_start = css.index("[hidden]")
    hidden_rule = css[hidden_rule_start:hidden_rule_start + 80]
    assert "!important" in hidden_rule
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_css_design_tokens.py`
Expected: FAIL — `AssertionError` (no `:root` block, no `--ink` token, no `[hidden]` rule in the current 9-line `board.css`)

- [ ] **Implement**

Prepend to `static/css/board.css` (port from mock-jira's `board.css` lines 1-25, values unchanged):

```css
:root {
  --ink: #16261f;
  --rail: #2f4a3e;
  --paper: #f1ecdd;
  --stamp-red: #a3402f;
  --stamp-gold: #b98a2e;
  --stamp-green: #4c7a5e;
  --ink-line: #55483a;

  --rail-light: #3c5c4e;
  --paper-dim: #e7e1cf;
  --ink-text-on-paper: #201a12;
  --paper-text-on-rail: #f1ecdd;
  --stamp-gold-dim: rgba(185, 138, 46, 0.35);
}

[hidden] {
  display: none !important;
}

* {
  box-sizing: border-box;
}
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_css_design_tokens.py`
Expected: PASS (2 tests)

Also run the full regression sweep (BEH-5): `python3 -m pytest -q && node --test static/js/*.test.mjs` — expect the same 111 + 46 passes as before this task, since this step is purely additive.

- [ ] **Commit**

Branch: `feat/crm-ui/visual-design-system`

```bash
git checkout -b feat/crm-ui/visual-design-system
git add static/css/board.css tests/test_css_design_tokens.py
git commit -m "feat(crm-ui): port mock-jira's design tokens and [hidden] guard"
```

---

## Task 2: Restyle board-page rules + global button/input treatment [specialist: none]

**Charter capability:** n/a (refactor spec)
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `static/css/board.css` (repoint `body`, `header`, `#error-banner`, `#board`, `.stage-column`, `.cards`, `.opportunity-card` at the new tokens; add global `button`, `input`, `select`, `.form-error` rules per mock-jira's component treatment)
- Test: `tests/test_css_component_coverage.py`

**Tests:** `tests/test_css_component_coverage.py` — new suite, covers BEH-3 (buttons/inputs/`.form-error` styled consistently) and BEH-4 (board columns/cards restyled).

**Context to load:**
- `static/index.html` (full — every element this task's rules must match: `#account-switcher`, `#new-opportunity-btn`, `#create-opportunity-form` and its fields, `.stage-column`, `.cards`, the rendered `.opportunity-card`)
- `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` (lines 203-335: `button`, `.column`, `.card`, `.column-header`, `.switcher-plate` — component reference, adapted to this project's actual selectors, not copied verbatim since class names differ)

- [ ] **Write failing test**

```python
def test_board_css_styles_buttons_and_form_error(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert "button {" in css or "button{" in css
    assert ".form-error" in css
    assert "var(--stamp-gold)" in css or "var(--ink-line)" in css  # buttons must use tokens, not new literals


def test_board_css_restyles_columns_and_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    assert ".stage-column" in css
    assert ".opportunity-card" in css
    # No hardcoded literal from the pre-refactor stylesheet should remain
    for literal in ("#f4f5f7", "#ddd", "#fdecea", "#611a15"):
        assert literal not in css
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py`
Expected: FAIL — the old hardcoded literals are still present and no `button`/`.form-error` rule exists yet

- [ ] **Implement**

Replace the current `body`, `header`, `#error-banner`, `#board`, `.stage-column`, `.cards`,
`.opportunity-card` rules in `static/css/board.css` with token-driven equivalents (surface =
`var(--paper)`, page background = `var(--ink)`, borders = `var(--ink-line)`, accents =
`var(--stamp-gold)`/`var(--stamp-red)`, flat `2px 2px 0 rgba(0,0,0,0.35)` shadows, `2px` border
radius — mirroring mock-jira's treatment) and add global `button`, `input`, `select`,
`.form-error` rules using the same tokens, matching mock-jira's flat/bordered/hard-shadow look.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py`
Expected: PASS (2 tests)

Full regression sweep (BEH-5): `python3 -m pytest -q && node --test static/js/*.test.mjs` — 111 + 46 still pass.

- [ ] **Commit**

```bash
git add static/css/board.css tests/test_css_component_coverage.py
git commit -m "feat(crm-ui): restyle board page and global button/form-field rules"
```

---

## Task 3: Add coverage for deal.html elements [specialist: none]

**Charter capability:** n/a (refactor spec)
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `static/css/board.css` (add rules for `#deal-detail`, `#opportunity-section`, `#account-summary`, `#contacts-section`, `dl`/`dt`/`dd`, `#contacts-list` + `li` + `.edit-contact-btn`/`.delete-contact-btn`, `#edit-opportunity-form`, `#contact-form`)
- Test: `tests/test_css_component_coverage.py` (extend — per-behavior granularity, BEH-3 already has this suite from Task 2)

**Tests:** `tests/test_css_component_coverage.py` — extend with deal.html-specific assertions.

**Context to load:**
- `static/deal.html` (full — the exact selector list above comes from this file's current markup)

- [ ] **Write failing test**

Append to `tests/test_css_component_coverage.py`:

```python
def test_board_css_covers_deal_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in ("#deal-detail", "#contacts-list", "#edit-opportunity-form", "#contact-form"):
        assert selector in css
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py::test_board_css_covers_deal_page_elements`
Expected: FAIL — none of these selectors exist in `board.css` yet

- [ ] **Implement**

Add the deal.html rules to `static/css/board.css`, reusing the `button`/`input`/`select`/
`.form-error` treatment from Task 2 (no duplication — those are already global rules) and adding
only what's specific to this page: the `dl`/`dt`/`dd` field-list layout, the contacts `li` row
treatment with its two action buttons, and the account-summary panel.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py`
Expected: PASS (all tests in the file, including the two from Task 2)

Full regression sweep (BEH-5): `python3 -m pytest -q && node --test static/js/*.test.mjs`, plus a
headless-browser DOM dump of `deal.html?id=<seeded id>` to confirm visual coverage (manual check —
`validate.yaml`'s visual-verification check is disabled project-wide, so this is not an automated
gate, but the migration step's own verification per the spec).

- [ ] **Commit**

```bash
git add static/css/board.css tests/test_css_component_coverage.py
git commit -m "feat(crm-ui): restyle deal detail page elements"
```

---

## Task 4: Add coverage for accounts.html elements [specialist: none]

**Charter capability:** n/a (refactor spec)
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 3
**Files:**
- Modify: `static/css/board.css` (add rules for `#accounts-page`, `#accounts-list` + `li` + `.edit-account-btn`/`.delete-account-btn`/`.account-delete-error`/`.account-new-opportunity-btn`, `<details>`/`<summary>`/`.account-contacts-list`, `#account-form`, `#account-new-opportunity-form`, `#account-contact-form`)
- Test: `tests/test_css_component_coverage.py` (extend)

**Tests:** `tests/test_css_component_coverage.py` — extend with accounts.html-specific assertions.

**Context to load:**
- `static/accounts.html` (full — the exact selector list above comes from this file's current markup)

- [ ] **Write failing test**

Append to `tests/test_css_component_coverage.py`:

```python
def test_board_css_covers_accounts_page_elements(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in ("#accounts-list", ".account-delete-error", "#account-form", "#account-new-opportunity-form", "#account-contact-form"):
        assert selector in css
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py::test_board_css_covers_accounts_page_elements`
Expected: FAIL — none of these selectors exist in `board.css` yet

- [ ] **Implement**

Add the accounts.html rules to `static/css/board.css`, reusing the global `button`/`input`/
`select`/`.form-error` treatment and the `dl`/list-row pattern established in Task 3 (accounts
list items follow the same row shape as the contacts list), adding only what's new: the three
forms' layout and the `<details>`/`<summary>` disclosure treatment.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py`
Expected: PASS (all tests in the file — every assertion from Tasks 2-4)

Full regression sweep (BEH-5): `python3 -m pytest -q && node --test static/js/*.test.mjs`, plus a
headless-browser DOM dump of `accounts.html` to confirm visual coverage (manual check, same
rationale as Task 3).

- [ ] **Commit**

```bash
git add static/css/board.css tests/test_css_component_coverage.py
git commit -m "feat(crm-ui): restyle accounts page elements"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:
- Tests pass: `python3 -m pytest -q`
- Lint passes: `ruff check .`
- Integration tests (unaffected by this refactor, but must still pass): `python3 -m pytest -q tests/docker` (triggered on `post-implement`)

Additionally for this plan specifically:
- Frontend JS suite unchanged and passing: `node --test static/js/*.test.mjs` (not a `gates.yaml` entry, but asserted in every task above per BEH-5)
- All acceptance criteria from `visual-design-system.spec.md` satisfied
- No element `id`, `name`, or existing `class` value renamed, removed, or repurposed (spot-checked against `static/js/board.js`, `deal.js`, `accounts.js` and `tests/test_ui_*.py` at every task)
