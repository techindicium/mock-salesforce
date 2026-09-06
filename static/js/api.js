export function buildOpportunitiesUrl(accountId) {
  return accountId == null ? '/opportunities' : `/opportunities?account_id=${accountId}`;
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
