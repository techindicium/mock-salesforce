import { fetchAccounts, createAccount, updateAccount, deleteAccount, createOpportunity, fetchContacts, createContact, updateContact, deleteContact } from './api.js';
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

// --- Account CRUD (Task 10) ---

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

    const newOppBtn = document.createElement('button');
    newOppBtn.type = 'button';
    newOppBtn.className = 'account-new-opportunity-btn';
    newOppBtn.textContent = 'New opportunity';
    newOppBtn.addEventListener('click', () => openNewOpportunityForm(account));

    const contactsDetails = document.createElement('details');
    const contactsSummary = document.createElement('summary');
    contactsSummary.textContent = 'Contacts';
    const contactsListEl = document.createElement('ul');
    contactsListEl.className = 'account-contacts-list';
    contactsListEl.dataset.accountId = account.id;
    const newContactBtn = document.createElement('button');
    newContactBtn.type = 'button';
    newContactBtn.className = 'account-new-contact-btn';
    newContactBtn.textContent = 'New contact';
    newContactBtn.addEventListener('click', () => openAccountContactForm(account.id, null));
    let contactsLoaded = false;
    contactsDetails.addEventListener('toggle', () => {
      if (contactsDetails.open && !contactsLoaded) {
        contactsLoaded = true;
        renderAccountContacts(account.id, contactsListEl).catch((err) => {
          contactsLoaded = false;
          reportError('contacts', describeApiError('load contacts', err));
        });
      }
    });
    contactsDetails.append(contactsSummary, contactsListEl, newContactBtn);

    li.append(summary, editBtn, deleteBtn, dependentsMessage, newOppBtn, contactsDetails);
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

// --- Create-opportunity form (Task 11) ---

const newOppForm = document.getElementById('account-new-opportunity-form');
const newOppError = document.getElementById('account-new-opportunity-error');
const newOppAccountIdInput = document.getElementById('new-opp-for-account-id');
const cancelNewOppBtn = document.getElementById('cancel-account-new-opportunity-btn');

// --- Contact CRUD (Task 11) ---

const accountContactForm = document.getElementById('account-contact-form');
const accountContactFormError = document.getElementById('account-contact-form-error');
const accountContactIdInput = document.getElementById('account-contact-id-input');
const accountContactAccountIdInput = document.getElementById('account-contact-account-id-input');
const cancelAccountContactBtn = document.getElementById('cancel-account-contact-form-btn');

const accountContactsCache = new Map();

function openNewOpportunityForm(account) {
  newOppAccountIdInput.value = account.id;
  newOppForm.elements.name.value = '';
  newOppForm.elements.close_date.value = '';
  newOppError.textContent = '';
  newOppForm.hidden = false;
}

cancelNewOppBtn.addEventListener('click', () => { newOppForm.hidden = true; });

newOppForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: Number(newOppAccountIdInput.value),
    name: newOppForm.elements.name.value,
    close_date: newOppForm.elements.close_date.value,
  };
  try {
    const created = await createOpportunity(payload);
    window.location.href = `deal.html?id=${created.id}`;
  } catch (err) {
    newOppError.textContent = inlineErrorMessage(err);
  }
});

function openAccountContactForm(accountId, contact) {
  accountContactAccountIdInput.value = accountId;
  accountContactIdInput.value = contact ? contact.id : '';
  accountContactForm.elements.first_name.value = contact?.first_name ?? '';
  accountContactForm.elements.last_name.value = contact?.last_name ?? '';
  accountContactForm.elements.email.value = contact?.email ?? '';
  accountContactForm.elements.title.value = contact?.title ?? '';
  accountContactFormError.textContent = '';
  accountContactForm.hidden = false;
}

cancelAccountContactBtn.addEventListener('click', () => { accountContactForm.hidden = true; });

async function renderAccountContacts(accountId, listEl) {
  const prior = accountContactsCache.get(accountId) ?? [];
  const next = replaceList(prior, await fetchContacts(accountId));
  accountContactsCache.set(accountId, next);
  listEl.innerHTML = '';
  for (const contact of next) {
    const li = document.createElement('li');
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
    const summary = document.createElement('span');
    summary.textContent = `${name} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-account-contact-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openAccountContactForm(accountId, contact));
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'delete-account-contact-btn';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', async () => {
      if (!window.confirm('Delete this contact?')) return;
      try {
        await deleteContact(contact.id);
      } catch (err) {
        reportError('contacts', describeApiError('delete contact', err));
        return;
      }
      try {
        await renderAccountContacts(accountId, listEl);
      } catch (err) {
        reportError('contacts', describeApiError('refresh contacts', err));
      }
    });
    li.append(summary, editBtn, removeBtn);
    listEl.appendChild(li);
  }
}

accountContactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const accountId = Number(accountContactAccountIdInput.value);
  const payload = {
    account_id: accountId,
    first_name: accountContactForm.elements.first_name.value || null,
    last_name: accountContactForm.elements.last_name.value,
    email: accountContactForm.elements.email.value || null,
    title: accountContactForm.elements.title.value || null,
  };
  const listEl = accountsList.querySelector(`.account-contacts-list[data-account-id="${accountId}"]`);
  try {
    if (accountContactIdInput.value) {
      await updateContact(accountContactIdInput.value, payload);
    } else {
      await createContact(payload);
    }
  } catch (err) {
    accountContactFormError.textContent = inlineErrorMessage(err);
    return;
  }
  accountContactForm.hidden = true;
  if (listEl) {
    try {
      await renderAccountContacts(accountId, listEl);
    } catch (err) {
      reportError('contacts', describeApiError('refresh contacts', err));
    }
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
