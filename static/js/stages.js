export const STAGE_ORDER = [
  'Prospecting', 'Qualification', 'Needs Analysis', 'Value Proposition',
  'Id. Decision Makers', 'Perception Analysis', 'Proposal/Price Quote',
  'Negotiation/Review', 'Closed Won', 'Closed Lost',
];

export function groupByStage(opportunities) {
  const grouped = Object.fromEntries(STAGE_ORDER.map((s) => [s, []]));
  for (const opp of opportunities) {
    (grouped[opp.stage_name] ??= []).push(opp);
  }
  return grouped;
}
