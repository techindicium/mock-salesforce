<!-- partial_schema: plan@1 -->

# Implementation Plan: Deal detail page and CRUD forms

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-ui/charter.md
> **Spec:** .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.spec.md
> **Review:** PASS (2026-09-05) — skipped per risk policy (`risk_level: medium`, `require_review: false`)
> **Platform:** no frontend framework (vanilla HTML/CSS/JS, ES modules, no bundler), served by
> crm-api (Python 3.11 / FastAPI) via `STATIC_ASSETS_PATH`; JS pure-logic tests run on Node's
> built-in test runner (`node --test`) — no new npm/build tooling introduced

**Goal:** Ship a deal (Opportunity) detail page — full field detail, related Account summary,
read-only related-Contacts list, edit/delete actions — plus create/edit/delete forms for
Opportunity, Account, and Contact, all calling crm-api's existing CRUD endpoints.

**Architecture:** This plan extends the crm-ui static bundle the `pipeline-board-view` plan
already shipped (`static/index.html`, `static/js/{stages,api,errors,error-state,board-state,board}.js`,
`static/css/board.css`), served as-is by crm-api's existing static-file router
(`src/mock_salesforce/static.py`) — no backend changes. Two new pages are added,
`static/deal.html` (Opportunity detail + Account summary + Contacts) and `static/accounts.html`
(Account list + CRUD), each with its own thin DOM-wiring module (`static/js/deal.js`,
`static/js/accounts.js`). `static/js/api.js` (already existing, reused) gains the additional
fetch/mutate functions this spec needs, plus a shared `ApiError` that carries the API's
structured `{"error": code, "message": msg}` envelope (see `src/mock_salesforce/errors.py`) so
forms can show the exact validation-field or dependent-count message inline (BEH-7, Error Cases
table) instead of a generic HTTP-status string — `static/js/error-state.js` and
`static/js/errors.js` are reused unmodified for the top-of-page error banner, matching this
project's "reuse rather than duplicate fetch/error logic" convention. Two small new pure modules
are added: `static/js/list-state.js` (a generic full-list-replace helper, the same invariant
`board-state.js`'s `replaceOpportunities` already enforces — a refreshed list must never merge
with a stale one) and `static/js/form-errors.js` (picks the most specific message available for
an inline form error). DOM wiring is verified structurally through new pytest suites
(`tests/test_ui_deal_page.py`, `tests/test_ui_accounts_page.py`) following the exact
`TestClient` + `STATIC_ASSETS_PATH` pattern already used in `tests/test_ui_board_page.py` and
`tests/test_static_hosting.py`. Test granularity follows `manifest.yaml`'s `test_policy.granularity:
per-behavior` in the same spirit as the `pipeline-board-view` plan: each new suite file is
created once and extended by every later task that adds coverage to the same file, rather than
each task creating its own throwaway suite. Visual/browser-level verification stays out of
scope: `governance/validate.yaml` has visual-verification disabled and no browser-automation tool
is configured.

The spec names two valid entry points for two behaviors — BEH-5's create-opportunity form
"(from the board or an Account's page)" and BEH-6's Contact form "(reached from the deal detail
page's related-Contacts list, or an Account's page)" — and this plan implements both entry
points for each, not just one: the board (Task 8) and the deal detail page (Task 7) as already
planned, plus a second wiring pass on `static/accounts.html`/`static/js/accounts.js` (Task 11)
that adds a per-account "New opportunity" action (reusing `createOpportunity`, navigating to
`deal.html?id=<id>` on success, same as Task 8) and a per-account Contacts sub-list with its own
create/edit/delete form (reusing `createContact`/`updateContact`/`deleteContact` and
`replaceList`, same as Task 7).

---

## File Structure

**Create:**
- `static/js/list-state.js` — `replaceList(prior, next)`: generic full-replace helper for any
  fetched list (Contacts, Accounts)
- `static/js/form-errors.js` — `inlineErrorMessage(error)`: prefers the API's structured message
  (`ApiError.apiMessage`) for inline field/dependent-count display, falls back to `error.message`
- `static/deal.html` — deal detail page shell: Opportunity fields, Account summary, Contacts
  list, edit/delete-opportunity controls, create/edit/delete-contact form
- `static/js/deal.js` — DOM wiring for the deal detail page: initial fetch-and-render (BEH-1,
  BEH-2), edit/delete-opportunity (BEH-3, BEH-4), contact CRUD + list refresh (BEH-6), error
  banner + inline errors (BEH-8)
- `static/accounts.html` — Accounts list page shell: account list, create/edit-account form
  (later extended by Task 11 with a per-account "New opportunity" form and Contacts sub-list +
  contact form — the "Account's page" entry point BEH-5/BEH-6 name)
- `static/js/accounts.js` — DOM wiring for the Accounts page: fetch-and-render, create/edit/
  delete-account (BEH-7, including the inline 409 `ACCOUNT_HAS_DEPENDENTS` case), error banner
  (later extended by Task 11 with create-opportunity and Contact CRUD wiring per account)
- `static/js/list-state.test.mjs`, `static/js/form-errors.test.mjs` — unit suites (`node --test`)
- `tests/test_ui_deal_page.py` — pytest suite asserting `static/deal.html`/`static/js/deal.js`
  are served with the expected structural DOM contract
- `tests/test_ui_accounts_page.py` — pytest suite asserting `static/accounts.html`/
  `static/js/accounts.js` are served with the expected structural DOM contract

**Modify:**
- `static/js/api.js` — add `ApiError`, a shared `request()`/`jsonRequest()` helper, and
  `fetchOpportunity`, `fetchAccount`, `fetchContacts`, `createOpportunity`, `updateOpportunity`,
  `deleteOpportunity`, `createAccount`, `updateAccount`, `deleteAccount`, `createContact`,
  `updateContact`, `deleteContact`. Existing exports (`buildOpportunitiesUrl`, `fetchAccounts`,
  `fetchOpportunities`, `resolveAccountName`, `updateOpportunityStage`) are untouched — new code
  only extends the file, per the sibling plan's own "extend, do not replace" convention.
- `static/js/api.test.mjs` — extend with tests for the new functions
- `static/index.html` — add a "+ New opportunity" button + create-opportunity form, and a nav
  link to `accounts.html`
- `static/js/board.js` — add an opportunity-card click handler that navigates to
  `deal.html?id=<id>` (BEH-1), and wire the create-opportunity form (BEH-5)
- `tests/test_ui_board_page.py` — extend with assertions for the new nav link, create-opportunity
  form, and card-click wiring

**Reference (read, do not modify):**
- `src/mock_salesforce/models.py` — full field shapes: `OpportunityOut` (`id`, `account_id`,
  `name`, `stage_name`, `amount`, `close_date`, `probability`, `opportunity_type`, `lead_source`,
  `next_step`, `is_closed`, `is_won`, `created_at`, `updated_at`), `AccountOut` (`id`, `name`,
  `account_type`, `industry`, `website`, `phone`, `billing_*`, `created_at`, `updated_at`),
  `ContactOut` (`id`, `account_id`, `first_name`, `last_name`, `email`, `phone`, `title`,
  `created_at`, `updated_at`)
- `src/mock_salesforce/opportunities.py` — `POST /opportunities`, `GET /opportunities/{id}`
  (404 `OPPORTUNITY_NOT_FOUND`), `PATCH /opportunities/{id}` (partial update), `DELETE
  /opportunities/{id}` (204)
- `src/mock_salesforce/accounts.py` — `POST /accounts`, `GET /accounts/{id}` (404
  `ACCOUNT_NOT_FOUND`), `PATCH /accounts/{id}`, `DELETE /accounts/{id}` (409
  `ACCOUNT_HAS_DEPENDENTS` when `dependent_count(conn, account_id) > 0`)
- `src/mock_salesforce/contacts.py` — `POST /contacts`, `GET /contacts?account_id=`, `PATCH
  /contacts/{id}`, `DELETE /contacts/{id}` (404 `CONTACT_NOT_FOUND`)
- `src/mock_salesforce/errors.py` — error envelope shape `{"error": <code>, "message": <str>}` on
  every non-2xx response, including 422 `VALIDATION_ERROR` (message already prefixed with the
  offending field name) and 409 `ACCOUNT_HAS_DEPENDENTS`
- `src/mock_salesforce/static.py` — confirms `GET /{full_path}` serves any file under
  `STATIC_ASSETS_PATH`, not just `index.html` at `/` — `deal.html` and `accounts.html` are served
  the same way at their own paths
- `static/js/api.js`, `static/js/errors.js`, `static/js/error-state.js`, `static/js/board-state.js`,
  `static/js/board.js`, `static/index.html` — the existing pipeline-board-view modules this spec
  extends or reuses unmodified
- `tests/test_ui_board_page.py`, `tests/test_static_hosting.py`, `tests/conftest.py` — existing
  `TestClient` + `STATIC_ASSETS_PATH` test pattern to follow

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/crm-ui/deal-detail-and-crud-forms.spec.md` (BEH-1
  through BEH-7, Error Cases table)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capabilities: Deal detail page;
  Create/edit/delete opportunity; Create/edit/delete account; Create/edit/delete contact)
