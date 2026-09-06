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
