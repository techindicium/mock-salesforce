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
