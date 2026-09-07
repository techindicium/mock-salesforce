<!-- partial_schema: plan@1 -->

# Implementation Plan: Sidebar navigation and standalone Contacts view

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-ui/charter.md
> **Spec:** .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md
> **Review:** PASS (2026-09-07) — skipped per risk policy (`require_review: false`)
> **Platform:** FastAPI (Python 3.11), stdlib sqlite3, vanilla HTML/CSS/JS, no build step

**Goal:** Add a persistent sidebar (Opportunities / Accounts / Contacts) to all four
crm-ui pages, and a new standalone Contacts view with full CRUD, reusing the existing
`GET /contacts` endpoint's already-supported unfiltered "all contacts" call.

**Architecture:** Two independent surfaces. (1) A CSS/HTML navigation shell — `.app-shell`
(flex row) wrapping a `.sidebar` (ported from mock-jira) and `.app-main` (existing page
content) — added to `index.html`, `deal.html`, `accounts.html`, and the new `contacts.html`,
with zero change to any existing element's `id`/`class`/behavior inside `.app-main`. (2) A
new page `contacts.html` + `contacts.js`, structured identically to `accounts.js` (fetch,
render, CRUD, error-state wiring), reusing `list-state.js`'s `replaceList`, `error-state.js`,
`errors.js`, and `form-errors.js` unchanged, and a small backward-compatible extension to
`api.js`'s `fetchContacts` (mirroring the existing `buildOpportunitiesUrl`/`fetchOpportunities`
optional-filter pattern) to support fetching all contacts unfiltered.

---

## File Structure

**Create:**
- `static/contacts.html` — new Contacts view page
- `static/js/contacts.js` — fetch/render/CRUD logic for the Contacts view
- `tests/test_ui_contacts_page.py` — structural test for the new page (mirrors `test_ui_accounts_page.py`)

**Modify:**
- `static/css/board.css` — add `.app-shell`/`.sidebar`/`.nav-item`/`.nav-item:hover`/`.nav-item.active`/`.app-main` rules (ported from mock-jira), plus minimal `#contacts-page` coverage reusing existing list-row/form patterns
- `static/index.html` — wrap existing content in `.app-shell`/`.sidebar`/`.app-main`, remove the ad hoc `<a href="accounts.html">Accounts</a>` link (superseded by the sidebar)
- `static/deal.html` — same wrap; keep the contextual "← Back to board" link inside `.app-main`'s header (page-specific breadcrumb, not a sidebar concern), remove the ad hoc `<a href="accounts.html">Accounts</a>` link
- `static/accounts.html` — same wrap; remove the ad hoc `<a href="index.html">Back to board</a>` link
- `static/js/api.js` — add `buildContactsUrl(accountId)` (mirrors `buildOpportunitiesUrl`) and change `fetchContacts(accountId)` to use it, supporting `accountId == null` → unfiltered `/contacts`
- `static/js/api.test.mjs` — add coverage for `buildContactsUrl`

**Reference (read, do not modify):**
- `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` lines 35-95 (`.app-shell`/`.sidebar`/`.nav-item`/`.app-main` — the source pattern) and `static/index.html` lines 10-16 (sidebar markup shape, adapted from `<button data-view>` SPA-style to real `<a href>` multi-page links since crm-ui is not a SPA)
- `static/js/accounts.js` (full) — the CRUD/render/error-wiring pattern `contacts.js` mirrors
- `static/js/board.js` lines 63-81 (`appendAccountOption`/`loadAccounts` pattern for populating an account `<select>`)
- `static/js/error-state.js`, `static/js/errors.js`, `static/js/list-state.js`, `static/js/form-errors.js` — reused unchanged
- `tests/test_ui_accounts_page.py` (full) — the structural-test pattern `test_ui_contacts_page.py` mirrors

## Context Packets

