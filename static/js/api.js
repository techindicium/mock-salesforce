export function buildOpportunitiesUrl(accountId) {
  return accountId == null ? '/opportunities' : `/opportunities?account_id=${accountId}`;
}

export function buildContactsUrl(accountId) {
  return accountId == null ? '/contacts' : `/contacts?account_id=${accountId}`;
}

async function fetchJson(url, action) {
  let response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new Error(`Failed to load ${action}: network error`);
  }
  if (!response.ok) {
    throw new Error(`Failed to load ${action}: HTTP ${response.status}`);
  }
  return response.json();
}

export function fetchAccounts() {
  return fetchJson('/accounts', 'accounts');
}

export function fetchOpportunities(accountId) {
  return fetchJson(buildOpportunitiesUrl(accountId), 'opportunities');
}

export function resolveAccountName(accounts, accountId) {
  const match = accounts.find((account) => account.id === accountId);
  return match ? match.name : 'Unknown account';
}

export async function updateOpportunityStage(id, stageName) {
  let response;
  try {
    response = await fetch(`/opportunities/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_name: stageName }),
    });
  } catch (err) {
    throw new Error(`Failed to move opportunity ${id}: network error`);
  }
  if (!response.ok) {
    throw new Error(`Failed to move opportunity ${id}: HTTP ${response.status}`);
  }
  return response.json();
}

// --- Detail / CRUD extensions (deal-detail-and-crud-forms) ---
// Unlike fetchJson() above (which only surfaces the HTTP status), ApiError carries
// the API's structured {"error": code, "message": msg} envelope (see errors.py) so
// callers can show the exact validation-field or dependent-count message inline
// (BEH-7, BEH-8 Error Cases table) instead of a generic "HTTP 422" string.
export class ApiError extends Error {
  constructor(action, status, code, apiMessage) {
    super(apiMessage ? `Failed to ${action}: ${apiMessage}` : `Failed to ${action}: HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.apiMessage = apiMessage;
  }
}

async function request(url, options, action) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    throw new Error(`Failed to ${action}: network error`);
  }
  if (!response.ok) {
    let body = null;
    try {
      body = await response.json();
    } catch (err) {
      // non-JSON or unreadable error body — fall back to the status code
    }
    throw new ApiError(action, response.status, body?.error ?? null, body?.message ?? null);
  }
  if (response.status === 204) return null;
  return response.json();
}

function jsonRequest(url, method, payload, action) {
  return request(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, action);
}

export function fetchOpportunity(id) {
  return request(`/opportunities/${id}`, undefined, 'load opportunity');
}

export function fetchAccount(id) {
  return request(`/accounts/${id}`, undefined, 'load account');
}

export function fetchContacts(accountId) {
  return request(buildContactsUrl(accountId), undefined, 'load contacts');
}

export function createOpportunity(payload) {
  return jsonRequest('/opportunities', 'POST', payload, 'create opportunity');
}

export function updateOpportunity(id, payload) {
  return jsonRequest(`/opportunities/${id}`, 'PATCH', payload, 'update opportunity');
}

export function deleteOpportunity(id) {
  return request(`/opportunities/${id}`, { method: 'DELETE' }, 'delete opportunity');
}

export function createAccount(payload) {
  return jsonRequest('/accounts', 'POST', payload, 'create account');
}

export function updateAccount(id, payload) {
  return jsonRequest(`/accounts/${id}`, 'PATCH', payload, 'update account');
}

export function deleteAccount(id) {
  return request(`/accounts/${id}`, { method: 'DELETE' }, 'delete account');
}

export function createContact(payload) {
  return jsonRequest('/contacts', 'POST', payload, 'create contact');
}

export function updateContact(id, payload) {
  return jsonRequest(`/contacts/${id}`, 'PATCH', payload, 'update contact');
}

export function deleteContact(id) {
  return request(`/contacts/${id}`, { method: 'DELETE' }, 'delete contact');
}
