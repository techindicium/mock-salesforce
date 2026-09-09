---
partial_schema: implement@1
charter: crm-api
status: validated
risk_level: low
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-05
updated: 2026-09-06
kind: behavioral
depends-on:
  - .context-index/specs/features/crm-api/account-and-contact-management.spec.md
  - .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
source-manifest:
  sha: "d29a6a5"
  files:
    - src/mock_salesforce/app.py
    - src/mock_salesforce/seed.py
    - tests/test_seed_accounts.py
    - tests/test_seed_contacts.py
    - tests/test_seed_idempotency.py
    - tests/test_seed_ids.py
    - tests/test_seed_opportunities.py
  computed-at: "2026-09-06T20:37:35.700Z"
drift_detected: true
---

# Live Spec: Fixture seed data

<!-- Live Spec within the crm-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-api/charter.md -->

## Behavioral Contract

### Preconditions

- The `account-and-contact-management` and `opportunity-lifecycle` specs' schemas exist —
  seeding writes through the same Account/Contact/Opportunity tables those specs define.
- Reconciliation with `../course-shared/canon` happens once, at spec-authoring time (this
  document), never at runtime. The values below are hardcoded into this repo's own seed fixture
  module; the running program never opens any file outside this repository. This is
  non-negotiable: a runtime read of `../course-shared/canon/*` would be an inbound dependency on
  another repo, which the constitution forbids outright.
- Canon already reserves an `Account` concept of its own (`ACCOUNT-NNNN`, `course-shared/canon/
  identifiers.md`). This module's Account entity is a distinct, internally-scoped identifier
  space — an auto-assigned integer `id`, never the string form `ACCOUNT-NNNN` — so there is no
  collision by construction. Seeded Account *names* echo canon's ten canonical accounts (by
  name only, as a narrative cross-reference, per the same convention `mock-jira`'s seed data
  uses for `assignee`/`reporter` names) — this module never creates, owns, or exposes an
  endpoint keyed on canon's `ACCOUNT-NNNN` scheme itself.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the API starts against an empty database (no Account rows exist), **then**
  it seeds exactly the ten canonical accounts from `course-shared/canon/company.md`'s Accounts
  table (`Nordkai Logistics`, `Tavares Distribuicao`, `Halden Cold Chain`, `Brightpath Freight`,
  `Meseta Almacenes`, `Kestrel Parts Group`, `Vlietwerk BV`, `Sunder Retail Supply`,
  `Copal Andina`, `Fjordline Depot`), each with a plausible `industry` ("Logistics and Supply
  Chain") and `billing_country` derived from canon's Region column (`EU` → a real EU country,
  `NA` → `United States`, `LATAM` → a real LATAM country), all present and queryable immediately
  once startup completes — no placeholder or lorem-ipsum text in any field.
- **BEH-2** — **When** the ten named Accounts are seeded, **then** at least six of canon's twelve
  Named People (`course-shared/canon/company.md`'s Named People table) are seeded as Contacts,
  distributed across at least four different seeded Accounts, each with a plausible `title`
  derived from their canon Role — never an invented placeholder name.
- **BEH-3** — **When** the ten named Accounts are seeded, **then** at least one Opportunity is seeded
  under each Account, together spanning at least five of the ten fixed `stage_name` values
  (including at least one `Closed Won` and one `Closed Lost`), so a fresh pipeline board shows
  populated columns rather than one column with every card.

**Why 412 and not ten.** The ten named Accounts carry the detail every other system keys on.
The remaining 402 exist so that counting the CRM returns Portwell's real customer number. A
document in the product repository claims "500+", and the exercise is to query the system of
record rather than believe the document. With ten rows in the table there is nothing to find.
The unelaborated Accounts carry no Contacts and no Opportunities, which is also true of most
of a real book of business.

- **BEH-4** — **When** the API starts against a database that already has at least one Account
  row, **then** it performs no seeding — existing data is left untouched, and restarting the
  process any number of times never creates a second copy.
- **BEH-5** — **When** the seed module assigns Account/Contact/Opportunity ids, **then** none of
  them is ever formatted as `ACCOUNT-NNNN`, `TICKET-NNNNNN`, `POLICY-NN`, or any other reserved
  scheme in `course-shared/canon/identifiers.md` — this module's ids are plain auto-incrementing
  integers, a disjoint format from every canon scheme by construction.

### Postconditions

- After a fresh-database startup, `GET /accounts` returns exactly 412 Accounts, ten of them named in canon and the rest unelaborated,
  `GET /contacts` returns the seeded Contacts, and `GET /opportunities` returns the seeded
  Opportunities distributed across at least five distinct `stage_name` values.
- Seeded Opportunity `next_step` text may narratively mention canon entities by their real ID
  (e.g. `INCIDENT-01`) as read-only narrative references, but this module never creates, owns,
  or exposes an endpoint for any canon-owned entity type (canon's Account, Incident, Ticket,
  Article, etc.).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Seed data fails validation (a hardcoded row is malformed) | Startup aborts with a clear error naming the offending row | `SEED_DATA_INVALID` |
| Database file path is not writable | Startup aborts with a clear error naming the path | `SEED_DB_NOT_WRITABLE` |

## System Constitution Reference

- **Principle:** "Identifiers reconcile with the shared canon. Any account, contact, or entity
  ID this API returns must be consistent with `course-shared/canon/identifiers.md` where an
  overlap exists — never invent an ID that could collide with the canon's reserved ranges." —
  This spec exists specifically to satisfy this principle: it documents, at authoring time, why
  this module's Account entity and canon's `ACCOUNT-NNNN` scheme cannot collide (disjoint id
  formats) and reconciles seeded names/people with canon's real records.
- **Principle:** "No inbound dependencies. This repo never depends on `course-shared`...
  Consuming tracks depend on it; it never depends back." — Applies because reconciliation must
  be a one-time authoring-time act (this document), never a runtime file read across the repo
  boundary — see Preconditions.
- **Principle:** "Fixture-backed, offline only." — Applies directly: this is the fixture.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Write the seed fixture module | 412 Accounts of which 10 are named, 6+ Contacts, 10+ Opportunities, values reconciled with canon at authoring time (this spec), committed only in this repo | medium |
| Wire seed-on-empty-database startup check | Run the seed module once, only when no Account rows exist yet | small |
| Idempotency test | Start twice against the same database file; assert exactly 412 Accounts after both runs | small |

## Acceptance Criteria

- [x] Fresh-database startup seeds the ten canon-named Accounts, no placeholder text (BEH-1)
- [x] At least six canon Named People are seeded as Contacts across 4+ Accounts (BEH-2)
- [x] At least one Opportunity per named Account, spanning 5+ stages incl. Closed Won/Lost (BEH-3)
- [x] Restarting against an already-seeded database creates no duplicate rows (BEH-4)
- [x] No seeded id is ever formatted as a canon-reserved scheme (BEH-5)
- [x] The seed module contains no runtime file read outside this repository
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
