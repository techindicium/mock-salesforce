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

test('applyStageMoveResult matches a numeric opportunity id against a stringified id', () => {
  const list = [{ id: 1, stage_name: 'Prospecting' }];
  const moved = applyStageMoveResult(list, '1', 'Closed Won', true);
  assert.equal(moved[0].stage_name, 'Closed Won');
});

test('updateOpportunityStage throws a descriptive error on a non-2xx PATCH response', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: false, status: 404 }));
  await assert.rejects(() => updateOpportunityStage(7, 'Closed Won'), /opportunity/i);
});

test('updateOpportunityStage throws a descriptive error when fetch itself rejects (network error)', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(() => updateOpportunityStage(7, 'Closed Won'), /opportunity/i);
});