- Source files: `src/mock_salesforce/models.py` (full read — all three `*Out`/`*Create`/
  `*Update` shapes), `src/mock_salesforce/opportunities.py`, `src/mock_salesforce/accounts.py`,
  `src/mock_salesforce/contacts.py` (signatures only — every CRUD route + status code),
  `src/mock_salesforce/errors.py` (full read — error envelope shape), `static/js/api.js` (from
  the pipeline-board-view plan, full read — extend, do not replace)

### Task 2 Context
- Spec: same file (BEH-6, Postconditions — "no stale field is shown")
- Charter: capability: Create/edit/delete contact; Create/edit/delete account
- Source files: `static/js/board-state.js` (full read — the `replaceOpportunities` full-replace
  precedent this module generalizes)

### Task 3 Context
- Spec: same file (BEH-7, Error Cases table — 422 `VALIDATION_ERROR`, 409
  `ACCOUNT_HAS_DEPENDENTS`)
- Charter: capabilities: Create/edit/delete opportunity; Create/edit/delete account;
  Create/edit/delete contact
- Source files: none new — this is a pure function over the `ApiError` shape Task 1 defines
  (tested with plain object fixtures, no import of `api.js` needed)

### Task 4 Context
- Spec: same file (BEH-1, BEH-2)
- Charter: capability: Deal detail page
- Source files: `static/index.html` (from pipeline-board-view, full read — page-shell
  conventions: `<link>` to `css/board.css`, `type="module"` script, `#error-banner`)

### Task 5 Context
- Spec: same file (BEH-1, BEH-2)
- Charter: capability: Deal detail page
- Source files: `static/deal.html` (from Task 4, full read), `static/js/api.js` (from Task 1,
  export signatures: `fetchOpportunity`, `fetchAccount`, `fetchContacts`), `static/js/error-state.js`,
  `static/js/errors.js` (from pipeline-board-view, full read — reuse unmodified), `static/js/board.js`
  (full read — the `reportError`/`reportSuccess`/`renderErrorBanner` per-source pattern to mirror)

### Task 6 Context
- Spec: same file (BEH-3, BEH-4)
- Charter: capability: Create/edit/delete opportunity
- Source files: `static/js/deal.js` (from Task 5, full read — extend), `static/js/api.js`
  (export signatures: `updateOpportunity`, `deleteOpportunity`), `static/js/form-errors.js`
  (from Task 3, export signature: `inlineErrorMessage`)

### Task 7 Context
- Spec: same file (BEH-6)
- Charter: capability: Create/edit/delete contact
- Source files: `static/js/deal.js` (from Task 6, full read — extend), `static/js/api.js`
  (export signatures: `createContact`, `updateContact`, `deleteContact`), `static/js/list-state.js`
  (from Task 2, export signature: `replaceList`), `static/js/form-errors.js` (from Task 3, export
  signature: `inlineErrorMessage`)

### Task 8 Context
- Spec: same file (BEH-5)
- Charter: capability: Create/edit/delete opportunity
- Source files: `static/js/board.js` (from pipeline-board-view, full read — extend),
  `static/index.html` (full read — extend), `static/js/api.js` (export signature:
  `createOpportunity`), `static/js/form-errors.js` (export signature: `inlineErrorMessage`)

### Task 9 Context
- Spec: same file (BEH-7)
- Charter: capability: Create/edit/delete account
- Source files: `static/deal.html`, `static/accounts.html` conventions mirror each other — no
  additional source beyond the page-shell conventions already read in Task 4

### Task 10 Context
- Spec: same file (BEH-7, Error Cases table — 409 `ACCOUNT_HAS_DEPENDENTS`)
- Charter: capability: Create/edit/delete account
- Source files: `static/accounts.html` (from Task 9, full read), `static/js/api.js` (export
  signatures: `createAccount`, `updateAccount`, `deleteAccount`), `static/js/list-state.js`,
  `static/js/form-errors.js` (export signatures), `static/js/errors.js`, `static/js/error-state.js`
  (full read — reuse unmodified), `src/mock_salesforce/accounts.py` (signature only — the 409
  `ACCOUNT_HAS_DEPENDENTS` delete path)

### Task 11 Context
- Spec: same file (BEH-5's "or an Account's page" entry point; BEH-6's "or an Account's page"
  entry point)
- Charter: capability: Create/edit/delete opportunity; Create/edit/delete contact
- Source files: `static/accounts.html` (from Task 10, full read — extend), `static/js/accounts.js`
  (from Task 10, full read — extend), `static/js/api.js` (from Task 1, export signatures:
  `createOpportunity`, `fetchContacts`, `createContact`, `updateContact`, `deleteContact`),
  `static/js/list-state.js` (from Task 2, export signature: `replaceList`),
  `static/js/form-errors.js` (from Task 3, export signature: `inlineErrorMessage`)

### Task 12 Context
- Spec: same file (all behaviors — navigation is the connective tissue between them)
- Charter: capability: Deal detail page; Create/edit/delete account
- Source files: `static/index.html` (from Task 8, full read), `static/deal.html` (from Task 7,
  full read), `static/accounts.html` (from Task 9, full read)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty (`boundaries: []`), no
  rules to check

No ADRs, samples, or cross-cutting specs apply — none exist in this repo yet. No heuristics are
recorded for the `crm-ui` module (`adev heuristics retrieve --module crm-ui` returned `__NONE__`).

---

## Parallelization

- Group A (sequential): Task 1 → Task 8 (Task 8's create-opportunity form calls `createOpportunity`,
  added to `api.js` by Task 1)
- Group B (independent): Task 2 (no file overlap with any other group)
- Group C (independent): Task 3 (no file overlap with any other group)
- Group D (sequential): Task 4 → Task 5 → Task 6 → Task 7 (each extends the prior task's
  `static/deal.html` / `static/js/deal.js`)
- Group E (independent): Task 9 (no file overlap with any other group)

