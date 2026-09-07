import { fetchOpportunity, fetchAccount, fetchContacts, updateOpportunity, deleteOpportunity, createContact, updateContact, deleteContact } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { inlineErrorMessage } from './form-errors.js';
import { replaceList } from './list-state.js';

const errorBanner = document.getElementById('error-banner');
const opportunityName = document.getElementById('opportunity-name');
const opportunityFields = document.getElementById('opportunity-fields');
const accountFields = document.getElementById('account-fields');
const contactsList = document.getElementById('contacts-list');

let errorState = new Map();
let opportunity = null;
let account = null;
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

// --- Opportunity load & render (Task 5) ---
function field(dl, label, value) {
  const dt = document.createElement('dt');
  dt.textContent = label;
  const dd = document.createElement('dd');
  dd.textContent = value == null || value === '' ? '—' : String(value);
  dl.appendChild(dt);
  dl.appendChild(dd);
}

function renderOpportunity() {
  opportunityName.textContent = opportunity.name;
  opportunityFields.innerHTML = '';
  field(opportunityFields, 'Stage', opportunity.stage_name);
  field(opportunityFields, 'Amount', opportunity.amount);
  field(opportunityFields, 'Close date', opportunity.close_date);
  field(opportunityFields, 'Probability', opportunity.probability);
  field(opportunityFields, 'Type', opportunity.opportunity_type);
  field(opportunityFields, 'Lead source', opportunity.lead_source);
  field(opportunityFields, 'Next step', opportunity.next_step);
  field(opportunityFields, 'Closed', opportunity.is_closed);
  field(opportunityFields, 'Won', opportunity.is_won);
}

function renderAccount() {
  accountFields.innerHTML = '';
  field(accountFields, 'Name', account.name);
  field(accountFields, 'Industry', account.industry);
  field(accountFields, 'Phone', account.phone);
}

function renderContacts() {
  contactsList.innerHTML = '';
  for (const contact of contacts) {
    const li = document.createElement('li');
    li.dataset.contactId = contact.id;
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
    const summary = document.createElement('span');
    summary.textContent = `${name} — ${contact.title ?? ''} — ${contact.email ?? ''}`;
    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-contact-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openContactForm(contact));
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'delete-contact-btn';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', () => removeContact(contact.id));
    li.append(summary, editBtn, removeBtn);
    contactsList.appendChild(li);
  }
}

function getOpportunityId() {
  return new URLSearchParams(window.location.search).get('id');
}

async function loadDetail() {
  const id = getOpportunityId();
  try {
    opportunity = await fetchOpportunity(id);
    reportSuccess('opportunity');
    renderOpportunity();
  } catch (err) {
    reportError('opportunity', describeApiError('load opportunity', err));
    return;
  }
  try {
    account = await fetchAccount(opportunity.account_id);
    reportSuccess('account');
    renderAccount();
  } catch (err) {
    reportError('account', describeApiError('load account', err));
  }
  try {
    contacts = await fetchContacts(opportunity.account_id);
    reportSuccess('contacts');
    renderContacts();
  } catch (err) {
    reportError('contacts', describeApiError('load contacts', err));
  }
}

// --- Opportunity edit/delete (Task 6) ---
const editBtn = document.getElementById('edit-opportunity-btn');
const deleteBtn = document.getElementById('delete-opportunity-btn');
const editForm = document.getElementById('edit-opportunity-form');
const editError = document.getElementById('edit-opportunity-error');
const cancelEditBtn = document.getElementById('cancel-edit-opportunity-btn');

function openEditForm() {
  if (!opportunity) return;
  editForm.elements.name.value = opportunity.name;
  editForm.elements.amount.value = opportunity.amount ?? '';
  editForm.elements.close_date.value = opportunity.close_date;
  editError.textContent = '';
  editForm.hidden = false;
}

editBtn.addEventListener('click', openEditForm);
cancelEditBtn.addEventListener('click', () => { editForm.hidden = true; });

editForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    name: editForm.elements.name.value,
    amount: editForm.elements.amount.value === '' ? null : Number(editForm.elements.amount.value),
    close_date: editForm.elements.close_date.value,
  };
  try {
    opportunity = await updateOpportunity(opportunity.id, payload);
    editForm.hidden = true;
    reportSuccess('opportunity');
    renderOpportunity();
  } catch (err) {
    editError.textContent = inlineErrorMessage(err);
  }
});

deleteBtn.addEventListener('click', async () => {
  if (!window.confirm('Delete this opportunity?')) return;
  try {
    await deleteOpportunity(opportunity.id);
    window.location.href = 'index.html';
  } catch (err) {
    reportError('opportunity', describeApiError('delete opportunity', err));
  }
});

// --- Contact CRUD (Task 7) ---
const newContactBtn = document.getElementById('new-contact-btn');
const contactForm = document.getElementById('contact-form');
const contactFormError = document.getElementById('contact-form-error');
const contactIdInput = document.getElementById('contact-id-input');
const cancelContactBtn = document.getElementById('cancel-contact-form-btn');

function openContactForm(contact) {
  contactIdInput.value = contact ? contact.id : '';
  contactForm.elements.first_name.value = contact?.first_name ?? '';
  contactForm.elements.last_name.value = contact?.last_name ?? '';
  contactForm.elements.email.value = contact?.email ?? '';
  contactForm.elements.title.value = contact?.title ?? '';
  contactFormError.textContent = '';
  contactForm.hidden = false;
}

newContactBtn.addEventListener('click', () => openContactForm(null));
cancelContactBtn.addEventListener('click', () => { contactForm.hidden = true; });

async function refreshContacts() {
  contacts = replaceList(contacts, await fetchContacts(opportunity.account_id));
  renderContacts();
}

contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    account_id: opportunity.account_id,
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
  try {
    await refreshContacts();
    reportSuccess('contacts');
  } catch (err) {
    reportError('contacts', describeApiError('refresh contacts', err));
  }
});

async function removeContact(id) {
  if (!window.confirm('Delete this contact?')) return;
  try {
    await deleteContact(id);
    await refreshContacts();
    reportSuccess('contacts');
  } catch (err) {
    reportError('contacts', describeApiError('delete contact', err));
  }
}

loadDetail();
