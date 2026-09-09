import { FAQ_CATEGORIES, filterFaqs } from './faq-content.js';

const searchInput = document.getElementById('faq-search');
const listEl = document.getElementById('faq-list');
const emptyState = document.getElementById('faq-empty-state');

function renderFaqs(categories) {
  listEl.innerHTML = '';
  emptyState.hidden = categories.length !== 0;

  for (const cat of categories) {
    const section = document.createElement('section');
    section.className = 'faq-category';

    const heading = document.createElement('h2');
    heading.textContent = cat.category;
    section.appendChild(heading);

    for (const item of cat.items) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = item.question;
      const answer = document.createElement('p');
      answer.textContent = item.answer;
      details.append(summary, answer);
      section.appendChild(details);
    }

    listEl.appendChild(section);
  }
}

searchInput.addEventListener('input', () => {
  renderFaqs(filterFaqs(FAQ_CATEGORIES, searchInput.value));
});

renderFaqs(FAQ_CATEGORIES);