Groups B, C, D, and E can all run in parallel with Group A and with each other. Two tasks inside
Group D also reach across groups: Task 6 additionally depends on Task 3 (`inlineErrorMessage` for
the edit-opportunity form's inline error), and Task 7 additionally depends on Task 2
(`replaceList` for the contacts-list refresh) and Task 3. Task 8 additionally depends on Task 3
(`inlineErrorMessage` for the create-opportunity form). Task 10 depends on Task 1, Task 2, Task 3,
and Task 9 together and is not part of any group above. Task 11 depends on Task 1, Task 2, Task 3,
and Task 10 together (it extends the Accounts page Task 10 wires) and is not part of any group
above. Task 12 depends on Task 4, Task 8, Task 9, and Task 11 together, runs last, and is not
part of any group above.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Extend api.js with detail/CRUD fetch functions and ApiError | medium | unit | — | 0 create, 1 modify |
| 2 | Generic list-replace helper | small | unit | — | 2 create |
| 3 | Inline form-error message helper | small | unit | — | 2 create |
| 4 | Deal detail page shell (HTML) | medium | unit | — | 2 create |
| 5 | Deal detail fetch-and-render wiring | medium | unit | Task 1, Task 4 | 1 create/modify |
| 6 | Edit/delete opportunity forms | medium | unit | Task 3, Task 5 | 2 modify |
| 7 | Contact CRUD forms on the deal page | medium | unit | Task 2, Task 3, Task 6 | 2 modify |
| 8 | Board navigation to deal page + create-opportunity form | medium | unit | Task 1, Task 3 | 2 modify |
| 9 | Accounts list page shell (HTML) | small | unit | — | 2 create |
| 10 | Account CRUD forms (incl. 409 dependents) | medium | unit | Task 1, Task 2, Task 3, Task 9 | 1 create/modify |
| 11 | Create-opportunity + Contact CRUD from the Accounts page (2nd entry point) | medium | unit | Task 1, Task 2, Task 3, Task 10 | 2 modify |
| 12 | Cross-page navigation links | small | unit | Task 4, Task 8, Task 9, Task 11 | 2 modify |

Spec coverage: 8 of 8 behaviors mapped, with both spec-named entry points implemented for BEH-5
and BEH-6 (BEH-1 → Task 4/5/8; BEH-2 → Task 4/5; BEH-3 → Task 6; BEH-4 → Task 6; BEH-5 → Task 8
(board), Task 11 (Account's page); BEH-6 → Task 2/3/7 (deal page), Task 11 (Account's page);
BEH-7 → Task 3/9/10; BEH-8 → Task 5/6/7/8/10/11).

---

## Task Structure

### Task 1: Extend api.js with detail/CRUD fetch functions and ApiError [specialist: none]

**Charter capability:** Deal detail page; Create/edit/delete opportunity; Create/edit/delete
account; Create/edit/delete contact
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/api.js`
- Test: `static/js/api.test.mjs` (extend)

**Tests:** `static/js/api.test.mjs` — extend the existing suite (BEH-1 through BEH-7). The suite
already exists from the pipeline-board-view plan; add coverage for the new functions without
touching the existing tests.

**Context to load:**
- `src/mock_salesforce/models.py` (full read — all `*Out` field shapes)
- `src/mock_salesforce/opportunities.py`, `src/mock_salesforce/accounts.py`,
  `src/mock_salesforce/contacts.py` (signatures only — every CRUD route + status code)
- `src/mock_salesforce/errors.py` (full read — `{"error", "message"}` envelope)

- [ ] **Write failing test**

```javascript
import { ApiError, fetchOpportunity, fetchAccount, fetchContacts, createOpportunity,
  updateOpportunity, deleteOpportunity, deleteAccount, createContact } from './api.js';

test('fetchOpportunity calls GET /opportunities/{id}', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url) => {
    calls.push(url);
    return { ok: true, json: async () => ({ id: 5, name: 'Big Deal' }) };
  });
  const opp = await fetchOpportunity(5);
  assert.deepEqual(calls, ['/opportunities/5']);
  assert.equal(opp.name, 'Big Deal');
});

test('fetchAccount calls GET /accounts/{id}', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: true, json: async () => ({ id: 2, name: 'Acme' }) }));
  const account = await fetchAccount(2);
  assert.equal(account.name, 'Acme');
});

test('fetchContacts calls GET /contacts?account_id={id}', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url) => { calls.push(url); return { ok: true, json: async () => [] }; });
  await fetchContacts(2);
  assert.deepEqual(calls, ['/contacts?account_id=2']);
});

test('createOpportunity POSTs to /opportunities with the JSON payload', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return { ok: true, json: async () => ({ id: 9 }) };
  });
  await createOpportunity({ name: 'New Deal', account_id: 1, close_date: '2026-12-01' });
  assert.equal(calls[0].url, '/opportunities');
  assert.equal(calls[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].init.body), { name: 'New Deal', account_id: 1, close_date: '2026-12-01' });
});

test('updateOpportunity PATCHes /opportunities/{id}', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => { calls.push({ url, init }); return { ok: true, json: async () => ({ id: 9 }) }; });
  await updateOpportunity(9, { amount: 500 });
  assert.equal(calls[0].url, '/opportunities/9');
  assert.equal(calls[0].init.method, 'PATCH');
});

test('deleteOpportunity DELETEs /opportunities/{id} and resolves with null on a 204', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, '/opportunities/9');
    assert.equal(init.method, 'DELETE');
    return { ok: true, status: 204 };
  });
  assert.equal(await deleteOpportunity(9), null);
});

test('a non-2xx response surfaces the API\'s structured error message via ApiError', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({
    ok: false,
    status: 409,
    json: async () => ({ error: 'ACCOUNT_HAS_DEPENDENTS', message: 'Account 5 has 3 dependent record(s)' }),
  }));
  await assert.rejects(() => deleteAccount(5), (err) => {
    assert.ok(err instanceof ApiError);
    assert.equal(err.code, 'ACCOUNT_HAS_DEPENDENTS');
    assert.match(err.message, /3 dependent record\(s\)/);
    return true;
  });
});

