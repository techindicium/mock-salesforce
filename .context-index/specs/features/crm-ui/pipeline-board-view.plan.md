<!-- partial_schema: plan@1 -->

# Implementation Plan: Pipeline board view, account switcher

> **Methodology:** adev
> **Charter:** .context-index/specs/features/crm-ui/charter.md
> **Spec:** .context-index/specs/features/crm-ui/pipeline-board-view.spec.md
> **Review:** PASS (2026-09-05) — skipped per risk policy (`risk_level: medium`, `require_review: false`)
> **Platform:** no frontend framework (vanilla HTML/CSS/JS, ES modules, no bundler), served by crm-api (Python 3.11 / FastAPI) via `STATIC_ASSETS_PATH`; JS pure-logic tests run on Node 24's built-in test runner (`node --test`) — no new npm/build tooling introduced

**Goal:** Ship a static HTML/CSS/JS pipeline board — ten fixed Opportunity stage columns, an
account switcher, and drag-and-drop stage moves via `PATCH /opportunities/{id}` — served as-is
by crm-api's existing static-file router.

**Architecture:** This is the first crm-ui code in the repo. crm-api already serves `index.html`
at `/` and any other file under `STATIC_ASSETS_PATH` (default relative `static/`) at its own
path (`src/mock_salesforce/static.py`) — no new backend work, no build step. The board is split
into small, independently-testable ES modules under `static/js/`: pure logic (stage ordering,
grouping, URL building, error messaging, board-state replace/move-or-revert semantics) lives in
plain functions with no DOM dependency, unit-tested with Node's built-in `node:test` runner
(available on Node 24, requires no new dependency). DOM wiring (`static/js/board.js`) stays thin
— it calls the pure modules and is verified structurally through a new pytest suite
(`tests/test_ui_board_page.py`) that follows the same `TestClient`-based pattern already used in
`tests/test_static_hosting.py`, keeping `python3 -m pytest -q` as the single Python-side gate.
Visual/browser-level verification is out of scope: this project's `governance/validate.yaml` has
visual-verification disabled, and no browser-automation tool is configured.

---

## File Structure

**Create:**
- `static/index.html` — page shell: account switcher `<select>`, ten stage-column containers
  (one per fixed `stage_name`), an error-banner container, `<link>` to `css/board.css`, and a
  `type="module"` `<script>` loading `js/board.js`
