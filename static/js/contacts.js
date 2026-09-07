import { fetchAccounts, fetchContacts, resolveAccountName } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';

const errorBanner = document.getElementById('error-banner');
const listEl = document.getElementById('all-contacts-list');
const emptyState = document.getElementById('contacts-empty-state');
const accountSelect = document.getElementById('contact-account-select');
const newContactBtn = document.getElementById('new-contact-btn');
const contactForm = document.getElementById('contact-form');
const cancelBtn = document.getElementById('cancel-contact-form-btn');

let errorState = new Map();
let accounts = [];
let contacts = [];

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

function renderContacts() {
  listEl.innerHTML = '';
  emptyState.hidden = contacts.length !== 0;
  for (const contact of contacts) {
    const li = document.createElement('li');
    li.dataset.contactId = contact.id;
    const accountName = resolveAccountName(accounts, contact.account_id);
    const summary = document.createElement('span');
    summary.textContent = `${contact.first_name} ${contact.last_name} — ${accountName} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    li.appendChild(summary);
    listEl.appendChild(li);
  }
}

async function loadAccounts() {
  try {
    accounts = await fetchAccounts();
    accountSelect.innerHTML = '';
    for (const account of accounts) {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.name;
      accountSelect.appendChild(option);
    }
    reportSuccess('accounts');
  } catch (err) {
    reportError('accounts', describeApiError('load accounts', err));
  }
}

async function loadContacts() {
  try {
    const next = await fetchContacts(null);
    contacts = replaceList(contacts, next);
    reportSuccess('contacts');
    renderContacts();
  } catch (err) {
    reportError('contacts', describeApiError('load contacts', err));
  }
}

newContactBtn.addEventListener('click', () => { contactForm.hidden = false; });
cancelBtn.addEventListener('click', () => { contactForm.hidden = true; });

async function init() {
  await loadAccounts();
  await loadContacts();
}

init();
