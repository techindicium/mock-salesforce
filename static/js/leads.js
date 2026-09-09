import { fetchLeads, createLead, updateLead, deleteLead, convertLead } from './api.js';
import { describeApiError } from './errors.js';
import { setError, clearError, bannerMessage } from './error-state.js';
import { replaceList } from './list-state.js';
import { inlineErrorMessage } from './form-errors.js';

const errorBanner = document.getElementById('error-banner');
const listEl = document.getElementById('leads-list');
const emptyState = document.getElementById('leads-empty-state');
const newLeadBtn = document.getElementById('new-lead-btn');
const leadForm = document.getElementById('lead-form');
const leadFormError = document.getElementById('lead-form-error');
const leadIdInput = document.getElementById('lead-id-input');
const cancelBtn = document.getElementById('cancel-lead-form-btn');

let errorState = new Map();
let leads = [];

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

function openLeadForm(lead) {
  leadIdInput.value = lead ? lead.id : '';
  leadForm.elements.first_name.value = lead?.first_name ?? '';
  leadForm.elements.last_name.value = lead?.last_name ?? '';
  leadForm.elements.company.value = lead?.company ?? '';
  leadForm.elements.title.value = lead?.title ?? '';
  leadForm.elements.email.value = lead?.email ?? '';
  leadForm.elements.phone.value = lead?.phone ?? '';
  leadForm.elements.status.value = lead?.status ?? 'New';
  leadForm.elements.rating.value = lead?.rating ?? '';
  leadFormError.textContent = '';
  leadForm.hidden = false;
}

function renderLeads() {
  listEl.innerHTML = '';
  emptyState.hidden = leads.length !== 0;
  for (const lead of leads) {
    const li = document.createElement('li');
    li.dataset.leadId = lead.id;
    const summary = document.createElement('span');
    summary.textContent =
      `${lead.first_name ?? ''} ${lead.last_name} — ${lead.company} — ` +
      `${lead.status} — ${lead.rating ?? ''}`;
    li.append(summary);

    if (lead.converted) {
      const convertedLabel = document.createElement('span');
      convertedLabel.className = 'lead-converted-label';
      convertedLabel.textContent = 'Converted';
      li.append(convertedLabel);
      listEl.appendChild(li);
      continue;
    }

    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'edit-lead-btn';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => openLeadForm(lead));

    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'delete-lead-btn';
    deleteBtn.textContent = 'Delete';
    const deleteError = document.createElement('span');
    deleteError.className = 'lead-delete-error';
    deleteBtn.addEventListener('click', async () => {
      if (!window.confirm(`Delete lead "${lead.last_name}"?`)) return;
      deleteError.textContent = '';
      try {
        await deleteLead(lead.id);
      } catch (err) {
        deleteError.textContent = inlineErrorMessage(err);
        return;
      }
      try {
        await loadLeads();
        reportSuccess('leads');
      } catch (err) {
        reportError('leads', describeApiError('refresh leads', err));
      }
    });

    const convertBtn = document.createElement('button');
    convertBtn.type = 'button';
    convertBtn.className = 'convert-lead-btn';
    convertBtn.textContent = 'Convert';
    convertBtn.addEventListener('click', async () => {
      let result;
      try {
        result = await convertLead(lead.id);
      } catch (err) {
        reportError('leads', describeApiError('convert lead', err));
        return;
      }
      if (result.converted_opportunity_id != null) {
        window.location.href = `deal.html?id=${result.converted_opportunity_id}`;
      } else {
        window.location.href = 'accounts.html';
      }
    });

    li.append(editBtn, deleteBtn, deleteError, convertBtn);
    listEl.appendChild(li);
  }
}

async function loadLeads() {
  const next = await fetchLeads();
  leads = replaceList(leads, next);
  renderLeads();
}

newLeadBtn.addEventListener('click', () => openLeadForm(null));
cancelBtn.addEventListener('click', () => { leadForm.hidden = true; });

// 'invalid' does not bubble, so listen in the capture phase on the form itself.
// Without this, submitting with Last name or Company blank silently does
// nothing visible beyond the browser's own (easy-to-miss) validation tooltip.
leadForm.addEventListener('invalid', () => {
  leadFormError.textContent = 'Last name and Company are required.';
}, true);

leadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    first_name: leadForm.elements.first_name.value || null,
    last_name: leadForm.elements.last_name.value,
    company: leadForm.elements.company.value,
    title: leadForm.elements.title.value || null,
    email: leadForm.elements.email.value || null,
    phone: leadForm.elements.phone.value || null,
    status: leadForm.elements.status.value,
    rating: leadForm.elements.rating.value || null,
  };
  try {
    if (leadIdInput.value) {
      await updateLead(leadIdInput.value, payload);
    } else {
      await createLead(payload);
    }
  } catch (err) {
    leadFormError.textContent = inlineErrorMessage(err);
    return;
  }
  leadForm.hidden = true;
  try {
    await loadLeads();
    reportSuccess('leads');
  } catch (err) {
    reportError('leads', describeApiError('refresh leads', err));
  }
});

async function init() {
  try {
    await loadLeads();
    reportSuccess('leads');
  } catch (err) {
    reportError('leads', describeApiError('load leads', err));
  }
}

init();
