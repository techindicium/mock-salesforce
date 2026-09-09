import test from 'node:test';
import assert from 'node:assert/strict';
import { HELP_CONTENT, NAV_OVERVIEW, getPageHelp } from './help-content.js';

test('getPageHelp returns the mapped content for each of the five known page ids', () => {
  for (const mainId of ['board', 'deal-detail', 'accounts-page', 'contacts-page', 'leads-page']) {
    const help = getPageHelp(mainId);
    assert.equal(help, HELP_CONTENT[mainId]);
    assert.ok(help.title.length > 0);
    assert.ok(help.body.length > 0);
  }
});

test('getPageHelp falls back to a generic message for an unmapped id', () => {
  const help = getPageHelp('some-future-page');
  assert.equal(help.title, 'SalesStrength');
  assert.match(help.body, /nav above/i);
});

test('NAV_OVERVIEW lists exactly the four nav sections with a description each', () => {
  assert.equal(NAV_OVERVIEW.length, 4);
  const labels = NAV_OVERVIEW.map((entry) => entry.label);
  assert.deepEqual(labels, ['Opportunities', 'Accounts', 'Contacts', 'Leads']);
  for (const entry of NAV_OVERVIEW) {
    assert.ok(entry.description.length > 0);
  }
});
