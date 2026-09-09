export const FAQ_CATEGORIES = [
  {
    category: 'General',
    items: [
      {
        question: 'What is SalesStrength?',
        answer: 'SalesStrength is a lightweight CRM for tracking Accounts (companies), ' +
          'Contacts (people), Opportunities (deals), and Leads (unqualified prospects). ' +
          'Everything you see is stored locally — no real network or third-party service is ' +
          'involved.',
      },
      {
        question: 'Can I undo a delete?',
        answer: 'No — deleting an Account, Contact, Opportunity, or Lead is permanent. Every ' +
          'delete action asks you to confirm first, so make sure before you click through.',
      },
      {
        question: 'Why does the app look different after a restart?',
        answer: 'It shouldn\'t — your data lives in a local database file that persists across ' +
          'restarts. If you see completely different records, you (or someone) may be pointed ' +
          'at a different database file or a freshly reset one.',
      },
    ],
  },
  {
    category: 'Opportunities',
    items: [
      {
        question: 'How do I move a deal to a different stage?',
        answer: 'Drag its card from one column to another on the Opportunities board, or open ' +
          'the deal\'s detail page and edit its Stage field directly.',
      },
      {
        question: 'What do the stage names mean?',
        answer: 'Every Opportunity moves through the same ten fixed stages, from Prospecting ' +
          'through Closed Won or Closed Lost. The set of stages is fixed and cannot be ' +
          'customized.',
      },
      {
        question: 'How do I see only one Account\'s deals?',
        answer: 'Use the Account dropdown above the board to filter it down to a single ' +
          'Account\'s Opportunities. Choose "All accounts" to see everything again.',
      },
    ],
  },
  {
    category: 'Accounts',
    items: [
      {
        question: 'How do I add a Contact to an Account?',
        answer: 'Open the Account\'s row on the Accounts page and expand its "Contacts" ' +
          'disclosure, then click "New contact".',
      },
      {
        question: 'Why can\'t I delete an Account?',
        answer: 'An Account can\'t be deleted while it still has any Contact or Opportunity ' +
          'attached to it. Delete or reassign those first.',
      },
      {
        question: 'How do I start a new deal for a company I already track?',
        answer: 'Click "New opportunity" directly on that Account\'s row on the Accounts page.',
      },
    ],
  },
  {
    category: 'Contacts',
    items: [
      {
        question: 'How is the Contacts page different from an Account\'s Contacts list?',
        answer: 'The Contacts page lists every Contact across every Account in one place. An ' +
          'Account\'s own Contacts disclosure only shows the people tied to that one Account.',
      },
      {
        question: 'How do I tell which company a Contact belongs to?',
        answer: 'Each row on the Contacts page shows the owning Account\'s name alongside the ' +
          'person\'s name, title, and email.',
      },
    ],
  },
  {
    category: 'Leads',
    items: [
      {
        question: 'What\'s the difference between a Lead and a Contact?',
        answer: 'A Lead is an unqualified prospect that isn\'t attached to an Account yet — ' +
          'just a name, company, and contact info. A Contact always belongs to a real Account. ' +
          'Converting a Lead is what turns it into an Account + Contact.',
      },
      {
        question: 'I clicked "Save lead" and nothing seemed to happen — why?',
        answer: 'Last name and Company are both required on a Lead. If either is blank, the ' +
          'form won\'t submit — it now shows "Last name and Company are required." inline so ' +
          'this isn\'t silent anymore.',
      },
      {
        question: 'What happens when I click "Convert" on a Lead?',
        answer: 'It creates a new Account and Contact from the Lead\'s info (or attaches to ' +
          'existing ones, if driven via the API/MCP tools with an account_id), optionally ' +
          'creates an Opportunity, and marks the Lead as converted.',
      },
      {
        question: 'Can I undo a Lead conversion?',
        answer: 'No — conversion is one-way, matching real Salesforce. A converted Lead is ' +
          'frozen: it can no longer be edited, deleted, or converted again.',
      },
      {
        question: 'Why can\'t I edit a Lead anymore?',
        answer: 'It has already been converted. Converted Leads are read-only by design — make ' +
          'changes on the Account/Contact/Opportunity it produced instead.',
      },
    ],
  },
];

export function filterFaqs(categories, query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return categories;
  return categories
    .map((cat) => ({
      category: cat.category,
      items: cat.items.filter(
        (item) =>
          item.question.toLowerCase().includes(needle) ||
          item.answer.toLowerCase().includes(needle)
      ),
    }))
    .filter((cat) => cat.items.length > 0);
}
