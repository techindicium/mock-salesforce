import { STAGE_ORDER, groupByStage } from './stages.js';
import { fetchAccounts, fetchOpportunities, updateOpportunityStage, resolveAccountName } from './api.js';
import { describeApiError } from './errors.js';
import { replaceOpportunities, applyStageMoveResult } from './board-state.js';
import { setError, clearError, bannerMessage } from './error-state.js';

const switcher = document.getElementById('account-switcher');
const errorBanner = document.getElementById('error-banner');
const board = document.getElementById('board');

let accounts = [];
let opportunities = [];
let selectedAccountId = null;
let draggedId = null;
// Tracks every currently-failing action independently (source -> message) via
// the pure error-state.js reducer, so one action succeeding never hides an
// unrelated action's still-active failure (BEH-5: the UI must never fail
// silently). The banner stays visible as long as any source has an
// outstanding error, and only clears once all of them do.
let errorState = new Map();

function renderErrorBanner() {
  const message = bannerMessage(errorState);
  errorBanner.textContent = message ?? '';
  errorBanner.hidden = message == null;
}

function reportError(source, message) {
  errorState = setError(errorState, source, message);
  renderErrorBanner();
}

function reportSuccess(source) {
  errorState = clearError(errorState, source);
  renderErrorBanner();
}

function render() {
  const grouped = groupByStage(opportunities);
  for (const stage of STAGE_ORDER) {
    const column = board.querySelector(`[data-stage-column="${stage}"] .cards`);
    column.innerHTML = '';
    for (const opp of grouped[stage]) {
      const card = document.createElement('div');
      card.className = 'opportunity-card';
      card.draggable = true;
      card.dataset.id = opp.id;
      const accountName = resolveAccountName(accounts, opp.account_id);
      card.textContent = `${opp.name} — ${accountName} — ${opp.amount ?? ''} — ${opp.close_date}`;
      card.addEventListener('dragstart', () => { draggedId = opp.id; });
      column.appendChild(card);
    }
  }
}

async function loadAccounts() {
  try {
    accounts = await fetchAccounts();
    for (const account of accounts) {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.name;
      switcher.appendChild(option);
    }
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('load accounts', err));
  }
}

async function loadOpportunities() {
  try {
    const next = await fetchOpportunities(selectedAccountId);
    opportunities = replaceOpportunities(opportunities, next);
    reportSuccess('opportunities');
    render();
  } catch (err) {
    reportError('opportunities', describeApiError('load opportunities', err));
  }
}

switcher.addEventListener('change', () => {
  selectedAccountId = switcher.value === '' ? null : Number(switcher.value);
  loadOpportunities();
});

for (const column of board.querySelectorAll('.cards')) {
  column.addEventListener('dragover', (event) => event.preventDefault());
  column.addEventListener('drop', async (event) => {
    event.preventDefault();
    const id = draggedId;
    let stageName;
    try {
      const stageColumn = column.closest('[data-stage-column]');
      if (!stageColumn || id == null) return;
      stageName = stageColumn.dataset.stageColumn;
      await updateOpportunityStage(id, stageName);
      opportunities = applyStageMoveResult(opportunities, id, stageName, true);
      reportSuccess('move');
      render();
    } catch (err) {
      opportunities = applyStageMoveResult(opportunities, id, stageName, false);
      reportError('move', describeApiError('move opportunity', err));
    }
  });
}

async function init() {
  // Accounts must load first: render() resolves each card's account name via
  // resolveAccountName(accounts, ...), so opportunities must not render before
  // accounts has populated — otherwise every card would permanently show
  // "Unknown account" with no later re-render to correct it.
  await loadAccounts();
  await loadOpportunities();
}

init();