- `static/css/board.css` — column/card layout styling (kanban-style horizontal columns)
- `static/js/stages.js` — `STAGE_ORDER` (the ten fixed stage names, in the API's fixed order)
  and `groupByStage(opportunities)` (buckets opportunities per stage, always returns all ten
  keys, empty arrays for stages with no matches)
- `static/js/api.js` — `buildOpportunitiesUrl(accountId)`, `fetchAccounts()`,
  `fetchOpportunities(accountId)`, `updateOpportunityStage(id, stageName)` — thin `fetch()`
  wrappers around crm-api's same-origin REST endpoints; `resolveAccountName(accounts, accountId)`
  — a pure join over the fetched Account list, since `OpportunityOut` carries only `account_id`
  (see `models.py`), not an account name, so BEH-2's "owning Account's `name`" card field must be
  resolved client-side against the Accounts already fetched in BEH-1
- `static/js/errors.js` — `describeApiError(action, error)` — turns a failed fetch/response into
  a visible, human-readable message naming what failed
- `static/js/board-state.js` — `replaceOpportunities(prior, next)` (full-replace semantics) and
  `applyStageMoveResult(list, id, newStageName, success)` (moves an opportunity's `stage_name`
  only when `success` is true; returns the list unchanged on failure)
- `static/js/board.js` — DOM wiring: initial load (BEH-1), render columns from
  `groupByStage()`, account-switcher `change` listener (BEH-3), HTML5 drag-and-drop handlers
  calling `updateOpportunityStage` then `applyStageMoveResult` (BEH-4), error-banner rendering
  (BEH-5), empty-column rendering (BEH-6)
- `static/js/stages.test.mjs` — BEH-2 / BEH-6 suite (via `node --test`)
- `static/js/api.test.mjs` — BEH-1 suite
- `static/js/errors.test.mjs` — BEH-5 suite
- `static/js/board-state.test.mjs` — BEH-3 / BEH-4 suite
- `tests/test_ui_board_page.py` — pytest suite (via `python3 -m pytest -q`) asserting the real
  `static/` directory's `index.html`/`board.css`/`board.js` are served with the expected
  structural markers (ten column containers, switcher `<select>`, stylesheet link, module script)

**Modify:** none — crm-api's static-file router, routes, and models are already implemented and
require no changes for this spec.

**Reference (read, do not modify):**
- `src/mock_salesforce/static.py` — confirms `GET /{full_path}` serves `STATIC_ASSETS_PATH`
  (default `static/`), `index.html` at `/`, 404 shape `{"error": "STATIC_ASSET_NOT_FOUND", ...}`
- `src/mock_salesforce/models.py` — `StageName` Literal (the ten fixed stage values, exact
  spelling/order), `OpportunityOut` shape (`id`, `account_id`, `name`, `stage_name`, `amount`,
  `close_date`, `is_closed`, `is_won`, `created_at`, `updated_at`), `AccountOut` shape (`id`,
  `name`, ...)
- `src/mock_salesforce/opportunities.py` — `GET /opportunities?account_id=&stage_name=`,
  `PATCH /opportunities/{id}` (partial update; 404 `OPPORTUNITY_NOT_FOUND` on missing id)
- `src/mock_salesforce/accounts.py` — `GET /accounts`
- `src/mock_salesforce/errors.py` — error envelope shape `{"error": <code>, "message": <str>}`
  returned on every non-2xx response, including validation (422/400) and not-found (404/409)
- `tests/test_static_hosting.py` — existing pattern for testing the static router with
  `TestClient` + `monkeypatch.setenv("STATIC_ASSETS_PATH", ...)`
- `tests/conftest.py` — existing `client` fixture pattern (`DB_PATH` env + `TestClient`)

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-2, BEH-6)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capability: Render pipeline board)
- Source files: `src/mock_salesforce/models.py` — `StageName` Literal (full read, exact spelling/order)

### Task 2 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-1, BEH-2 card
  field — the Account-name join)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capability: Render pipeline board; Account switcher)
- Source files: `src/mock_salesforce/accounts.py` (signature: `GET /accounts` → `list[AccountOut]`),
  `src/mock_salesforce/opportunities.py` (signature: `GET /opportunities?account_id=&stage_name=` → `list[OpportunityOut]`),
  `src/mock_salesforce/models.py` (`AccountOut`, `OpportunityOut` field shapes, full read — note
  `OpportunityOut` carries only `account_id`, no account name, hence `resolveAccountName`)

### Task 3 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-5, Error Cases table)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (Quality Attributes: Observability)
- Source files: `src/mock_salesforce/errors.py` (full read — error envelope `{"error", "message"}` shape)

### Task 4 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-3, BEH-4, Postconditions)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capability: Move opportunity between stages)
- Source files: `src/mock_salesforce/opportunities.py` (signature: `PATCH /opportunities/{id}` — partial
  update body, 404 `OPPORTUNITY_NOT_FOUND`), `static/js/api.js` (from Task 2, full read — extend, do not replace)

### Task 5 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-1, BEH-2, BEH-6, Preconditions)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capabilities: Render pipeline board; Account switcher)
- Source files: `src/mock_salesforce/static.py` (full read — serving contract), `tests/test_static_hosting.py`
  (full read — TestClient + `STATIC_ASSETS_PATH` pattern to follow), `static/js/stages.js` (from Task 1, export
  signatures only — `STAGE_ORDER` values needed for column labels)

### Task 6 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (BEH-2 — card field presentation)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (Quality Attributes: Performance)
- Source files: `static/index.html` (from Task 5, full read — element/class names to style)

### Task 7 Context
- Spec: `.context-index/specs/features/crm-ui/pipeline-board-view.spec.md` (all of BEH-1..BEH-6, Postconditions)
- Charter: `.context-index/specs/features/crm-ui/charter.md` (capabilities: Render pipeline board; Move
  opportunity between stages; Account switcher)