test('a non-2xx response with no parseable JSON body falls back to the HTTP status', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: false, status: 500 }));
  await assert.rejects(() => createContact({ last_name: 'Doe', account_id: 1 }), /HTTP 500/);
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/api.test.mjs`
Expected: FAIL — `fetchOpportunity is not defined` (and the other new exports)

- [ ] **Implement**

Append to `static/js/api.js`:

```javascript
// --- Detail / CRUD extensions (deal-detail-and-crud-forms) ---
// Unlike fetchJson() above (which only surfaces the HTTP status), ApiError carries
// the API's structured {"error": code, "message": msg} envelope (see errors.py) so
// callers can show the exact validation-field or dependent-count message inline
// (BEH-7, BEH-8 Error Cases table) instead of a generic "HTTP 422" string.
export class ApiError extends Error {
  constructor(action, status, code, apiMessage) {
    super(apiMessage ? `Failed to ${action}: ${apiMessage}` : `Failed to ${action}: HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.apiMessage = apiMessage;
  }
}

async function request(url, options, action) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new Error(`Failed to ${action}: network error`);
  }
  if (!response.ok) {
    let body = null;
    try {
      body = await response.json();
    } catch (err) {
      // non-JSON or unreadable error body — fall back to the status code
    }
    throw new ApiError(action, response.status, body?.error ?? null, body?.message ?? null);
  }
  if (response.status === 204) return null;
  return response.json();
}

function jsonRequest(url, method, payload, action) {
  return request(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, action);
}

export function fetchOpportunity(id) {
  return request(`/opportunities/${id}`, undefined, 'load opportunity');
}

export function fetchAccount(id) {
  return request(`/accounts/${id}`, undefined, 'load account');
}

export function fetchContacts(accountId) {
  return request(`/contacts?account_id=${accountId}`, undefined, 'load contacts');
}

export function createOpportunity(payload) {
  return jsonRequest('/opportunities', 'POST', payload, 'create opportunity');
}

export function updateOpportunity(id, payload) {
  return jsonRequest(`/opportunities/${id}`, 'PATCH', payload, 'update opportunity');
}

export function deleteOpportunity(id) {
  return request(`/opportunities/${id}`, { method: 'DELETE' }, 'delete opportunity');
}

export function createAccount(payload) {
  return jsonRequest('/accounts', 'POST', payload, 'create account');
}

export function updateAccount(id, payload) {
  return jsonRequest(`/accounts/${id}`, 'PATCH', payload, 'update account');
}

export function deleteAccount(id) {
  return request(`/accounts/${id}`, { method: 'DELETE' }, 'delete account');
}

export function createContact(payload) {
  return jsonRequest('/contacts', 'POST', payload, 'create contact');
}

export function updateContact(id, payload) {
  return jsonRequest(`/contacts/${id}`, 'PATCH', payload, 'update contact');
}

export function deleteContact(id) {
  return request(`/contacts/${id}`, { method: 'DELETE' }, 'delete contact');
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/api.test.mjs`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/crm-ui/deal-detail-and-crud-forms`

```bash
git add static/js/api.js static/js/api.test.mjs
git commit -m "feat(crm-ui): add detail/CRUD fetch functions and structured ApiError to api.js"
```

---

### Task 2: Generic list-replace helper [specialist: none]

**Charter capability:** Create/edit/delete contact; Create/edit/delete account
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/list-state.js`
- Test: `static/js/list-state.test.mjs`

**Tests:** `static/js/list-state.test.mjs` — new suite (BEH-6, and the list-refresh half of
BEH-7). This is the first task touching this suite; create it.

**Context to load:**
- `static/js/board-state.js` (full read — the `replaceOpportunities` full-replace precedent)

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { replaceList } from './list-state.js';

test('replaceList fully replaces the prior list, never merges', () => {
  const prior = [{ id: 1 }];
  const next = replaceList(prior, [{ id: 2 }, { id: 3 }]);
  assert.deepEqual(next, [{ id: 2 }, { id: 3 }]);
});

test('replaceList returns an empty array when the next fetch has no results', () => {
  assert.deepEqual(replaceList([{ id: 1 }], []), []);
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/list-state.test.mjs`
Expected: FAIL — `Cannot find module './list-state.js'`

- [ ] **Implement**

```javascript
// Generic full-replace helper for any fetched list (Contacts, Accounts) — mirrors
// board-state.js's replaceOpportunities semantics: a refreshed list must never
// merge with a stale one (same invariant the pipeline board's Account filter
// switch already enforces).
export function replaceList(_prior, next) {
  return next;
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/list-state.test.mjs`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/list-state.js static/js/list-state.test.mjs
git commit -m "feat(crm-ui): add generic list-replace helper for Contacts/Accounts refresh"
```

---

### Task 3: Inline form-error message helper [specialist: none]

**Charter capability:** Create/edit/delete opportunity; Create/edit/delete account;
Create/edit/delete contact
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/form-errors.js`
- Test: `static/js/form-errors.test.mjs`

**Tests:** `static/js/form-errors.test.mjs` — new suite (BEH-7, Error Cases table — 422/409
inline display). This is the first task touching this suite; create it. Tested against plain
object fixtures (no import of `api.js`), so this task has no dependency on Task 1.

**Context to load:**
- None beyond the spec's Error Cases table — this is a pure function over the `{message,
  apiMessage}` shape Task 1 will attach to `ApiError`.

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { inlineErrorMessage } from './form-errors.js';

test('prefers the structured API message (e.g. a 422 field error) when present', () => {
  const err = { message: 'Failed to create contact: last_name: field required', apiMessage: 'last_name: field required' };
  assert.equal(inlineErrorMessage(err), 'last_name: field required');
});

test('prefers the structured API message for a 409 dependent-count error', () => {
  const err = { message: 'Failed to delete account: Account 5 has 3 dependent record(s)', apiMessage: 'Account 5 has 3 dependent record(s)' };
  assert.equal(inlineErrorMessage(err), 'Account 5 has 3 dependent record(s)');
});

test('falls back to the generic error message when no apiMessage is present', () => {
  const err = new Error('Failed to create contact: network error');
  assert.equal(inlineErrorMessage(err), 'Failed to create contact: network error');
});

test('never returns an empty string for an unrecognized error shape', () => {
  assert.equal(inlineErrorMessage(null), 'unknown error');
  assert.equal(inlineErrorMessage(undefined), 'unknown error');
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/form-errors.test.mjs`
Expected: FAIL — `Cannot find module './form-errors.js'`

- [ ] **Implement**

```javascript
// Picks the most specific message available for an inline form error: the API's
// own structured message (already names the offending field for a 422, or the
// dependent count for a 409 — see errors.py/accounts.py) when present, falling
// back to the error's generic message otherwise. Never returns an empty string.
export function inlineErrorMessage(error) {
  if (error && typeof error.apiMessage === 'string' && error.apiMessage.length > 0) {
    return error.apiMessage;
  }
  if (error && typeof error.message === 'string' && error.message.length > 0) {
    return error.message;
  }
  return 'unknown error';
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/form-errors.test.mjs`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/form-errors.js static/js/form-errors.test.mjs
git commit -m "feat(crm-ui): add inline form-error message helper"
```

---

### Task 4: Deal detail page shell (HTML) [specialist: none]

**Charter capability:** Deal detail page
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/deal.html`
- Test: `tests/test_ui_deal_page.py`

**Tests:** `tests/test_ui_deal_page.py` — new suite. This is the first task touching this suite;
create it. Covers the structural preconditions for BEH-1/BEH-2 — the exact DOM hooks Task 5's
`deal.js` will bind against (`getElementById` with no fallback), following
`test_ui_board_page.py`'s convention of asserting precise ids, not just "a heading exists
somewhere".

**Context to load:**
- `static/index.html` (from pipeline-board-view, full read — page-shell conventions to mirror:
  stylesheet `<link>`, `type="module"` script, `#error-banner`)

- [ ] **Write failing test**

```python
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_deal_html_has_the_detail_dom_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/deal.html")
        assert response.status_code == 200
        html = response.text
        # These exact ids are the DOM contract Task 5's deal.js binds against
        # (getElementById with no fallback) — asserting only "a heading exists
        # somewhere" would let this task pass without the hooks Task 5 needs.
        assert 'id="opportunity-name"' in html
        assert 'id="opportunity-fields"' in html
        assert 'id="account-fields"' in html
        assert 'id="contacts-list"' in html
        assert 'id="error-banner"' in html
        assert 'type="module"' in html
        assert 'js/deal.js' in html
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: FAIL — `static/deal.html` does not exist yet

- [ ] **Implement**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Deal Detail</title>
  <link rel="stylesheet" href="css/board.css" />
</head>
<body>
  <header>
    <a href="index.html">&larr; Back to board</a>
  </header>
  <div id="error-banner" role="alert" hidden></div>
  <main id="deal-detail">
    <section id="opportunity-section">
      <h1 id="opportunity-name"></h1>
      <dl id="opportunity-fields"></dl>
    </section>
    <section id="account-summary">
      <h2>Account</h2>
      <dl id="account-fields"></dl>
    </section>
    <section id="contacts-section">
      <h2>Contacts</h2>
      <ul id="contacts-list"></ul>
    </section>
  </main>
  <script type="module" src="js/deal.js"></script>
</body>
</html>
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/deal.html tests/test_ui_deal_page.py
git commit -m "feat(crm-ui): add deal detail page shell"
```

---

### Task 5: Deal detail fetch-and-render wiring [specialist: none]

**Depends on:** Task 1, Task 4
**Charter capability:** Deal detail page
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/deal.js`
- Test: `tests/test_ui_deal_page.py` (extend)

**Tests:** `tests/test_ui_deal_page.py` — extend the suite from Task 4 with a structural
js-serving assertion, mirroring `test_ui_board_page.py`'s `test_board_js_wires_the_per_source_error_state_module`:
confirms `deal.js` fetches all three resources and reuses `error-state.js`/`errors.js` rather
than reintroducing its own error tracking.

**Context to load:**
- `static/js/api.js` (from Task 1, export signatures: `fetchOpportunity`, `fetchAccount`,
  `fetchContacts`), `static/js/error-state.js`, `static/js/errors.js` (full read — reuse
  unmodified), `static/js/board.js` (full read — the `reportError`/`reportSuccess` pattern to
  mirror)

- [ ] **Write failing test**

Append to `tests/test_ui_deal_page.py`:

```python
def test_deal_js_is_served_and_fetches_opportunity_account_and_contacts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/deal.js")
        assert response.status_code == 200
        js = response.text
        assert "fetchOpportunity" in js
        assert "fetchAccount" in js
        assert "fetchContacts" in js
        assert "from './error-state.js'" in js
        assert "from './errors.js'" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: FAIL — 404 `STATIC_ASSET_NOT_FOUND`, `static/js/deal.js` does not exist yet

- [ ] **Implement**

```javascript
import { fetchOpportunity, fetchAccount, fetchContacts } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';

const errorBanner = document.getElementById('error-banner');
const opportunityName = document.getElementById('opportunity-name');
const opportunityFields = document.getElementById('opportunity-fields');
const accountFields = document.getElementById('account-fields');
const contactsList = document.getElementById('contacts-list');

let errorState = new Map();
let opportunity = null;
let account = null;
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

function field(dl, label, value) {
  const dt = document.createElement('dt');
  dt.textContent = label;
  const dd = document.createElement('dd');
  dd.textContent = value == null || value === '' ? '—' : String(value);
  dl.appendChild(dt);
  dl.appendChild(dd);
}

function renderOpportunity() {
  opportunityName.textContent = opportunity.name;
  opportunityFields.innerHTML = '';
  field(opportunityFields, 'Stage', opportunity.stage_name);
  field(opportunityFields, 'Amount', opportunity.amount);
  field(opportunityFields, 'Close date', opportunity.close_date);
  field(opportunityFields, 'Probability', opportunity.probability);
  field(opportunityFields, 'Type', opportunity.opportunity_type);
  field(opportunityFields, 'Lead source', opportunity.lead_source);
  field(opportunityFields, 'Next step', opportunity.next_step);
  field(opportunityFields, 'Closed', opportunity.is_closed);
  field(opportunityFields, 'Won', opportunity.is_won);
}

function renderAccount() {
  accountFields.innerHTML = '';
  field(accountFields, 'Name', account.name);
  field(accountFields, 'Industry', account.industry);
  field(accountFields, 'Phone', account.phone);
}

function renderContacts() {
  contactsList.innerHTML = '';
  for (const contact of contacts) {
    const li = document.createElement('li');
    li.dataset.contactId = contact.id;
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
    li.textContent = `${name} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    contactsList.appendChild(li);
  }
}

function getOpportunityId() {
  return new URLSearchParams(window.location.search).get('id');
}

async function loadDetail() {
  const id = getOpportunityId();
  try {
    opportunity = await fetchOpportunity(id);
    reportSuccess('opportunity');
    renderOpportunity();
  } catch (err) {
    reportError('opportunity', describeApiError('load opportunity', err));
    return;
  }
  try {
    account = await fetchAccount(opportunity.account_id);
    reportSuccess('account');
    renderAccount();
  } catch (err) {
    reportError('account', describeApiError('load account', err));
  }
  try {
    contacts = await fetchContacts(opportunity.account_id);
    reportSuccess('contacts');
    renderContacts();
  } catch (err) {
    reportError('contacts', describeApiError('load contacts', err));
  }
}

loadDetail();
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/deal.js tests/test_ui_deal_page.py
git commit -m "feat(crm-ui): wire deal detail fetch-and-render (Opportunity, Account, Contacts)"
```

---

### Task 6: Edit/delete opportunity forms [specialist: none]

**Depends on:** Task 3, Task 5
**Charter capability:** Create/edit/delete opportunity
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/deal.html` (add edit-opportunity form + delete button)
- Modify: `static/js/deal.js` (wire PATCH/DELETE)
- Test: `tests/test_ui_deal_page.py` (extend)

**Tests:** `tests/test_ui_deal_page.py` — extend the suite from Task 5. Covers BEH-3 (PATCH +
re-render from the response) and BEH-4 (DELETE + navigate to the board), plus BEH-8's inline
error path via `form-errors.js`.

**Context to load:**
- `static/js/deal.js` (from Task 5, full read — extend), `static/js/api.js` (export signatures:
  `updateOpportunity`, `deleteOpportunity`), `static/js/form-errors.js` (export signature:
  `inlineErrorMessage`)

- [ ] **Write failing test**

Append to `tests/test_ui_deal_page.py`:

```python
def test_deal_js_wires_edit_and_delete_opportunity(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'id="edit-opportunity-form"' in html
        assert 'id="delete-opportunity-btn"' in html

        js = client.get("/js/deal.js").text
        assert "updateOpportunity" in js
        assert "deleteOpportunity" in js
        assert "inlineErrorMessage" in js
        assert "confirm(" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: FAIL — `edit-opportunity-form`/`delete-opportunity-btn` not present, `deal.js` does not
reference `updateOpportunity`/`deleteOpportunity`/`inlineErrorMessage` yet

- [ ] **Implement**

Add inside `#opportunity-section` in `static/deal.html`:

```html
      <button id="edit-opportunity-btn" type="button">Edit</button>
      <button id="delete-opportunity-btn" type="button">Delete</button>
      <form id="edit-opportunity-form" hidden>
        <div id="edit-opportunity-error" class="form-error" role="alert"></div>
        <label for="opp-name-input">Name</label>
        <input id="opp-name-input" name="name" type="text" required />
        <label for="opp-amount-input">Amount</label>
        <input id="opp-amount-input" name="amount" type="number" step="0.01" />
        <label for="opp-close-date-input">Close date</label>
        <input id="opp-close-date-input" name="close_date" type="date" required />
        <button type="submit">Save</button>
        <button type="button" id="cancel-edit-opportunity-btn">Cancel</button>
      </form>
```

Append to `static/js/deal.js` (add `updateOpportunity, deleteOpportunity` to the existing `./api.js`
import, and `inlineErrorMessage` from a new `./form-errors.js` import):

```javascript
import { inlineErrorMessage } from './form-errors.js';

const editBtn = document.getElementById('edit-opportunity-btn');
const deleteBtn = document.getElementById('delete-opportunity-btn');
const editForm = document.getElementById('edit-opportunity-form');
const editError = document.getElementById('edit-opportunity-error');
const cancelEditBtn = document.getElementById('cancel-edit-opportunity-btn');

function openEditForm() {
  editForm.elements.name.value = opportunity.name;
  editForm.elements.amount.value = opportunity.amount ?? '';
  editForm.elements.close_date.value = opportunity.close_date;
  editError.textContent = '';
  editForm.hidden = false;
}

editBtn.addEventListener('click', openEditForm);
cancelEditBtn.addEventListener('click', () => { editForm.hidden = true; });

editForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    name: editForm.elements.name.value,
    amount: editForm.elements.amount.value === '' ? null : Number(editForm.elements.amount.value),
    close_date: editForm.elements.close_date.value,
  };
  try {
    opportunity = await updateOpportunity(opportunity.id, payload);
    editForm.hidden = true;
    reportSuccess('opportunity');
    renderOpportunity();
  } catch (err) {
    editError.textContent = inlineErrorMessage(err);
  }
});

deleteBtn.addEventListener('click', async () => {
  if (!window.confirm('Delete this opportunity?')) return;
  try {
    await deleteOpportunity(opportunity.id);
    window.location.href = 'index.html';
  } catch (err) {
    reportError('opportunity', describeApiError('delete opportunity', err));
  }
});
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/deal.html static/js/deal.js tests/test_ui_deal_page.py
git commit -m "feat(crm-ui): wire edit/delete opportunity forms on the deal detail page"
```

---

### Task 7: Contact CRUD forms on the deal page [specialist: none]

**Depends on:** Task 2, Task 3, Task 6
**Charter capability:** Create/edit/delete contact
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/deal.html` (add contact create/edit form)
- Modify: `static/js/deal.js` (wire Contact CRUD + list refresh)
- Test: `tests/test_ui_deal_page.py` (extend)

**Tests:** `tests/test_ui_deal_page.py` — extend the suite from Task 6. Covers BEH-6: every
Contact CRUD action refreshes the related-Contacts list via `replaceList` (never merges a stale
list with a fresh one) rather than splicing the mutated contact in locally.

**Context to load:**
- `static/js/deal.js` (from Task 6, full read — extend), `static/js/api.js` (export signatures:
  `createContact`, `updateContact`, `deleteContact`), `static/js/list-state.js` (export
  signature: `replaceList`), `static/js/form-errors.js` (export signature: `inlineErrorMessage`)

- [ ] **Write failing test**

Append to `tests/test_ui_deal_page.py`:

```python
def test_deal_js_wires_contact_crud_and_list_refresh(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'id="contact-form"' in html
        assert 'id="new-contact-btn"' in html

        js = client.get("/js/deal.js").text
        assert "createContact" in js
        assert "updateContact" in js
        assert "deleteContact" in js
        assert "from './list-state.js'" in js
        assert "replaceList" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: FAIL — `contact-form`/`new-contact-btn` not present, `deal.js` does not reference the
Contact CRUD functions or `replaceList` yet

- [ ] **Implement**

Add inside `#contacts-section` in `static/deal.html`:

```html
      <button id="new-contact-btn" type="button">New contact</button>
      <form id="contact-form" hidden>
        <input type="hidden" id="contact-id-input" />
        <div id="contact-form-error" class="form-error" role="alert"></div>
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
```

Replace `renderContacts()` and append the rest to `static/js/deal.js` (add `createContact,
updateContact, deleteContact` to the `./api.js` import, and a new `./list-state.js` import):

```javascript
import { replaceList } from './list-state.js';

const newContactBtn = document.getElementById('new-contact-btn');
const contactForm = document.getElementById('contact-form');
const contactFormError = document.getElementById('contact-form-error');
const contactIdInput = document.getElementById('contact-id-input');
const cancelContactBtn = document.getElementById('cancel-contact-form-btn');

function renderContacts() {
  contactsList.innerHTML = '';
  for (const contact of contacts) {
    const li = document.createElement('li');
    li.dataset.contactId = contact.id;
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
    const summary = document.createElement('span');
    summary.textContent = `${name} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-contact-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openContactForm(contact));
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'delete-contact-btn';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', () => removeContact(contact.id));
    li.append(summary, editBtn, removeBtn);
    contactsList.appendChild(li);
  }
}

function openContactForm(contact) {
  contactIdInput.value = contact ? contact.id : '';
  contactForm.elements.first_name.value = contact?.first_name ?? '';
  contactForm.elements.last_name.value = contact?.last_name ?? '';
  contactForm.elements.email.value = contact?.email ?? '';
  contactForm.elements.title.value = contact?.title ?? '';
  contactFormError.textContent = '';
  contactForm.hidden = false;
}

newContactBtn.addEventListener('click', () => openContactForm(null));
cancelContactBtn.addEventListener('click', () => { contactForm.hidden = true; });

async function refreshContacts() {
  contacts = replaceList(contacts, await fetchContacts(opportunity.account_id));
  renderContacts();
}

contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: opportunity.account_id,
    first_name: contactForm.elements.first_name.value || null,
    last_name: contactForm.elements.last_name.value,
    email: contactForm.elements.email.value || null,
    title: contactForm.elements.title.value || null,
  };
  try {
    if (contactIdInput.value) {
      await updateContact(contactIdInput.value, payload);
    } else {
      await createContact(payload);
    }
    contactForm.hidden = true;
    await refreshContacts();
    reportSuccess('contacts');
  } catch (err) {
    contactFormError.textContent = inlineErrorMessage(err);
  }
});

