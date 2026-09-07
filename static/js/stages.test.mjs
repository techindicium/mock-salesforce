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