- Source files: `static/js/stages.js`, `static/js/api.js`, `static/js/errors.js`,
  `static/js/board-state.js` (all from Tasks 1-4, full read — this task is pure wiring over them),
  `static/index.html` (from Task 5, full read — element IDs/classes to bind against)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty (`boundaries: []`), no rules to check

No ADRs, samples, or cross-cutting specs apply — none exist in this repo yet. No heuristics are
recorded for the `crm-ui` module (`adev heuristics retrieve --module crm-ui` returned `__NONE__`).

---

## Parallelization

- Group A (sequential): Task 2 → Task 4 (Task 4 extends `static/js/api.js` created by Task 2)
- Group B (sequential): Task 1 → Task 5 → Task 6 (Task 5 depends on Task 1's `STAGE_ORDER`
  labels; Task 6 styles elements Task 5 creates; all three share no files with Group A)
- Group C (independent): Task 3 (no file overlap with A or B)

Groups B and C can run in parallel with Group A and with each other. Task 7 depends on every
task above (1, 2, 3, 4, 5, 6) and always runs last — it is not part of any group above.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Stage order and grouping | small | unit | — | 2 create |
| 2 | Accounts/Opportunities fetch client | medium | unit | — | 2 create |
| 3 | API error messaging | small | unit | — | 2 create |
| 4 | Stage-move request and board-state replace/move-or-revert | medium | unit | Task 2 | 2 create, 1 modify |
| 5 | Board page shell (HTML) | medium | unit | Task 1 | 2 create |
| 6 | Board layout styling (CSS) | small | unit | Task 5 | 1 create, 1 modify |
| 7 | Board wiring: render, switcher, drag-and-drop, errors | large | unit | Task 1, 2, 3, 4, 5, 6 | 1 create, 1 modify |

Spec coverage: 6 of 6 behaviors mapped (BEH-1 → Task 2/7; BEH-2 → Task 1/5/7; BEH-3 → Task 4/7;
BEH-4 → Task 4/7; BEH-5 → Task 3/7; BEH-6 → Task 1/5/7).

---

## Task Structure

### Task 1: Stage order and grouping [specialist: none]

**Charter capability:** Render pipeline board
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/stages.js`
- Test: `static/js/stages.test.mjs`

**Tests:** `static/js/stages.test.mjs` — new suite (BEH-2, BEH-6). This is the first task; the
suite does not exist yet, so create it.

**Context to load:**
- `src/mock_salesforce/models.py` (the `StageName` Literal — exact ten values and order)

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { STAGE_ORDER, groupByStage } from './stages.js';

test('STAGE_ORDER has the ten fixed stages in the API\'s fixed order', () => {
  assert.deepEqual(STAGE_ORDER, [
    'Prospecting', 'Qualification', 'Needs Analysis', 'Value Proposition',
    'Id. Decision Makers', 'Perception Analysis', 'Proposal/Price Quote',
    'Negotiation/Review', 'Closed Won', 'Closed Lost',
  ]);
});

test('groupByStage buckets opportunities under their stage_name', () => {
  const opps = [
    { id: 1, stage_name: 'Prospecting' },
    { id: 2, stage_name: 'Closed Won' },
  ];
  const grouped = groupByStage(opps);
  assert.equal(grouped['Prospecting'].length, 1);
  assert.equal(grouped['Closed Won'][0].id, 2);
});

test('groupByStage returns all ten keys with empty arrays when given zero opportunities', () => {
  const grouped = groupByStage([]);
  assert.equal(Object.keys(grouped).length, 10);
  for (const stage of STAGE_ORDER) {
    assert.deepEqual(grouped[stage], []);
  }
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/stages.test.mjs`
Expected: FAIL — `Cannot find module './stages.js'`

- [ ] **Implement**

