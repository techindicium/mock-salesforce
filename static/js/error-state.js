// Pure error-banner state: tracks which named sources (e.g. 'accounts',
// 'opportunities', 'move') currently have an active failure, each with its own
// message. This is deliberately independent per source so one action
// succeeding never clears an unrelated action's still-active failure — the
// board must never fail silently (see pipeline-board-view.spec.md BEH-5).

export function setError(state, source, message) {
  const next = new Map(state);
  next.set(source, message);
  return next;
}

export function clearError(state, source) {
  if (!state.has(source)) return state;
  const next = new Map(state);
  next.delete(source);
  return next;
}

export function bannerMessage(state) {
  if (state.size === 0) return null;
  return Array.from(state.values()).join(' | ');
}
