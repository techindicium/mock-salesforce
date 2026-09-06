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