async function removeContact(id) {
  if (!window.confirm('Delete this contact?')) return;
  try {
    await deleteContact(id);
    await refreshContacts();
    reportSuccess('contacts');
  } catch (err) {
    reportError('contacts', describeApiError('delete contact', err));
  }
}
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_deal_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/deal.html static/js/deal.js tests/test_ui_deal_page.py
git commit -m "feat(crm-ui): wire contact CRUD forms and related-list refresh on the deal page"
```

---

### Task 8: Board navigation to deal page + create-opportunity form [specialist: none]

**Depends on:** Task 1, Task 3
**Charter capability:** Create/edit/delete opportunity
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (add "+ New opportunity" button + form)
- Modify: `static/js/board.js` (card click → navigate; wire create form)
- Test: `tests/test_ui_board_page.py` (extend)

**Tests:** `tests/test_ui_board_page.py` — extend the existing suite (from pipeline-board-view).
Covers BEH-1's navigation trigger (opening a card) and BEH-5 (create-opportunity form →
`POST /opportunities` → navigate to the new deal's detail page).

**Context to load:**
- `static/js/board.js`, `static/index.html` (from pipeline-board-view, full read — extend),
  `static/js/api.js` (export signature: `createOpportunity`), `static/js/form-errors.js`
  (export signature: `inlineErrorMessage`)

- [ ] **Write failing test**

Append to `tests/test_ui_board_page.py`:

```python
def test_board_js_wires_create_opportunity_and_card_navigation(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text
        assert 'id="new-opportunity-btn"' in html
        assert 'id="create-opportunity-form"' in html

        js = client.get("/js/board.js").text
        assert "createOpportunity" in js
        assert "deal.html?id=" in js
        assert "from './form-errors.js'" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: FAIL — `new-opportunity-btn`/`create-opportunity-form` not present, `board.js` does not
reference `createOpportunity`/`deal.html?id=`/`form-errors.js` yet

- [ ] **Implement**

Add to `static/index.html` (a "+ New opportunity" button in the header, and a form after it):

```html
    <button id="new-opportunity-btn" type="button">+ New opportunity</button>
  </header>
  <form id="create-opportunity-form" hidden>
    <div id="create-opportunity-error" class="form-error" role="alert"></div>
    <label for="new-opp-account-select">Account</label>
    <select id="new-opp-account-select" name="account_id" required></select>
    <label for="new-opp-name-input">Name</label>
    <input id="new-opp-name-input" name="name" type="text" required />
    <label for="new-opp-close-date-input">Close date</label>
    <input id="new-opp-close-date-input" name="close_date" type="date" required />
    <button type="submit">Create</button>
    <button type="button" id="cancel-create-opportunity-btn">Cancel</button>
  </form>
```

Append to `static/js/board.js` (add `createOpportunity` to the `./api.js` import, and a new
`./form-errors.js` import; extend `loadAccounts()` to also populate `accountSelect`; add a click
listener on each card):

```javascript
import { inlineErrorMessage } from './form-errors.js';

const newOppBtn = document.getElementById('new-opportunity-btn');
const createForm = document.getElementById('create-opportunity-form');
const createError = document.getElementById('create-opportunity-error');
const cancelCreateBtn = document.getElementById('cancel-create-opportunity-btn');
const accountSelect = document.getElementById('new-opp-account-select');

newOppBtn.addEventListener('click', () => { createError.textContent = ''; createForm.hidden = false; });
cancelCreateBtn.addEventListener('click', () => { createForm.hidden = true; });

createForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: Number(accountSelect.value),
    name: createForm.elements.name.value,
    close_date: createForm.elements.close_date.value,
  };
  try {
    const created = await createOpportunity(payload);
    window.location.href = `deal.html?id=${created.id}`;
  } catch (err) {
    createError.textContent = inlineErrorMessage(err);
  }
});
```

In `loadAccounts()`, alongside the existing `switcher` option-population loop, also populate
`accountSelect`:

```javascript
    for (const account of accounts) {
      const switcherOption = document.createElement('option');
      switcherOption.value = account.id;
      switcherOption.textContent = account.name;
      switcher.appendChild(switcherOption);

      const createOption = document.createElement('option');
      createOption.value = account.id;
      createOption.textContent = account.name;
      accountSelect.appendChild(createOption);
    }
```

In `render()`, add a click listener to each card (kept distinct from the existing `dragstart`
listener, which only records `draggedId` for the stage-move gesture):

```javascript
      card.addEventListener('click', () => { window.location.href = `deal.html?id=${opp.id}`; });
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board.js tests/test_ui_board_page.py
git commit -m "feat(crm-ui): wire card-to-deal navigation and create-opportunity form on the board"
```

---

### Task 9: Accounts list page shell (HTML) [specialist: none]

**Charter capability:** Create/edit/delete account
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/accounts.html`
- Test: `tests/test_ui_accounts_page.py`

**Tests:** `tests/test_ui_accounts_page.py` — new suite. This is the first task touching this
suite; create it. Covers the structural precondition for BEH-7 — the exact DOM hooks Task 10's
`accounts.js` will bind against.

**Context to load:**
- `static/deal.html` (from Task 4, full read — the page-shell convention this page mirrors)

- [ ] **Write failing test**

```python
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_accounts_html_has_the_list_and_form_dom_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/accounts.html")
        assert response.status_code == 200
        html = response.text
        assert 'id="accounts-list"' in html
        assert 'id="new-account-btn"' in html
        assert 'id="account-form"' in html
        assert 'id="error-banner"' in html
        assert 'type="module"' in html
        assert 'js/accounts.js' in html
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: FAIL — `static/accounts.html` does not exist yet

- [ ] **Implement**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Accounts</title>
  <link rel="stylesheet" href="css/board.css" />
</head>
<body>
  <header>
    <a href="index.html">&larr; Back to board</a>
  </header>
  <div id="error-banner" role="alert" hidden></div>
  <main id="accounts-page">
    <h1>Accounts</h1>
    <ul id="accounts-list"></ul>
    <button id="new-account-btn" type="button">New account</button>
    <form id="account-form" hidden>
      <input type="hidden" id="account-id-input" />
      <div id="account-form-error" class="form-error" role="alert"></div>
      <label for="account-name-input">Name</label>
      <input id="account-name-input" name="name" type="text" required />
      <label for="account-industry-input">Industry</label>
      <input id="account-industry-input" name="industry" type="text" />
      <label for="account-phone-input">Phone</label>
      <input id="account-phone-input" name="phone" type="text" />
      <button type="submit">Save account</button>
      <button type="button" id="cancel-account-form-btn">Cancel</button>
    </form>
  </main>
  <script type="module" src="js/accounts.js"></script>
</body>
</html>
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/accounts.html tests/test_ui_accounts_page.py
git commit -m "feat(crm-ui): add accounts list page shell"
```

---

### Task 10: Account CRUD forms (incl. 409 dependents) [specialist: none]

**Depends on:** Task 1, Task 2, Task 3, Task 9
**Charter capability:** Create/edit/delete account
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/accounts.js`
- Test: `tests/test_ui_accounts_page.py` (extend)

**Tests:** `tests/test_ui_accounts_page.py` — extend the suite from Task 9. Covers BEH-7 in
full, including the 409 `ACCOUNT_HAS_DEPENDENTS` inline case: the account must stay in the
list/UI (never removed) on a failed delete.

**Context to load:**
- `static/accounts.html` (from Task 9, full read), `static/js/api.js` (export signatures:
  `createAccount`, `updateAccount`, `deleteAccount`), `static/js/list-state.js`,
  `static/js/form-errors.js` (export signatures), `static/js/errors.js`,
  `static/js/error-state.js` (full read — reuse unmodified), `src/mock_salesforce/accounts.py`
  (signature only — the 409 `ACCOUNT_HAS_DEPENDENTS` delete path)

- [ ] **Write failing test**

Append to `tests/test_ui_accounts_page.py`:

```python
def test_accounts_js_wires_crud_and_409_dependents_handling(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/accounts.js")
        assert response.status_code == 200
        js = response.text
        assert "createAccount" in js
        assert "updateAccount" in js
        assert "deleteAccount" in js
        assert "from './list-state.js'" in js
        assert "from './form-errors.js'" in js
        assert "from './error-state.js'" in js
        assert "confirm(" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: FAIL — 404 `STATIC_ASSET_NOT_FOUND`, `static/js/accounts.js` does not exist yet

- [ ] **Implement**

```javascript
import { fetchAccounts, createAccount, updateAccount, deleteAccount } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';
import { inlineErrorMessage } from './form-errors.js';

const errorBanner = document.getElementById('error-banner');
const accountsList = document.getElementById('accounts-list');
const newAccountBtn = document.getElementById('new-account-btn');
const accountForm = document.getElementById('account-form');
const accountFormError = document.getElementById('account-form-error');
const accountIdInput = document.getElementById('account-id-input');
const cancelAccountBtn = document.getElementById('cancel-account-form-btn');

let errorState = new Map();
let accounts = [];

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

function openAccountForm(account) {
  accountIdInput.value = account ? account.id : '';
  accountForm.elements.name.value = account?.name ?? '';
  accountForm.elements.industry.value = account?.industry ?? '';
  accountForm.elements.phone.value = account?.phone ?? '';
  accountFormError.textContent = '';
  accountForm.hidden = false;
}

function renderAccounts() {
  accountsList.innerHTML = '';
  for (const account of accounts) {
    const li = document.createElement('li');
    li.dataset.accountId = account.id;
    const summary = document.createElement('span');
    summary.textContent = `${account.name} — ${account.industry ?? ''} — ${account.phone ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-account-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openAccountForm(account));
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'delete-account-btn';
    deleteBtn.textContent = 'Delete';
    const dependentsMessage = document.createElement('span');
    dependentsMessage.className = 'account-delete-error';
    deleteBtn.addEventListener('click', async () => {
      if (!window.confirm(`Delete account "${account.name}"?`)) return;
      dependentsMessage.textContent = '';
      try {
        await deleteAccount(account.id);
        await refreshAccounts();
        reportSuccess('accounts');
      } catch (err) {
        // BEH-7: a 409 ACCOUNT_HAS_DEPENDENTS must show inline, naming the
        // dependent count, and the Account must stay in the list — never
        // removed on a failed delete.
        dependentsMessage.textContent = inlineErrorMessage(err);
      }
    });
    li.append(summary, editBtn, deleteBtn, dependentsMessage);
    accountsList.appendChild(li);
  }
}

async function refreshAccounts() {
  accounts = replaceList(accounts, await fetchAccounts());
  renderAccounts();
}

newAccountBtn.addEventListener('click', () => openAccountForm(null));
cancelAccountBtn.addEventListener('click', () => { accountForm.hidden = true; });

accountForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    name: accountForm.elements.name.value,
    industry: accountForm.elements.industry.value || null,
    phone: accountForm.elements.phone.value || null,
  };
  try {
    if (accountIdInput.value) {
      await updateAccount(accountIdInput.value, payload);
    } else {
      await createAccount(payload);
    }
    accountForm.hidden = true;
    await refreshAccounts();
    reportSuccess('accounts');
  } catch (err) {
    accountFormError.textContent = inlineErrorMessage(err);
  }
});

async function init() {
  try {
    await refreshAccounts();
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('load accounts', err));
  }
}

init();
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/accounts.js tests/test_ui_accounts_page.py
git commit -m "feat(crm-ui): wire account CRUD forms with inline 409 dependents handling"
```

---

### Task 11: Create-opportunity + Contact CRUD from the Accounts page (2nd entry point) [specialist: none]

**Depends on:** Task 1, Task 2, Task 3, Task 10
**Charter capability:** Create/edit/delete opportunity; Create/edit/delete contact
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/accounts.html` (add per-account "New opportunity" form + Contacts sub-list +
  contact form)
- Modify: `static/js/accounts.js` (wire create-opportunity and Contact CRUD per account)
- Test: `tests/test_ui_accounts_page.py` (extend)

**Tests:** `tests/test_ui_accounts_page.py` — extend the suite from Task 10. The spec names two
valid entry points for BEH-5 ("from the board or an Account's page") and BEH-6 ("from the deal
detail page's related-Contacts list, or an Account's page"); Task 8 and Task 7 covered the first
entry point for each — this task covers the second, so that submitting either form from either
named location satisfies the same behavior (same `POST /opportunities` / Contact CRUD endpoints,
same success outcome).

**Context to load:**
- `static/accounts.html` (from Task 10, full read — extend), `static/js/accounts.js` (from Task
  10, full read — extend), `static/js/api.js` (export signatures: `createOpportunity`,
  `fetchContacts`, `createContact`, `updateContact`, `deleteContact`), `static/js/list-state.js`
  (export signature: `replaceList`), `static/js/form-errors.js` (export signature:
  `inlineErrorMessage`)

- [ ] **Write failing test**

Append to `tests/test_ui_accounts_page.py`:

```python
def test_accounts_js_wires_new_opportunity_and_contact_crud_per_account(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/accounts.html").text
        assert 'id="account-new-opportunity-form"' in html
        assert 'id="account-contact-form"' in html

        js = client.get("/js/accounts.js").text
        assert "createOpportunity" in js
        assert "fetchContacts" in js
        assert "createContact" in js
        assert "updateContact" in js
        assert "deleteContact" in js
        assert "deal.html?id=" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: FAIL — `account-new-opportunity-form`/`account-contact-form` not present, `accounts.js`
does not reference `createOpportunity`/`fetchContacts`/Contact CRUD/`deal.html?id=` yet

- [ ] **Implement**

Add to `static/accounts.html`, after the existing `#account-form`:

```html
    <form id="account-new-opportunity-form" hidden>
      <input type="hidden" id="new-opp-for-account-id" />
      <div id="account-new-opportunity-error" class="form-error" role="alert"></div>
      <label for="account-new-opp-name-input">Name</label>
      <input id="account-new-opp-name-input" name="name" type="text" required />
      <label for="account-new-opp-close-date-input">Close date</label>
      <input id="account-new-opp-close-date-input" name="close_date" type="date" required />
      <button type="submit">Create opportunity</button>
      <button type="button" id="cancel-account-new-opportunity-btn">Cancel</button>
    </form>
    <form id="account-contact-form" hidden>
      <input type="hidden" id="account-contact-id-input" />
      <input type="hidden" id="account-contact-account-id-input" />
      <div id="account-contact-form-error" class="form-error" role="alert"></div>
      <label for="account-contact-first-name-input">First name</label>
      <input id="account-contact-first-name-input" name="first_name" type="text" />
      <label for="account-contact-last-name-input">Last name</label>
      <input id="account-contact-last-name-input" name="last_name" type="text" required />
      <label for="account-contact-email-input">Email</label>
      <input id="account-contact-email-input" name="email" type="email" />
      <label for="account-contact-title-input">Title</label>
      <input id="account-contact-title-input" name="title" type="text" />
      <button type="submit">Save contact</button>
      <button type="button" id="cancel-account-contact-form-btn">Cancel</button>
    </form>
```

Append to `static/js/accounts.js` (add `createOpportunity, fetchContacts, createContact,
updateContact, deleteContact` to the existing `./api.js` import from Task 10 — the import
becomes `import { fetchAccounts, createAccount, updateAccount, deleteAccount, createOpportunity,
fetchContacts, createContact, updateContact, deleteContact } from './api.js';`; extend
`renderAccounts()` with a per-account "New opportunity" button and an expandable Contacts
sub-list):

```javascript
import { createOpportunity, fetchContacts, createContact, updateContact, deleteContact } from './api.js';

const newOppForm = document.getElementById('account-new-opportunity-form');
const newOppError = document.getElementById('account-new-opportunity-error');
const newOppAccountIdInput = document.getElementById('new-opp-for-account-id');
const cancelNewOppBtn = document.getElementById('cancel-account-new-opportunity-btn');

const accountContactForm = document.getElementById('account-contact-form');
const accountContactFormError = document.getElementById('account-contact-form-error');
const accountContactIdInput = document.getElementById('account-contact-id-input');
const accountContactAccountIdInput = document.getElementById('account-contact-account-id-input');
const cancelAccountContactBtn = document.getElementById('cancel-account-contact-form-btn');

const accountContactsCache = new Map();

function openNewOpportunityForm(account) {
  newOppAccountIdInput.value = account.id;
  newOppForm.elements.name.value = '';
  newOppForm.elements.close_date.value = '';
  newOppError.textContent = '';
  newOppForm.hidden = false;
}

cancelNewOppBtn.addEventListener('click', () => { newOppForm.hidden = true; });

newOppForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: Number(newOppAccountIdInput.value),
    name: newOppForm.elements.name.value,
    close_date: newOppForm.elements.close_date.value,
  };
  try {
    const created = await createOpportunity(payload);
    window.location.href = `deal.html?id=${created.id}`;
  } catch (err) {
    newOppError.textContent = inlineErrorMessage(err);
  }
});

function openAccountContactForm(accountId, contact) {
  accountContactAccountIdInput.value = accountId;
  accountContactIdInput.value = contact ? contact.id : '';
  accountContactForm.elements.first_name.value = contact?.first_name ?? '';
  accountContactForm.elements.last_name.value = contact?.last_name ?? '';
  accountContactForm.elements.email.value = contact?.email ?? '';
  accountContactForm.elements.title.value = contact?.title ?? '';
  accountContactFormError.textContent = '';
  accountContactForm.hidden = false;
}

cancelAccountContactBtn.addEventListener('click', () => { accountContactForm.hidden = true; });

async function renderAccountContacts(accountId, listEl) {
  const prior = accountContactsCache.get(accountId) ?? [];
  const next = replaceList(prior, await fetchContacts(accountId));
  accountContactsCache.set(accountId, next);
  listEl.innerHTML = '';
  for (const contact of next) {
    const li = document.createElement('li');
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
    const summary = document.createElement('span');
    summary.textContent = `${name} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-account-contact-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openAccountContactForm(accountId, contact));
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'delete-account-contact-btn';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', async () => {
      if (!window.confirm('Delete this contact?')) return;
      try {
        await deleteContact(contact.id);
        await renderAccountContacts(accountId, listEl);
      } catch (err) {
        reportError('contacts', describeApiError('delete contact', err));
      }
    });
    li.append(summary, editBtn, removeBtn);
    listEl.appendChild(li);
  }
}

accountContactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const accountId = Number(accountContactAccountIdInput.value);
  const payload = {
    account_id: accountId,
    first_name: accountContactForm.elements.first_name.value || null,
    last_name: accountContactForm.elements.last_name.value,
    email: accountContactForm.elements.email.value || null,
    title: accountContactForm.elements.title.value || null,
  };
  const listEl = accountsList.querySelector(`.account-contacts-list[data-account-id="${accountId}"]`);
  try {
    if (accountContactIdInput.value) {
      await updateContact(accountContactIdInput.value, payload);
    } else {
      await createContact(payload);
    }
    accountContactForm.hidden = true;
    if (listEl) await renderAccountContacts(accountId, listEl);
  } catch (err) {
    accountContactFormError.textContent = inlineErrorMessage(err);
  }
});
```

Extend `renderAccounts()` (from Task 10) to add, per account row, a "New opportunity" button and
an expandable Contacts `<details>` (contacts fetched lazily on first expand, matching this
project's fixture-sized-data simplicity — no pagination or eager N+1 fetch on page load):

```javascript
    const newOppBtn = document.createElement('button');
    newOppBtn.type = 'button';
    newOppBtn.className = 'account-new-opportunity-btn';
    newOppBtn.textContent = 'New opportunity';
    newOppBtn.addEventListener('click', () => openNewOpportunityForm(account));

    const contactsDetails = document.createElement('details');
    const contactsSummary = document.createElement('summary');
    contactsSummary.textContent = 'Contacts';
    const contactsListEl = document.createElement('ul');
    contactsListEl.className = 'account-contacts-list';
    contactsListEl.dataset.accountId = account.id;
    const newContactBtn = document.createElement('button');
    newContactBtn.type = 'button';
    newContactBtn.className = 'account-new-contact-btn';
    newContactBtn.textContent = 'New contact';
    newContactBtn.addEventListener('click', () => openAccountContactForm(account.id, null));
    let contactsLoaded = false;
    contactsDetails.addEventListener('toggle', () => {
      if (contactsDetails.open && !contactsLoaded) {
        contactsLoaded = true;
        renderAccountContacts(account.id, contactsListEl);
      }
    });
    contactsDetails.append(contactsSummary, contactsListEl, newContactBtn);
    li.append(newOppBtn, contactsDetails);
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_accounts_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/accounts.html static/js/accounts.js tests/test_ui_accounts_page.py
git commit -m "feat(crm-ui): wire create-opportunity and contact CRUD from the Accounts page"
```

---

### Task 12: Cross-page navigation links [specialist: none]

**Depends on:** Task 4, Task 8, Task 9, Task 11
**Charter capability:** Deal detail page; Create/edit/delete account
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (add nav link to `accounts.html`)
- Modify: `static/deal.html` (add nav link to `accounts.html`)
- Test: `tests/test_ui_board_page.py` (extend), `tests/test_ui_deal_page.py` (extend)

**Tests:** `tests/test_ui_board_page.py` and `tests/test_ui_deal_page.py` — extend both suites
with a link-presence assertion. This closes the loop so every page reachable from the board can
also reach the Accounts page (BEH-7's "an Account's page" entry point), without which
`accounts.html` from Task 9/10 would be unreachable from the rest of the app.

**Context to load:**
- `static/index.html` (from Task 8, full read), `static/deal.html` (from Task 7, full read),
  `static/accounts.html` (from Task 9, full read)

- [ ] **Write failing test**

Append to `tests/test_ui_board_page.py`:

```python
def test_board_page_links_to_accounts_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/").text
        assert 'href="accounts.html"' in html
