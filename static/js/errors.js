function extractDetail(error) {
  if (error instanceof Error) {
    return error.message || 'unknown error';
  }
  if (typeof error === 'string') {
    return error || 'unknown error';
  }
  if (error === null || error === undefined) {
    return 'unknown error';
  }
  if (typeof error === 'object') {
    try {
      const json = JSON.stringify(error);
      if (json && json !== '{}') return json;
    } catch (e) {
      // circular or unserializable - fall through to generic fallback
    }
    return 'unknown error';
  }
  const str = String(error);
  return str || 'unknown error';
}

export function describeApiError(action, error) {
  const detail = extractDetail(error);
  return `Could not ${action}: ${detail}`;
}
