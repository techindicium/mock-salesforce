import { getPageHelp, NAV_OVERVIEW } from './help-content.js';

const helpBtn = document.getElementById('help-btn');
const helpPanel = document.getElementById('help-panel');
const helpPanelTitle = document.getElementById('help-panel-title');
const helpPanelBody = document.getElementById('help-panel-body');
const helpNavOverview = document.getElementById('help-nav-overview');

function renderNavOverview() {
  helpNavOverview.innerHTML = '';
  for (const entry of NAV_OVERVIEW) {
    const li = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = entry.label;
    li.append(strong, document.createTextNode(` — ${entry.description}`));
    helpNavOverview.appendChild(li);
  }
}

function openPanel() {
  const mainId = document.querySelector('main')?.id ?? '';
  const help = getPageHelp(mainId);
  helpPanelTitle.textContent = help.title;
  helpPanelBody.textContent = help.body;
  renderNavOverview();
  helpPanel.hidden = false;
  helpBtn.setAttribute('aria-expanded', 'true');
}

function closePanel() {
  helpPanel.hidden = true;
  helpBtn.setAttribute('aria-expanded', 'false');
}

helpBtn.addEventListener('click', (event) => {
  event.stopPropagation();
  if (helpPanel.hidden) {
    openPanel();
  } else {
    closePanel();
  }
});

document.addEventListener('click', (event) => {
  if (helpPanel.hidden) return;
  if (helpPanel.contains(event.target) || helpBtn.contains(event.target)) return;
  closePanel();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !helpPanel.hidden) {
    closePanel();
  }
});