```

Append to `tests/test_ui_deal_page.py`:

```python
def test_deal_page_links_to_accounts_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        html = client.get("/deal.html").text
        assert 'href="accounts.html"' in html
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py tests/test_ui_deal_page.py`
Expected: FAIL — neither page links to `accounts.html` yet

- [ ] **Implement**

Add to `static/index.html`'s `<header>`, alongside the account switcher and the "+ New
opportunity" button:

```html
    <a href="accounts.html">Accounts</a>
```

Add to `static/deal.html`'s `<header>`, alongside the "Back to board" link:

```html
    <a href="accounts.html">Accounts</a>
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py tests/test_ui_deal_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/deal.html tests/test_ui_board_page.py tests/test_ui_deal_page.py
git commit -m "feat(crm-ui): add cross-page navigation links to the Accounts page"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

- Tests pass (Python, existing gate): `python3 -m pytest -q`
- Tests pass (new/extended JS pure-logic suites this plan introduces):
  `node --test static/js` — covers the extended `api.test.mjs` plus the new
  `list-state.test.mjs` and `form-errors.test.mjs`
- Lint passes: `ruff check .` (Python only — no JS lint tool is configured in this repo, matching
  its "no build tooling" convention; not a gap this plan introduces)
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-8)

`governance/validate.yaml` for this project enables only the deterministic checks (quality
gates, source-manifest, boundaries, transition-gates, gate-executability); spec-compliance,
constitution-compliance, and visual-verification are disabled, consistent with this repo's
lightweight governance posture.
