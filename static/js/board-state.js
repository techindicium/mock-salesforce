export function replaceOpportunities(_prior, next) {
  return next;
}

export function applyStageMoveResult(list, id, newStageName, success) {
  if (!success) return list;
  return list.map((opp) => (String(opp.id) === String(id) ? { ...opp, stage_name: newStageName } : opp));
}
