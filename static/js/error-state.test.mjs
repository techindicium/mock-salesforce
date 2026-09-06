import test from 'node:test';
import assert from 'node:assert/strict';
import { setError, clearError, bannerMessage } from './error-state.js';

test('bannerMessage returns null when no source has an active error', () => {
  assert.equal(bannerMessage(new Map()), null);
});

test('setError records a message for a source, clearError removes it', () => {
  let state = new Map();
  state = setError(state, 'accounts', 'Failed to load accounts: HTTP 500');
  assert.equal(bannerMessage(state), 'Failed to load accounts: HTTP 500');
  state = clearError(state, 'accounts');
  assert.equal(bannerMessage(state), null);
});

test('clearError on a source with no active error is a no-op', () => {
  const state = new Map();
  assert.equal(clearError(state, 'accounts'), state);
});

test('a later success for one source never clears a different, still-active source', () => {
  let state = new Map();
  state = setError(state, 'accounts', 'Failed to load accounts: HTTP 500');
  state = setError(state, 'opportunities', 'Failed to load opportunities: HTTP 500');
  state = clearError(state, 'opportunities');
  assert.equal(bannerMessage(state), 'Failed to load accounts: HTTP 500');
});

test('bannerMessage joins multiple simultaneously active errors', () => {
  let state = new Map();
  state = setError(state, 'accounts', 'Failed to load accounts: HTTP 500');
  state = setError(state, 'move', 'Failed to move opportunity: HTTP 404');
  assert.equal(
    bannerMessage(state),
    'Failed to load accounts: HTTP 500 | Failed to move opportunity: HTTP 404',
  );
});

test('setError overwrites only the same source\'s prior message', () => {
  let state = new Map();
  state = setError(state, 'accounts', 'first failure');
  state = setError(state, 'accounts', 'second failure');
  assert.equal(bannerMessage(state), 'second failure');
});
