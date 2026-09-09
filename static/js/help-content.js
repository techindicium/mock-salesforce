export const HELP_CONTENT = {
  'board': {
    title: 'Opportunities',
    body: "This is your sales pipeline. Each column is a deal stage — move a card to a new " +
      "column to advance it. Click a card to open its full detail page. Use the Account " +
      "dropdown above to filter to one account's deals.",
  },
  'deal-detail': {
    title: 'Deal detail',
    body: "Full detail for one Opportunity: its fields, the owning Account, and that " +
      "Account's Contacts. Edit or delete the deal here, and manage its Contacts directly.",
  },
  'accounts-page': {
    title: 'Accounts',
    body: 'Every Account (company) in the system. Expand a row\'s "Contacts" disclosure to ' +
      'see and manage its people, or start a new Opportunity for that Account right from its row.',
  },
  'contacts-page': {
    title: 'Contacts',
    body: 'Every Contact across every Account, in one list. Use this when you want to find or ' +
      "manage a person without first navigating to their Account.",
  },
  'leads-page': {
    title: 'Leads',
    body: 'Unqualified prospects, captured before they have an Account or Opportunity. ' +
      'Qualify a Lead by editing its Status/Rating, then click "Convert" to turn it into a ' +
      'real Account and Contact (and optionally an Opportunity).',
  },
  'help-center-page': {
    title: 'Help Center',
    body: "You're already in the Help Center — browse a category below, or use the search " +
      'box to jump straight to a topic.',
  },
};

export const NAV_OVERVIEW = [
  { label: 'Opportunities', description: 'The sales pipeline kanban board.' },
  { label: 'Accounts', description: 'Companies you sell to, with their Contacts and deals.' },
  { label: 'Contacts', description: 'Every person across every Account.' },
  { label: 'Leads', description: 'Unqualified prospects, ready to qualify and convert.' },
];

const FALLBACK_HELP = {
  title: 'SalesStrength',
  body: 'Use the nav above to get around SalesStrength.',
};

export function getPageHelp(mainId) {
  return HELP_CONTENT[mainId] ?? FALLBACK_HELP;
}
