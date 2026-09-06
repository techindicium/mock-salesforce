// Picks the most specific message available for an inline form error: the API's
// own structured message (already names the offending field for a 422, or the
// dependent count for a 409 — see errors.py/accounts.py) when present, falling
// back to the error's generic message otherwise. Never returns an empty string.
export function inlineErrorMessage(error) {
  if (error && typeof error.apiMessage === 'string' && error.apiMessage.length > 0) {
    return error.apiMessage;
  }
  if (error && typeof error.message === 'string' && error.message.length > 0) {
    return error.message;
  }
  return 'unknown error';
}
