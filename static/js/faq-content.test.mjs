import test from 'node:test';
import assert from 'node:assert/strict';
import { FAQ_CATEGORIES, filterFaqs } from './faq-content.js';

test('FAQ_CATEGORIES has real content for every app section', () => {
  const names = FAQ_CATEGORIES.map((c) => c.category);
  assert.deepEqual(names, ['General', 'Opportunities', 'Accounts', 'Contacts', 'Leads']);
  for (const cat of FAQ_CATEGORIES) {
    assert.ok(cat.items.length > 0, cat.category);
    for (const item of cat.items) {
      assert.ok(item.question.length > 0);
      assert.ok(item.answer.length > 0);
    }
  }
});

test('filterFaqs with an empty query returns every category and item unchanged', () => {
  assert.equal(filterFaqs(FAQ_CATEGORIES, ''), FAQ_CATEGORIES);
  assert.equal(filterFaqs(FAQ_CATEGORIES, '   '), FAQ_CATEGORIES);
});

test('filterFaqs narrows to entries whose question matches, case-insensitively', () => {
  const result = filterFaqs(FAQ_CATEGORIES, 'CONVERT');
  const leadsCat = result.find((c) => c.category === 'Leads');
  assert.ok(leadsCat);
  assert.ok(leadsCat.items.some((i) => i.question.includes('Convert')));
  // Categories with no match are dropped entirely, not shown empty.
  assert.ok(!result.some((c) => c.category === 'Contacts'));
});

test('filterFaqs also matches against answer text, not just the question', () => {
  const result = filterFaqs(FAQ_CATEGORIES, 'confirm');
  const generalCat = result.find((c) => c.category === 'General');
  assert.ok(generalCat);
  assert.ok(generalCat.items.some((i) => i.answer.toLowerCase().includes('confirm')));
});

test('filterFaqs returns no categories when nothing matches', () => {
  const result = filterFaqs(FAQ_CATEGORIES, 'xyz-nonexistent-term');
  assert.deepEqual(result, []);
});

test('filterFaqs never mutates the original categories or their item arrays', () => {
  const before = JSON.stringify(FAQ_CATEGORIES);
  filterFaqs(FAQ_CATEGORIES, 'lead');
  assert.equal(JSON.stringify(FAQ_CATEGORIES), before);
});
