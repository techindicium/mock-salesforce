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

test('describeApiError surfaces a thrown string directly', () => {
  const message = describeApiError('load accounts', 'boom');
  assert.match(message, /load accounts/);
  assert.match(message, /boom/);
});

test('describeApiError falls back sensibly for non-Error, non-string values', () => {
  const objectMessage = describeApiError('load accounts', { code: 404 });
  assert.ok(objectMessage.length > 0);
  assert.match(objectMessage, /404/);

  const undefinedMessage = describeApiError('load accounts', undefined);
  assert.ok(undefinedMessage.length > 0);
});
