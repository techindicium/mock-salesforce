// Generic full-replace helper for any fetched list (Contacts, Accounts) — mirrors
// board-state.js's replaceOpportunities semantics: a refreshed list must never
// merge with a stale one (same invariant the pipeline board's Account filter
// switch already enforces).
export function replaceList(_prior, next) {
  return next;
}