```javascript
export const STAGE_ORDER = [
  'Prospecting', 'Qualification', 'Needs Analysis', 'Value Proposition',
  'Id. Decision Makers', 'Perception Analysis', 'Proposal/Price Quote',
  'Negotiation/Review', 'Closed Won', 'Closed Lost',
];

export function groupByStage(opportunities) {
  const grouped = Object.fromEntries(STAGE_ORDER.map((s) => [s, []]));
  for (const opp of opportunities) {
    (grouped[opp.stage_name] ??= []).push(opp);
  }
  return grouped;
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/stages.test.mjs`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/crm-ui/pipeline-board-view`

```bash
git add static/js/stages.js static/js/stages.test.mjs
git commit -m "feat(crm-ui): add fixed stage order and opportunity grouping"
```

---

### Task 2: Accounts/Opportunities fetch client [specialist: none]

**Charter capability:** Render pipeline board; Account switcher
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/api.js`
- Test: `static/js/api.test.mjs`

**Tests:** `static/js/api.test.mjs` — new suite (BEH-1, plus the Account-name join for BEH-2).
This is the first task touching this suite; create it.

**Context to load:**
- `src/mock_salesforce/accounts.py` (signature only: `GET /accounts`)
- `src/mock_salesforce/opportunities.py` (signature only: `GET /opportunities?account_id=&stage_name=`)
- `src/mock_salesforce/models.py` (`AccountOut`, `OpportunityOut` fields, full read)

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildOpportunitiesUrl, fetchAccounts, fetchOpportunities, resolveAccountName } from './api.js';

test('buildOpportunitiesUrl omits account_id when unset ("all accounts")', () => {
  assert.equal(buildOpportunitiesUrl(null), '/opportunities');
});

test('buildOpportunitiesUrl includes account_id when set', () => {
  assert.equal(buildOpportunitiesUrl(42), '/opportunities?account_id=42');
});

test('fetchAccounts calls GET /accounts and returns the parsed JSON list', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url) => {
    calls.push(url);
    return { ok: true, json: async () => [{ id: 1, name: 'Acme' }] };
  });
  const accounts = await fetchAccounts();
  assert.deepEqual(calls, ['/accounts']);
  assert.deepEqual(accounts, [{ id: 1, name: 'Acme' }]);
});

test('fetchOpportunities throws a descriptive error on a non-2xx response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: false, status: 500 }));
  await assert.rejects(() => fetchOpportunities(null), /opportunities/i);
});

test('fetchOpportunities throws a descriptive error when fetch itself rejects (network error)', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(() => fetchOpportunities(null), /opportunities/i);
});

test('resolveAccountName finds the matching account\'s name by id', () => {
  const accounts = [{ id: 1, name: 'Acme' }, { id: 2, name: 'Globex' }];
  assert.equal(resolveAccountName(accounts, 2), 'Globex');
});