### Task 1 Context
- Spec: sidebar-navigation-and-contacts-view.spec.md (BEH-1, BEH-2)
- Source files: `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` lines 1-16 (`:root` tokens already ported — for reference only, not to re-add), lines 35-95 (`.app-shell`/`.sidebar`/`.nav-item`/`.app-main`)
- Current `static/css/board.css` (full, ~260 lines as left by the visual-design-system spec)

### Task 2 Context
- Spec: BEH-1, BEH-2, plus the spec's own "No existing id/class renamed" acceptance criterion
- Source files: `static/index.html`, `static/deal.html`, `static/accounts.html` (full, current content)
- Existing tests to keep green: `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`, `tests/test_ui_accounts_page.py`

### Task 3 Context
- Spec: BEH-3, BEH-6, BEH-7
- Source files: `static/js/accounts.js` (full — the pattern to mirror), `static/js/api.js` (full), `static/js/board.js` lines 63-81 (account-select population pattern), `static/js/error-state.js`, `static/js/errors.js`, `static/js/list-state.js` (full, small files — reused unchanged)
- `tests/test_ui_accounts_page.py` (full — structural test pattern)

### Task 4 Context
- Spec: BEH-4, BEH-5, error cases table
- Source files: `static/js/accounts.js` (full — Account CRUD form pattern to mirror for Contact), `static/js/form-errors.js` (reused unchanged), `static/js/deal.js` (Contact CRUD forms already exist here for the per-deal contacts section — mirror the same field set: first_name, last_name, email, title)

## Parallelization

