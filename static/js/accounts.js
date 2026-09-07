import { fetchAccounts, createAccount, updateAccount, deleteAccount } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';
import { inlineErrorMessage } from './form-errors.js';

const errorBanner = document.getElementById('error-banner');
const accountsList = document.getElementById('accounts-list');
const newAccountBtn = document.getElementById('new-account-btn');
const accountForm = document.getElementById('account-form');
const accountFormError = document.getElementById('account-form-error');
const accountIdInput = document.getElementById('account-id-input');
const cancelAccountBtn = document.getElementById('cancel-account-form-btn');

let errorState = new Map();
let accounts = [];

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

function openAccountForm(account) {
  accountIdInput.value = account ? account.id : '';
  accountForm.elements.name.value = account?.name ?? '';
  accountForm.elements.industry.value = account?.industry ?? '';
  accountForm.elements.phone.value = account?.phone ?? '';
  accountFormError.textContent = '';
  accountForm.hidden = false;
}

function renderAccounts() {
  accountsList.innerHTML = '';
  for (const account of accounts) {
    const li = document.createElement('li');
    li.dataset.accountId = account.id;
    const summary = document.createElement('span');
    summary.textContent = `${account.name} — ${account.industry ?? ''} — ${account.phone ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-account-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openAccountForm(account));
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'delete-account-btn';
    deleteBtn.textContent = 'Delete';
    const dependentsMessage = document.createElement('span');
    dependentsMessage.className = 'account-delete-error';
    deleteBtn.addEventListener('click', async () => {
      if (!window.confirm(`Delete account "${account.name}"?`)) return;
      dependentsMessage.textContent = '';
      try {
        await deleteAccount(account.id);
      } catch (err) {
        // BEH-7: a 409 ACCOUNT_HAS_DEPENDENTS must show inline, naming the
        // dependent count, and the Account must stay in the list — never
        // removed on a failed delete.
        dependentsMessage.textContent = inlineErrorMessage(err);
        return;
      }
      try {
        await refreshAccounts();
        reportSuccess('accounts');
      } catch (err) {
        reportError('accounts', describeApiError('refresh accounts', err));
      }
    });
    li.append(summary, editBtn, deleteBtn, dependentsMessage);
    accountsList.appendChild(li);
  }
}

async function refreshAccounts() {
  accounts = replaceList(accounts, await fetchAccounts());
  renderAccounts();
}

newAccountBtn.addEventListener('click', () => openAccountForm(null));
cancelAccountBtn.addEventListener('click', () => { accountForm.hidden = true; });

accountForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    name: accountForm.elements.name.value,
    industry: accountForm.elements.industry.value || null,
    phone: accountForm.elements.phone.value || null,
  };
  try {
    if (accountIdInput.value) {
      await updateAccount(accountIdInput.value, payload);
    } else {
      await createAccount(payload);
    }
  } catch (err) {
    accountFormError.textContent = inlineErrorMessage(err);
    return;
  }
  accountForm.hidden = true;
  try {
    await refreshAccounts();
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('refresh accounts', err));
  }
});

async function init() {
  try {
    await refreshAccounts();
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('load accounts', err));
  }
}

init();
