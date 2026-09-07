import test from 'node:test';
import assert from 'node:assert/strict';
import { buildOpportunitiesUrl, buildContactsUrl, fetchAccounts, fetchOpportunities, resolveAccountName, ApiError, fetchOpportunity, fetchAccount, fetchContacts, createOpportunity,
  updateOpportunity, deleteOpportunity, deleteAccount, createContact, createAccount, updateAccount, updateContact, deleteContact } from './api.js';

test('buildOpportunitiesUrl omits account_id when unset ("all accounts")', () => {
  assert.equal(buildOpportunitiesUrl(null), '/opportunities');
});

test('buildOpportunitiesUrl includes account_id when set', () => {
  assert.equal(buildOpportunitiesUrl(42), '/opportunities?account_id=42');
});

test('buildContactsUrl omits account_id when unset ("all contacts")', () => {
  assert.equal(buildContactsUrl(null), '/contacts');
});

test('buildContactsUrl includes account_id when set', () => {
  assert.equal(buildContactsUrl(2), '/contacts?account_id=2');
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

test('createAccount POSTs to /accounts with the JSON payload', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return { ok: true, json: async () => ({ id: 3 }) };
  });
  await createAccount({ name: 'Initech' });
  assert.equal(calls[0].url, '/accounts');
  assert.equal(calls[0].init.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].init.body), { name: 'Initech' });
});

test('updateAccount PATCHes /accounts/{id} with the JSON payload', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return { ok: true, json: async () => ({ id: 3 }) };
  });
  await updateAccount(3, { name: 'Initech Corp' });
  assert.equal(calls[0].url, '/accounts/3');
  assert.equal(calls[0].init.method, 'PATCH');
  assert.deepEqual(JSON.parse(calls[0].init.body), { name: 'Initech Corp' });
});

test('updateContact PATCHes /contacts/{id} with the JSON payload', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    calls.push({ url, init });
    return { ok: true, json: async () => ({ id: 7 }) };
  });
  await updateContact(7, { last_name: 'Smith' });
  assert.equal(calls[0].url, '/contacts/7');
  assert.equal(calls[0].init.method, 'PATCH');
  assert.deepEqual(JSON.parse(calls[0].init.body), { last_name: 'Smith' });
});

test('deleteContact DELETEs /contacts/{id} and resolves with null on a 204', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, '/contacts/7');
    assert.equal(init.method, 'DELETE');
    return { ok: true, status: 204 };
  });
  assert.equal(await deleteContact(7), null);
});

test('createAccount throws a descriptive error when fetch itself rejects (network error)', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(() => createAccount({ name: 'Initech' }), /create account/i);
});
