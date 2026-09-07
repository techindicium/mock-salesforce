import { fetchAccounts, fetchContacts, resolveAccountName, createContact, updateContact, deleteContact } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';
import { inlineErrorMessage } from './form-errors.js';

const errorBanner = document.getElementById('error-banner');
const listEl = document.getElementById('all-contacts-list');
const emptyState = document.getElementById('contacts-empty-state');
const accountSelect = document.getElementById('contact-account-select');
const newContactBtn = document.getElementById('new-contact-btn');
const contactForm = document.getElementById('contact-form');
const contactFormError = document.getElementById('contact-form-error');
const contactIdInput = document.getElementById('contact-id-input');
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

// --- Contact CRUD (Task 4) ---

function openContactForm(contact) {
  contactIdInput.value = contact ? contact.id : '';
  accountSelect.value = contact?.account_id ?? '';
  contactForm.elements.first_name.value = contact?.first_name ?? '';
  contactForm.elements.last_name.value = contact?.last_name ?? '';
  contactForm.elements.email.value = contact?.email ?? '';
  contactForm.elements.title.value = contact?.title ?? '';
  contactFormError.textContent = '';
  contactForm.hidden = false;
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
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-contact-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openContactForm(contact));
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'delete-contact-btn';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', async () => {
      try {
        await deleteContact(contact.id);
      } catch (err) {
        reportError('delete', describeApiError('delete contact', err));
        return;
      }
      try {
        await loadContacts();
        reportSuccess('delete');
      } catch (err) {
        reportError('contacts', describeApiError('load contacts', err));
      }
    });
    li.append(summary, editBtn, deleteBtn);
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

newContactBtn.addEventListener('click', () => openContactForm(null));
cancelBtn.addEventListener('click', () => { contactForm.hidden = true; });

contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: Number(accountSelect.value),
    first_name: contactForm.elements.first_name.value || null,
    last_name: contactForm.elements.last_name.value,
    email: contactForm.elements.email.value || null,
    title: contactForm.elements.title.value || null,
  };
  try {
    if (contactIdInput.value) {
      await updateContact(contactIdInput.value, payload);
    } else {
      await createContact(payload);
    }
  } catch (err) {
    contactFormError.textContent = inlineErrorMessage(err);
    return;
  }
  contactForm.hidden = true;
  await loadContacts();
});

async function init() {
  await loadAccounts();
  await loadContacts();
}

init();