test('resolveAccountName falls back gracefully for an unknown or missing account_id', () => {
  const accounts = [{ id: 1, name: 'Acme' }];
  assert.equal(resolveAccountName(accounts, 999), 'Unknown account');
  assert.equal(resolveAccountName([], 1), 'Unknown account');
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/api.test.mjs`
Expected: FAIL — `Cannot find module './api.js'`

- [ ] **Implement**

```javascript
export function buildOpportunitiesUrl(accountId) {
  return accountId == null ? '/opportunities' : `/opportunities?account_id=${accountId}`;
}

async function fetchJson(url, action) {
  let response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new Error(`Failed to load ${action}: network error`);
  }
  if (!response.ok) {
    throw new Error(`Failed to load ${action}: HTTP ${response.status}`);
  }
  return response.json();
}

export function fetchAccounts() {
  return fetchJson('/accounts', 'accounts');
}

export function fetchOpportunities(accountId) {
  return fetchJson(buildOpportunitiesUrl(accountId), 'opportunities');
}

export function resolveAccountName(accounts, accountId) {
  const match = accounts.find((account) => account.id === accountId);
  return match ? match.name : 'Unknown account';
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/api.test.mjs`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/api.js static/js/api.test.mjs
git commit -m "feat(crm-ui): add accounts/opportunities fetch client and account-name join"
```

---

### Task 3: API error messaging [specialist: none]

**Charter capability:** Render pipeline board (Quality Attribute: Observability)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/errors.js`
- Test: `static/js/errors.test.mjs`

**Tests:** `static/js/errors.test.mjs` — new suite (BEH-5). This is the first task touching this
suite; create it.

**Context to load:**
- `src/mock_salesforce/errors.py` (full read — the `{"error", "message"}` envelope shape)
- Spec Error Cases table (`UI_FETCH_FAILED`, `UI_STAGE_MOVE_FAILED`)

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { describeApiError } from './errors.js';

test('describeApiError names the action that failed', () => {
  const message = describeApiError('load opportunities', new Error('HTTP 500'));
  assert.match(message, /load opportunities/);
  assert.match(message, /HTTP 500/);
});

test('describeApiError never returns an empty string', () => {
  const message = describeApiError('move opportunity', new Error());
  assert.ok(message.length > 0);
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/errors.test.mjs`
Expected: FAIL — `Cannot find module './errors.js'`

- [ ] **Implement**

```javascript
export function describeApiError(action, error) {
  const detail = error && error.message ? error.message : 'unknown error';
  return `Could not ${action}: ${detail}`;
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/errors.test.mjs`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/errors.js static/js/errors.test.mjs
git commit -m "feat(crm-ui): add API error messaging helper"
```

---

### Task 4: Stage-move request and board-state replace/move-or-revert [specialist: none]

**Depends on:** Task 2
**Charter capability:** Move opportunity between stages
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/api.js` (add `updateOpportunityStage`)
- Create: `static/js/board-state.js`
- Test: `static/js/board-state.test.mjs`

**Tests:** `static/js/board-state.test.mjs` — new suite (BEH-3, BEH-4). This is the first task
touching this suite; create it. Covers both the success path and the failure paths for the
safety-critical part of BEH-4 (a failed `PATCH` must leave the card in its original column):
`updateOpportunityStage` is tested against a non-2xx response and against `fetch` itself
rejecting (network error), mirroring the failure-path coverage Task 2 has for `fetchAccounts`/
`fetchOpportunities`.

**Context to load:**
- `src/mock_salesforce/opportunities.py` (signature only: `PATCH /opportunities/{id}`, 404 `OPPORTUNITY_NOT_FOUND`)
- `static/js/api.js` (from Task 2, full read — extend, do not replace `fetchAccounts`/`fetchOpportunities`)

- [ ] **Write failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { updateOpportunityStage } from './api.js';
import { replaceOpportunities, applyStageMoveResult } from './board-state.js';

test('updateOpportunityStage PATCHes /opportunities/{id} with the new stage_name', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return { ok: true, json: async () => ({ id: 7, stage_name: 'Negotiation/Review' }) };
  });
  await updateOpportunityStage(7, 'Negotiation/Review');
  assert.equal(calls[0].url, '/opportunities/7');
  assert.equal(calls[0].init.method, 'PATCH');
  assert.deepEqual(JSON.parse(calls[0].init.body), { stage_name: 'Negotiation/Review' });
});

test('replaceOpportunities fully replaces the prior list, never merges', () => {
  const prior = [{ id: 1, stage_name: 'Prospecting' }];
  const next = replaceOpportunities(prior, [{ id: 2, stage_name: 'Closed Won' }]);
  assert.deepEqual(next, [{ id: 2, stage_name: 'Closed Won' }]);
});

test('applyStageMoveResult moves the opportunity only when success is true', () => {
  const list = [{ id: 1, stage_name: 'Prospecting' }];
  const moved = applyStageMoveResult(list, 1, 'Closed Won', true);
  assert.equal(moved[0].stage_name, 'Closed Won');
});

test('applyStageMoveResult leaves the list unchanged when success is false', () => {
  const list = [{ id: 1, stage_name: 'Prospecting' }];
  const unchanged = applyStageMoveResult(list, 1, 'Closed Won', false);
  assert.deepEqual(unchanged, list);
});

test('updateOpportunityStage throws a descriptive error on a non-2xx PATCH response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: false, status: 404 }));
  await assert.rejects(() => updateOpportunityStage(7, 'Closed Won'), /opportunity/i);
});