- Group A (sequential): Task 1 → Task 2 (Task 2's wrap depends on Task 1's sidebar CSS existing, so the sidebar isn't unstyled during the wrap)
- Group B (sequential): Task 3 → Task 4 (Task 4 extends the page/module Task 3 creates)

Group A and Group B touch disjoint files (Group A: `board.css` + the three existing HTML
pages; Group B: `contacts.html`/`contacts.js`/`api.js`/`api.test.mjs`, new files or an
additive change to `api.js`) and can run in parallel with each other, but Task 2 also adds
the sidebar `<nav>` markup to a `contacts.html` that doesn't exist until Task 3 creates it —
so in practice run Group A fully before starting Task 3's markup, to avoid Task 3 having to
guess the sidebar markup shape independently. Sequential execution (1→2→3→4) is the safer,
recommended order despite the file-level independence.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Port sidebar CSS | small | unit | — | 0 create, 1 modify |
| 2 | Wire sidebar into existing pages | medium | unit | Task 1 | 0 create, 3 modify |
| 3 | contacts.html + contacts.js: fetch/render/empty-state/errors | large | unit | Task 2 | 2 create, 2 modify (+1 test create) |
| 4 | Contact CRUD on contacts.html | medium | unit | Task 3 | 0 create, 2 modify |

## Strategy Summary

| Strategy | Tasks | Source |
|----------|-------|--------|
| unit | 4 | detected (high confidence — same `lib/test-strategies/detection.mjs` result as the visual-design-system plan for `static/**`/`tests/**` paths) |

Granularity: `per-behavior` (source: `manifest.yaml` `test_policy.granularity`). BEH-1/BEH-2
share `tests/test_ui_*.py` (existing, extended) plus a new visual/structural assertion in
each page's test. BEH-3/BEH-6/BEH-7 get `tests/test_ui_contacts_page.py` (created in Task 3).
BEH-4/BEH-5 extend `tests/test_ui_contacts_page.py` in Task 4 (per-behavior — same suite,
new assertions).

---

## Task 1: Port sidebar CSS [specialist: none]

**Charter capability:** n/a — charter-extension (see spec frontmatter comment); this task
implements the spec's own BEH-1/BEH-2, not a pre-existing charter capability row.
**Strategy:** unit (source: detected, confidence: high)
**Files:**
- Modify: `static/css/board.css` (append `.app-shell`, `.sidebar`, `.nav-item`,
  `.nav-item:hover`, `.nav-item.active`, `.app-main` — additive only, no existing rule
  touched)
- Test: `tests/test_css_component_coverage.py` (extend — reuse the existing per-behavior
  suite from the visual-design-system spec, since this is the same kind of "selector
  coverage exists in board.css" assertion)

**Tests:** `tests/test_css_component_coverage.py` — extend with a new test asserting the
six sidebar-shell selectors exist.

**Context to load:**
- `/Users/dpavancini/Development/adev-course/mock-jira/static/css/board.css` lines 35-95

- [ ] **Write failing test**

Append to `tests/test_css_component_coverage.py`:

```python
def test_board_css_defines_sidebar_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        css = client.get("/css/board.css").text

    for selector in (".app-shell", ".sidebar", ".nav-item", ".nav-item:hover", ".nav-item.active", ".app-main"):
        assert selector in css
```

- [ ] **Verify test fails**

Run: `source .venv/bin/activate && python3 -m pytest -q tests/test_css_component_coverage.py::test_board_css_defines_sidebar_shell`
Expected: FAIL — none of these selectors exist yet.

- [ ] **Implement**

Append to `static/css/board.css` (adapted from mock-jira; our `.nav-item` will style an
`<a>` element, not a `<button>` like mock-jira's SPA-style nav — so omit the
`background: none; box-shadow: none; border: none;` button-reset properties mock-jira
needs and we don't, and add `text-decoration: none;` since it's a link):

```css
.app-shell {
  display: flex;
  align-items: flex-start;
  min-height: 100vh;
}

.sidebar {
  flex: 0 0 168px;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 1rem 0;
  background: var(--rail);
  border-right: 1px solid var(--ink-line);
  min-height: 100vh;
  box-sizing: border-box;
}

.nav-item {
  display: block;
  width: 100%;
  text-align: left;
  text-decoration: none;
  border-left: 4px solid transparent;
  padding: 0.6rem 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--paper-text-on-rail);
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease;
}

.nav-item:hover {
  background: var(--rail-light);
}

.nav-item.active {
  background: var(--rail-light);
  border-left-color: var(--stamp-gold);
  color: var(--paper);
}

.app-main {
  flex: 1;
  min-width: 0;
  padding: 1rem 1.5rem;
}
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_css_component_coverage.py`
Expected: PASS (all tests in the file, including the new one)

Full regression: `python3 -m pytest -q && node --test static/js/*.test.mjs && ruff check .`
— expect 119 pytest (118 + 1 new), 46 node, ruff clean.

- [ ] **Commit**

Branch: `feat/crm-ui/sidebar-navigation-and-contacts-view`

```bash
git checkout -b feat/crm-ui/sidebar-navigation-and-contacts-view
git add static/css/board.css tests/test_css_component_coverage.py
git commit -m "feat(crm-ui): port sidebar shell CSS from mock-jira

Spec: .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md"
```

---

## Task 2: Wire sidebar into existing pages [specialist: none]

**Charter capability:** n/a — charter-extension.
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `static/index.html`, `static/deal.html`, `static/accounts.html`

**Tests:** `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`,
`tests/test_ui_accounts_page.py` — extend each with a sidebar-presence assertion; the
existing assertions in each (substring `in html` checks on specific ids/classes) must
keep passing unmodified since nothing inside `.app-main` changes.

**Context to load:**
- `static/index.html`, `static/deal.html`, `static/accounts.html` (full, current content — see plan's File Structure section above for each file's exact current markup)

- [ ] **Write failing test**

Append to each of `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`,
`tests/test_ui_accounts_page.py` (adapt the `id="nav-..."` per page):

```python
def test_index_html_has_sidebar_with_three_nav_items(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text

    assert 'class="sidebar"' in html
    assert html.count('class="nav-item') == 3
    assert 'class="nav-item active"' in html
```

(For `deal.html`/`accounts.html`, fetch the matching route and adjust the function name;
the assertion shape is identical — sidebar present, exactly 3 nav items, exactly one active.)

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py tests/test_ui_deal_page.py tests/test_ui_accounts_page.py`
Expected: FAIL — no `.sidebar` exists in any of the three pages yet.

- [ ] **Implement**

For each of `static/index.html`, `static/deal.html`, `static/accounts.html`: wrap the
existing `<body>` content in:

```html
<div class="app-shell">
  <nav class="sidebar" aria-label="Main navigation">
    <a class="nav-item{ACTIVE}" href="index.html"{ARIA}>Opportunities</a>
    <a class="nav-item{ACTIVE}" href="accounts.html"{ARIA}>Accounts</a>
    <a class="nav-item{ACTIVE}" href="contacts.html"{ARIA}>Contacts</a>
  </nav>
  <div class="app-main">
    <!-- existing page content unchanged, minus the ad hoc back/accounts links below -->
  </div>
</div>
```

`{ACTIVE}` is literally ` active` on the one link matching the current page (e.g.
`index.html` → "Opportunities" gets ` active`), empty string on the other two.
`{ARIA}` is literally ` aria-current="page"` on that same active link, omitted on the
other two. `deal.html` counts as the "Opportunities" page for active-state purposes (it's
a sub-page of the pipeline board — there is no fourth nav item for it).

Remove the now-redundant ad hoc links: `static/index.html`'s
`<a href="accounts.html">Accounts</a>`; `static/deal.html`'s
`<a href="accounts.html">Accounts</a>` (keep `<a href="index.html">← Back to board</a>` as
a page-specific breadcrumb inside `.app-main`'s `<header>`, it is not redundant with the
sidebar since it reads differently — "back" vs. a persistent nav item); `static/accounts.html`'s
`<a href="index.html">Back to board</a>` (fully redundant with the sidebar's "Opportunities"
link, remove it and its wrapping `<header>` if the header becomes empty).

Do not change any other element, id, class, or script tag in any of the three files.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py tests/test_ui_deal_page.py tests/test_ui_accounts_page.py`
Expected: PASS, including every pre-existing assertion in these three files (spot-check:
`test_index_html_has_ten_stage_columns_and_account_switcher`,
`test_board_css_is_served_with_css_content_type`, and the accounts/deal equivalents).

Full regression: `python3 -m pytest -q && node --test static/js/*.test.mjs && ruff check .`.
Also: a headless-browser DOM dump (`google-chrome --headless=new --dump-dom`) of all three
pages to visually confirm the sidebar renders and no existing element lost its styling
(this repo's Check 11 automated visual verification is disabled — see the
visual-design-system spec's validate report addendum — so this manual check is the only
visual verification this task gets; do not skip it).

- [ ] **Commit**

```bash
git add static/index.html static/deal.html static/accounts.html
git commit -m "feat(crm-ui): wire sidebar into board, deal, and accounts pages

Spec: .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md"
```

---

## Task 3: contacts.html + contacts.js — fetch/render/empty-state/errors [specialist: none]

**Charter capability:** n/a — charter-extension.
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 2
**Files:**
- Create: `static/contacts.html`
- Create: `static/js/contacts.js`
- Modify: `static/js/api.js` (add `buildContactsUrl`, change `fetchContacts` to use it)
- Modify: `static/js/api.test.mjs` (add `buildContactsUrl` coverage)
- Test: `tests/test_ui_contacts_page.py`

**Tests:** `tests/test_ui_contacts_page.py` — new suite (BEH-3, BEH-6, BEH-7);
`static/js/api.test.mjs` — extended (the `buildContactsUrl` unit, pure logic, same
pattern as `buildOpportunitiesUrl`'s existing tests).

**Context to load:**
- `static/js/accounts.js` (full)
- `static/js/api.js` (full)
- `static/js/board.js` lines 63-81
- `tests/test_ui_accounts_page.py` (full)

- [ ] **Write failing test**

`tests/test_ui_contacts_page.py` (new file, mirrors `test_ui_accounts_page.py`'s shape):

```python
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_contacts_html_has_sidebar_and_list_container(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/contacts.html")
        assert response.status_code == 200
        html = response.text
        assert html.count('class="nav-item') == 3
        assert 'id="contacts-page"' in html
        assert 'id="all-contacts-list"' in html
        assert 'type="module"' in html
        # BEH-5: a Contact cannot be created without selecting an Account — pin the
        # client-side validation contract in code, not only in the manual smoke check.
        select_start = html.index('id="contact-account-select"')
        select_tag_end = html.index('>', select_start)
        assert 'required' in html[select_start:select_tag_end]
```

`static/js/api.test.mjs` — append (mirrors `buildOpportunitiesUrl`'s two existing tests
at lines 6-12):

```javascript
test('buildContactsUrl omits account_id when unset ("all contacts")', () => {
  assert.equal(buildContactsUrl(null), '/contacts');
});

test('buildContactsUrl includes account_id when set', () => {
  assert.equal(buildContactsUrl(2), '/contacts?account_id=2');
});
```

(Add `buildContactsUrl` to the existing import line at the top of `api.test.mjs`.)

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_contacts_page.py` — expect FAIL (`static/contacts.html`
does not exist, 404).
Run: `node --test static/js/api.test.mjs` — expect FAIL (`buildContactsUrl` is not exported).

- [ ] **Implement**

In `static/js/api.js`, add (mirroring `buildOpportunitiesUrl` exactly) and change
`fetchContacts` to use it — this is a backward-compatible change since every existing
caller (`deal.js`, `accounts.js`) always passes a real `accountId`:

```javascript
export function buildContactsUrl(accountId) {
  return accountId == null ? '/contacts' : `/contacts?account_id=${accountId}`;
}
```

```javascript
export function fetchContacts(accountId) {
  return request(buildContactsUrl(accountId), undefined, 'load contacts');
}
```

Create `static/contacts.html` (structure mirrors `accounts.html`'s shape: sidebar +
app-main + list + create form, "Contacts" nav item active):

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Contacts</title>
  <link rel="stylesheet" href="css/board.css" />
</head>
<body>
  <div class="app-shell">
    <nav class="sidebar" aria-label="Main navigation">
      <a class="nav-item" href="index.html">Opportunities</a>
      <a class="nav-item" href="accounts.html">Accounts</a>
      <a class="nav-item active" href="contacts.html" aria-current="page">Contacts</a>
    </nav>
    <div class="app-main">
      <div id="error-banner" role="alert" hidden></div>
      <main id="contacts-page">
        <h1>Contacts</h1>
        <ul id="all-contacts-list"></ul>
        <p id="contacts-empty-state" hidden>No contacts yet.</p>
        <button id="new-contact-btn" type="button">New contact</button>
        <form id="contact-form" hidden>
          <input type="hidden" id="contact-id-input" />
          <div id="contact-form-error" class="form-error" role="alert"></div>
          <label for="contact-account-select">Account</label>
          <select id="contact-account-select" name="account_id" required></select>
          <label for="contact-first-name-input">First name</label>
          <input id="contact-first-name-input" name="first_name" type="text" />
          <label for="contact-last-name-input">Last name</label>
          <input id="contact-last-name-input" name="last_name" type="text" required />
          <label for="contact-email-input">Email</label>
          <input id="contact-email-input" name="email" type="email" />
          <label for="contact-title-input">Title</label>
          <input id="contact-title-input" name="title" type="text" />
          <button type="submit">Save contact</button>
          <button type="button" id="cancel-contact-form-btn">Cancel</button>
        </form>
      </main>
    </div>
  </div>
  <script type="module" src="js/contacts.js"></script>
</body>
</html>
```

Create `static/js/contacts.js` (fetch/render/empty-state/error-wiring only — CRUD form
submit handlers are Task 4's job; still wire the "New contact" button to open the form
and populate the account `<select>`, since BEH-5 requires that select to exist and be
populated, but leave the actual `POST`/`PATCH`/`DELETE` calls for Task 4):

```javascript
import { fetchAccounts, fetchContacts, resolveAccountName } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';

const errorBanner = document.getElementById('error-banner');
const listEl = document.getElementById('all-contacts-list');
const emptyState = document.getElementById('contacts-empty-state');
const accountSelect = document.getElementById('contact-account-select');
const newContactBtn = document.getElementById('new-contact-btn');
const contactForm = document.getElementById('contact-form');
const cancelBtn = document.getElementById('cancel-contact-form-btn');

let errorState = new Map();
let accounts = [];
let contacts = [];

function renderErrorBanner() {
  const message = bannerMessage(errorState);
  errorBanner.textContent = message ?? '';
  errorBanner.hidden = message == null;
}

function reportError(source, message) {
  errorState = setError(errorState, source, message);
  renderErrorBanner();
}

function reportSuccess(source) {
  errorState = clearError(errorState, source);
  renderErrorBanner();
}

function renderContacts() {
  listEl.innerHTML = '';
  emptyState.hidden = contacts.length !== 0;
  for (const contact of contacts) {
    const li = document.createElement('li');
    li.dataset.contactId = contact.id;
    const accountName = resolveAccountName(accounts, contact.account_id);
    const summary = document.createElement('span');
    summary.textContent = `${contact.first_name} ${contact.last_name} — ${accountName} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    li.appendChild(summary);
    listEl.appendChild(li);
  }
}

async function loadAccounts() {
  try {
    accounts = await fetchAccounts();
    accountSelect.innerHTML = '';
    for (const account of accounts) {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.name;
      accountSelect.appendChild(option);
    }
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('load accounts', err));
  }
}

async function loadContacts() {
  try {
    const next = await fetchContacts(null);
    contacts = replaceList(contacts, next);
    reportSuccess('contacts');
    renderContacts();
  } catch (err) {
    reportError('contacts', describeApiError('load contacts', err));
  }
}

newContactBtn.addEventListener('click', () => { contactForm.hidden = false; });
cancelBtn.addEventListener('click', () => { contactForm.hidden = true; });

async function init() {
  await loadAccounts();
  await loadContacts();
}

init();
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_contacts_page.py` — expect PASS.
Run: `node --test static/js/api.test.mjs` — expect PASS.

Full regression: `python3 -m pytest -q && node --test static/js/*.test.mjs && ruff check .`.
Headless-browser DOM dump of `contacts.html` with the seeded fixture data running behind
it, to confirm all 8 seeded Contacts render with their correct owning-Account name (not
"Unknown account" — a wrong `account_id` lookup would silently mislabel every row).

- [ ] **Commit**

```bash
git add static/contacts.html static/js/contacts.js static/js/api.js static/js/api.test.mjs tests/test_ui_contacts_page.py
git commit -m "feat(crm-ui): add contacts.html — fetch, render, empty-state, errors

Spec: .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md"
```

---

## Task 4: Contact CRUD on contacts.html [specialist: none]

**Charter capability:** n/a — charter-extension.
**Strategy:** unit (source: detected, confidence: high)
**Depends on:** Task 3
**Files:**
- Modify: `static/js/contacts.js` (add create/edit/delete wiring)
- Modify: `tests/test_ui_contacts_page.py` (extend)

**Tests:** `tests/test_ui_contacts_page.py` — extend with BEH-4/BEH-5 coverage.

**Context to load:**
- `static/js/accounts.js` (full — the Account CRUD form-submit pattern to mirror exactly for Contact: `openXForm`/form submit handler calling `createX`/`updateX`, `deleteX` wired to a per-row button)
- `static/js/form-errors.js` (reused unchanged)

- [ ] **Write failing test**

Append to `tests/test_ui_contacts_page.py`:

```python
def test_contacts_html_has_edit_and_delete_buttons_per_row(tmp_path, monkeypatch):
    # This is a structural smoke test only — the per-row edit/delete buttons are
    # rendered by contacts.js at runtime (dataset-driven, like accounts.js's
    # edit-account-btn/delete-account-btn), so this test asserts the JS file
    # references the expected class hooks rather than asserting on static HTML.
    contacts_js = (STATIC_DIR / "js" / "contacts.js").read_text()
    assert "edit-contact-btn" in contacts_js
    assert "delete-contact-btn" in contacts_js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_contacts_page.py::test_contacts_html_has_edit_and_delete_buttons_per_row`
Expected: FAIL — `contacts.js` (as left by Task 3) has no edit/delete buttons yet, only a
read-only summary `<span>` per row.

- [ ] **Implement**

In `static/js/contacts.js`, import `createContact, updateContact, deleteContact` from
`./api.js` and `inlineErrorMessage` from `./form-errors.js`. Add:

- `renderContacts()`: per row, append an `edit-contact-btn` and `delete-contact-btn`
  button (mirroring `accounts.js`'s `renderAccounts()` per-row button pattern exactly —
  `className` assignment, `dataset` already set on the `<li>`), wired to open the
  (now-shared, not create-only) form pre-filled for edit, and to call `deleteContact`
  respectively.
- The form's submit handler: read `contact-id-input` — empty means create (`POST`
  `/contacts` via `createContact`), non-empty means edit (`PATCH` via `updateContact`).
  On success: call `loadContacts()` again to re-fetch and re-render (matches this
  module's "no client-side cache" postcondition from the spec). On failure: set
  `contact-form-error`'s `textContent` via `inlineErrorMessage(err)`, keep the form open.
- Delete handler: call `deleteContact(id)`, on success re-run `loadContacts()`, on
  failure `reportError('delete', describeApiError('delete contact', err))`.
- `newContactBtn` handler (already wired in Task 3): also clear `contact-id-input` and
  reset the form fields, so reusing the same form for "new" after a previous "edit"
  doesn't leak stale values (mirrors `accounts.js`'s `openAccountForm(null)` pattern).

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_contacts_page.py` — expect PASS (all tests in the file).

Full regression: `python3 -m pytest -q && node --test static/js/*.test.mjs && ruff check .`.
Headless-browser interactive smoke check: with the app running, verify creating a Contact
from `contacts.html` with a real Account selected succeeds and the new row appears; verify
editing and deleting round-trip correctly; verify submitting with no Account selected is
blocked by the browser's native `required` validation on the `<select>` before any network
call (BEH-5's `n/a` error code — no HTTP request should even be observed). Also verify the
failure path required by BEH-4's postcondition: edit a Contact to an invalid state that
the API rejects (e.g. blank `last_name`, which `crm-api`'s `ContactIn` requires — see
`account-and-contact-management.spec.md`) and confirm the list is unchanged and
`contact-form-error` shows the API's message verbatim, not a generic failure.

- [ ] **Commit**

```bash
git add static/js/contacts.js tests/test_ui_contacts_page.py
git commit -m "feat(crm-ui): contact CRUD wiring on contacts.html

Spec: .context-index/specs/features/crm-ui/sidebar-navigation-and-contacts-view.spec.md"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results
are recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:
- Tests pass: `python3 -m pytest -q`
- Lint passes: `ruff check .`
- Integration tests (unaffected, but must still pass): `python3 -m pytest -q tests/docker`
  (run with a non-default `PORT`/`MCP_PORT` on this shared dev machine — see the
  visual-design-system spec's validate report for why)

Additionally for this plan specifically:
- Frontend JS suite unchanged/extended and passing: `node --test static/js/*.test.mjs`
- All acceptance criteria from `sidebar-navigation-and-contacts-view.spec.md` satisfied
- No element `id`, `name`, or existing `class` value used by `board.js`/`deal.js`/`accounts.js`
  or `tests/test_ui_*.py` renamed, removed, or repurposed (spot-checked at every task)
- Manual headless-browser visual verification at Tasks 2, 3, and 4 (Check 11 automated
  visual verification is disabled in this project's `governance/validate.yaml` — see the
  visual-design-system spec's real caught-bug precedent for why this manual step is not
  optional for this plan)