test('updateOpportunityStage throws a descriptive error when fetch itself rejects (network error)', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(() => updateOpportunityStage(7, 'Closed Won'), /opportunity/i);
});
```

- [ ] **Verify test fails**

Run: `node --test static/js/board-state.test.mjs`
Expected: FAIL — `Cannot find module './board-state.js'` (and `updateOpportunityStage` not exported from `./api.js`)

- [ ] **Implement**

Append to `static/js/api.js`:

```javascript
export async function updateOpportunityStage(id, stageName) {
  let response;
  try {
    response = await fetch(`/opportunities/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_name: stageName }),
    });
  } catch (err) {
    throw new Error(`Failed to move opportunity ${id}: network error`);
  }
  if (!response.ok) {
    throw new Error(`Failed to move opportunity ${id}: HTTP ${response.status}`);
  }
  return response.json();
}
```

`static/js/board-state.js`:

```javascript
export function replaceOpportunities(_prior, next) {
  return next;
}

export function applyStageMoveResult(list, id, newStageName, success) {
  if (!success) return list;
  return list.map((opp) => (opp.id === id ? { ...opp, stage_name: newStageName } : opp));
}
```

- [ ] **Verify test passes**

Run: `node --test static/js/board-state.test.mjs`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/api.js static/js/board-state.js static/js/board-state.test.mjs
git commit -m "feat(crm-ui): add stage-move PATCH call and board-state replace/move semantics"
```

---

### Task 5: Board page shell (HTML) [specialist: none]

**Depends on:** Task 1
**Charter capability:** Render pipeline board; Account switcher
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/index.html`
- Test: `tests/test_ui_board_page.py`

**Tests:** `tests/test_ui_board_page.py` — new suite. This is the first task touching this
suite; create it. Covers the structural preconditions for BEH-1 (switcher present), BEH-2 (ten
columns present), BEH-6 (empty column containers present in the static skeleton). The test must
assert the *exact* DOM hooks Task 7's `board.js` will bind against — `id="account-switcher"`,
`id="error-banner"`, `id="board"`, and a `class="cards"` element inside each stage column — not
just the presence of *a* `<select>` and *some* stage columns. Task 7 does
`document.getElementById('account-switcher' | 'error-banner' | 'board')` and
`querySelector('[data-stage-column="..."] .cards')` with no fallback: if Task 5 ships markup
without these exact ids/classes, `render()` calls a method on `null` and throws, crashing the
board — the one thing BEH-5/BEH-6 require never happens. Passing Task 5's test must not be
possible without also satisfying Task 7's DOM contract.

**Context to load:**
- `src/mock_salesforce/static.py` (full read — serving contract: `/` → `index.html`)
- `tests/test_static_hosting.py` (full read — `TestClient` + `STATIC_ASSETS_PATH` pattern)
- `static/js/stages.js` (from Task 1, export signatures only — the ten `STAGE_ORDER` labels)

- [ ] **Write failing test**

```python
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "static"


def test_index_html_has_ten_stage_columns_and_account_switcher(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert html.count('data-stage-column="') == 10
        # These exact ids/classes are the DOM contract Task 7's board.js binds against
        # (getElementById + querySelector with no fallback) — asserting only "a <select>
        # exists somewhere" would let Task 5 pass without the hooks Task 7 needs, causing
        # board.js to throw on a null element and crash the board at runtime.
        assert 'id="account-switcher"' in html
        assert 'id="error-banner"' in html
        assert 'id="board"' in html
        assert 'class="cards"' in html
        assert 'type="module"' in html
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: FAIL — `static/index.html` does not exist yet (0 columns found / file not created)

- [ ] **Implement**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Pipeline Board</title>
  <link rel="stylesheet" href="css/board.css" />
</head>
<body>
  <header>
    <label for="account-switcher">Account</label>
    <select id="account-switcher">
      <option value="">All accounts</option>
    </select>
  </header>
  <div id="error-banner" role="alert" hidden></div>
  <main id="board">
    <!-- One column per fixed stage_name, in STAGE_ORDER's order (see static/js/stages.js) -->
    <section class="stage-column" data-stage-column="Prospecting"><h2>Prospecting</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Qualification"><h2>Qualification</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Needs Analysis"><h2>Needs Analysis</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Value Proposition"><h2>Value Proposition</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Id. Decision Makers"><h2>Id. Decision Makers</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Perception Analysis"><h2>Perception Analysis</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Proposal/Price Quote"><h2>Proposal/Price Quote</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Negotiation/Review"><h2>Negotiation/Review</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Closed Won"><h2>Closed Won</h2><div class="cards"></div></section>
    <section class="stage-column" data-stage-column="Closed Lost"><h2>Closed Lost</h2><div class="cards"></div></section>
  </main>
  <script type="module" src="js/board.js"></script>
</body>
</html>
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html tests/test_ui_board_page.py
git commit -m "feat(crm-ui): add board page shell with ten stage columns and account switcher"
```

---

### Task 6: Board layout styling (CSS) [specialist: none]

**Depends on:** Task 5
**Charter capability:** Render pipeline board (Quality Attribute: Performance)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/css/board.css`
- Modify: `tests/test_ui_board_page.py` (extend)

**Tests:** `tests/test_ui_board_page.py` — extend the existing suite from Task 5 with a
stylesheet-serving assertion.

**Context to load:**
- `static/index.html` (from Task 5, full read — element/class names to style)

- [ ] **Write failing test**

Append to `tests/test_ui_board_page.py`:

```python
def test_board_css_is_served_with_css_content_type(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/css/board.css")
        assert response.status_code == 200
        assert "css" in response.headers["content-type"]
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: FAIL — 404 `STATIC_ASSET_NOT_FOUND`, `static/css/board.css` does not exist yet

- [ ] **Implement**

```css
body { margin: 0; font-family: system-ui, sans-serif; }
header { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; border-bottom: 1px solid #ddd; }
#error-banner { background: #fdecea; color: #611a15; padding: 0.5rem 1rem; }
#error-banner[hidden] { display: none; }
#board { display: flex; gap: 0.75rem; overflow-x: auto; padding: 1rem; align-items: flex-start; }
.stage-column { flex: 0 0 220px; background: #f4f5f7; border-radius: 6px; padding: 0.5rem; }
.stage-column h2 { font-size: 0.85rem; margin: 0 0 0.5rem; }
.cards { display: flex; flex-direction: column; gap: 0.5rem; min-height: 40px; }
.opportunity-card { background: #fff; border: 1px solid #ddd; border-radius: 4px; padding: 0.5rem; cursor: grab; }
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/css/board.css tests/test_ui_board_page.py
git commit -m "feat(crm-ui): add board kanban layout styling"
```

---

### Task 7: Board wiring — render, switcher, drag-and-drop, errors [specialist: none]

**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5, Task 6
**Charter capability:** Render pipeline board; Move opportunity between stages; Account switcher
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/js/board.js`
- Modify: `tests/test_ui_board_page.py` (extend)

**Tests:** `tests/test_ui_board_page.py` — extend the existing suite from Tasks 5/6 with a
structural assertion that `board.js` is served and wires the modules from Tasks 1-4. This is a
structural/smoke check, not a full behavioral test: no jsdom or browser-automation tool is
configured in this repo (`governance/validate.yaml` disables visual-verification), so the actual
DOM behaviors (BEH-1 through BEH-6) are exercised through the pure-function suites in Tasks 1-4
(`stages.test.mjs`, `api.test.mjs`, `errors.test.mjs`, `board-state.test.mjs`), which `board.js`
calls directly without adding branching logic of its own.

**Context to load:**
- `static/js/stages.js`, `static/js/api.js`, `static/js/errors.js`, `static/js/board-state.js`
  (from Tasks 1-4, full read — this task only wires these, no new logic). In particular, `api.js`
  exports `resolveAccountName(accounts, accountId)` (Task 2) — `board.js` must call it when
  rendering each card, since `OpportunityOut` carries only `account_id` and BEH-2 requires the
  owning Account's `name`, not its id.
- `static/index.html` (from Task 5, full read — element IDs/classes: `#account-switcher`,
  `#error-banner`, `#board`, `[data-stage-column]`, `.cards`)

- [ ] **Write failing test**

Append to `tests/test_ui_board_page.py`:

```python
def test_board_js_is_served_and_wires_the_pure_modules(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("STATIC_ASSETS_PATH", str(STATIC_DIR))

    from mock_salesforce.app import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/js/board.js")
        assert response.status_code == 200
        js = response.text
        assert "from './stages.js'" in js
        assert "from './api.js'" in js
        assert "from './errors.js'" in js
        assert "from './board-state.js'" in js
        assert "dragstart" in js
        assert "'drop'" in js or '"drop"' in js
        assert "account-switcher" in js
        assert "resolveAccountName" in js
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: FAIL — 404 `STATIC_ASSET_NOT_FOUND`, `static/js/board.js` does not exist yet

- [ ] **Implement**

```javascript
import { STAGE_ORDER, groupByStage } from './stages.js';
import { fetchAccounts, fetchOpportunities, updateOpportunityStage, resolveAccountName } from './api.js';
import { describeApiError } from './errors.js';
import { replaceOpportunities, applyStageMoveResult } from './board-state.js';

const switcher = document.getElementById('account-switcher');
const errorBanner = document.getElementById('error-banner');
const board = document.getElementById('board');

let accounts = [];
let opportunities = [];
let selectedAccountId = null;
let draggedId = null;

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
}

function render() {
  const grouped = groupByStage(opportunities);
  for (const stage of STAGE_ORDER) {
    const column = board.querySelector(`[data-stage-column="${stage}"] .cards`);
    column.innerHTML = '';
    for (const opp of grouped[stage]) {
      const card = document.createElement('div');
      card.className = 'opportunity-card';
      card.draggable = true;
      card.dataset.id = opp.id;
      const accountName = resolveAccountName(accounts, opp.account_id);
      card.textContent = `${opp.name} — ${accountName} — ${opp.amount ?? ''} — ${opp.close_date}`;
      card.addEventListener('dragstart', () => { draggedId = opp.id; });
      column.appendChild(card);
    }
  }
}

async function loadAccounts() {
  try {
    accounts = await fetchAccounts();
    for (const account of accounts) {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.name;
      switcher.appendChild(option);
    }
  } catch (err) {
    showError(describeApiError('load accounts', err));
  }
}

async function loadOpportunities() {
  try {
    const next = await fetchOpportunities(selectedAccountId);
    opportunities = replaceOpportunities(opportunities, next);
    clearError();
    render();
  } catch (err) {
    showError(describeApiError('load opportunities', err));
  }
}

switcher.addEventListener('change', () => {
  selectedAccountId = switcher.value === '' ? null : Number(switcher.value);
  loadOpportunities();
});

for (const column of board.querySelectorAll('.cards')) {
  column.addEventListener('dragover', (event) => event.preventDefault());
  column.addEventListener('drop', async (event) => {
    event.preventDefault();
    const stageName = column.closest('[data-stage-column]').dataset.stageColumn;
    const id = draggedId;
    if (id == null) return;
    try {
      await updateOpportunityStage(id, stageName);
      opportunities = applyStageMoveResult(opportunities, id, stageName, true);
      clearError();
      render();
    } catch (err) {
      opportunities = applyStageMoveResult(opportunities, id, stageName, false);
      showError(describeApiError('move opportunity', err));
    }
  });
}

async function init() {
  // Accounts must load first: render() resolves each card's account name via
  // resolveAccountName(accounts, ...), so opportunities must not render before
  // accounts has populated — otherwise every card would permanently show
  // "Unknown account" with no later re-render to correct it.
  await loadAccounts();
  await loadOpportunities();
}

init();
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q tests/test_ui_board_page.py`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board.js tests/test_ui_board_page.py
git commit -m "feat(crm-ui): wire pipeline board rendering, account switcher, and drag-and-drop stage moves"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

- Tests pass (Python, existing gate): `python3 -m pytest -q`
- Tests pass (new, JS pure-logic suites introduced by this plan): `node --test static/js`
- Lint passes: `ruff check .` (Python only — no JS lint tool is configured in this repo, matching
  its "no build tooling" convention; not a gap this plan introduces)
- All acceptance criteria from the spec satisfied (BEH-1 through BEH-6)

`governance/validate.yaml` for this project enables only the deterministic checks (quality
gates, source-manifest, boundaries, transition-gates, gate-executability); spec-compliance,
constitution-compliance, and visual-verification are disabled, consistent with this repo's
lightweight governance posture.
