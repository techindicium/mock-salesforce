---
spec: .context-index/specs/features/crm-api/fixture-seeding.spec.md
plan: .context-index/specs/features/crm-api/fixture-seeding.plan.md
validated-at: 2026-09-06
rigor-tier: quick
overall-status: PASS_WITH_NOTES
---

# Validation Report: Fixture seed data

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-api/fixture-seeding.spec.md
> **Plan:** .context-index/specs/features/crm-api/fixture-seeding.plan.md
> **Rigor Tier:** quick (resolved via `governance/risk-policies.yaml` — `risk_level: low` →
>   `validate_mode: quick`; no explicit `--tier` or routing override supplied)
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS

Gate set resolved via `adev domain load-gates` from `.context-index/governance/gates.yaml`
(2 usable gates; `integration-test` excluded — `INVALID_GATE: missing required command field`).

- **Check 1a (fast tier):**
  - `test` — `python3 -m pytest -q` — **PASS** (51 passed, 4 warnings, 0.44-0.49s)
  - `lint` — `ruff check .` — **PASS** (All checks passed!)
- **Check 1b (integration tier):** no gates configured (unwired sentinel `command: ""`) — skipped, not failed.
- **Check 1c (e2e tier):** no gates configured — skipped.

Gate outcomes attested: `test` → pass, `lint` → pass (manifest-sha: `d29a6a5`).

## Check 1.5: Source Manifest Verification — PASS

Run in full for extra rigor (not required at quick tier, but already gathered): `adev source-manifest verify`
reports `PASS — source manifest matches (sha: d29a6a5)`. All 7 manifest files
(`src/mock_salesforce/app.py`, `src/mock_salesforce/seed.py`, `tests/test_seed_accounts.py`,
`tests/test_seed_contacts.py`, `tests/test_seed_idempotency.py`, `tests/test_seed_ids.py`,
`tests/test_seed_opportunities.py`) are confirmed git-tracked with real commits (`8c24881`,
`0d836be`, `4ac1040`, `5245ff2`, `fe4c343`).

## Check 1.6: Code-Side Drift Warning — PASS (no drift)

`adev verify spec --check-drift` → `{"drifted":false}`. No `drift_detected` flag set.

## Check 2 / Check 4 — Synthesized Compliance Check (quick tier) — PASS_WITH_NOTES

Quick rigor tier fuses Spec Compliance (Check 2) and Constitution Compliance (Check 4) into a
single pass against the changed files. All citations below come from files read directly in
this validation run (`src/mock_salesforce/seed.py`, `src/mock_salesforce/app.py`,
`tests/test_seed_accounts.py`, `tests/test_seed_contacts.py`, `tests/test_seed_opportunities.py`,
`tests/test_seed_idempotency.py`, `tests/test_seed_ids.py`, the plan, and `git show`/`git log`).

### Spec Compliance

| Criterion | Verdict | Notes |
|---|---|---|
| BEH-1 (10 canon accounts seeded, no placeholder text) | PASS | `seed.py:18-39` `SEED_ACCOUNTS` — 10 rows, canon names, `industry: "Logistics and Supply Chain"`, real `billing_country` values; `tests/test_seed_accounts.py:189-211` asserts exact name set and rejects `"TBD"/"Lorem"/""` |
| BEH-2 (6+ Named People as Contacts across 4+ accounts) | PASS | `seed.py:42-59` `SEED_CONTACTS` — 8 rows across 6 distinct accounts (Nordkai x2, Halden, Sunder, Brightpath, Kestrel, Tavares, Meseta); `tests/test_seed_contacts.py:334-341` asserts `>= 6` contacts, `>= 4` distinct accounts, non-empty `last_name`/`title` |
| BEH-3 (1+ Opportunity/account, 5+ stages incl. Closed Won/Lost) | PASS | `seed.py:62-104` `SEED_OPPORTUNITIES` — 10 rows, one per account, 10 distinct `stage_name` values including `Closed Won` (Tavares) and `Closed Lost` (Kestrel); `tests/test_seed_opportunities.py:449-461` asserts every account id is covered, `>= 5` stages, both closed stages present, and `is_closed`/`is_won` derivation is correct per row |
| BEH-4 (idempotent — no reseed/duplication on restart) | PASS | `seed.py:190-192` guards on `SELECT COUNT(*) FROM accounts` and returns immediately if non-zero; `tests/test_seed_idempotency.py` starts two `TestClient` instances against the same `DB_PATH` and asserts exactly 10/8/10 rows after both |
| BEH-5 (no seeded id matches a canon reserved scheme) | PASS | Ids are `cur.lastrowid` (plain SQLite `AUTOINCREMENT` integers) by construction — `seed.py:107-181`; `tests/test_seed_ids.py:9-23` regex-asserts no id string matches any of the 10 reserved canon prefixes (`ACCOUNT-`, `TICKET-`, `POLICY-`, etc.) |
| Postconditions (immediate queryability via GET, no canon-owned endpoint exposed) | PASS | `app.py:20-24` calls `seed_if_empty(conn)` inside `on_startup`, before `conn.close()`, so data is committed before the app serves traffic; `next_step` text (`seed.py:67`) narratively references `INCIDENT-02` as read-only text, not a field/endpoint |
| Error Cases: `SEED_DATA_INVALID` names the offending row | PASS | `seed.py:108-114` wraps `pydantic.ValidationError` at the per-row construction site (not around the whole loop), naming the row by `name`; `tests/test_seed_ids.py:722-733` asserts the bad account's name appears in the message |
| Error Cases: `SEED_DB_NOT_WRITABLE` names the path | PASS | `seed.py:198-209` wraps `sqlite3.OperationalError` around the write phase, naming `get_db_path()`; `tests/test_seed_ids.py:737-753` triggers via a `Connection` subclass that raises on `commit()` (documented advisory in the plan: the real filesystem-unwritable path is pre-empted by `init_db`'s own commit, which runs first — the wrapping still correctly covers the seed-phase write, which is what this spec owns) |
| "No runtime file read outside this repository" | PASS | `tests/test_seed_ids.py:712-719` greps the actual `seed.py` source at runtime for `"course-shared"` and `"open("` and asserts neither is present — confirmed independently: `grep -n "course-shared\|open(" src/mock_salesforce/seed.py` returns no matches |

**Test-integrity check:** No loose matchers, conditional skips, or vacuous assertions found in
the five `test_seed_*.py` files — all assert exact set/count equality against hardcoded seed
data (e.g. `EXPECTED_NAMES` exact set, `len(contacts) >= 6` with an explicit fixed-8-row backing
constant, exact stage-set membership), not on ambient/dynamic values.

### Scope Expansion sub-finding — WARNING (justified)

Declared scope (`source-manifest.files`) is the 7 files above. `git show --stat` on the 5
fixture-seeding commits shows commit `5245ff2` ("seed fixture data once on startup...") also
touched **`tests/test_accounts.py`, `tests/test_contacts.py`, `tests/test_opportunities.py`** —
three files outside the declared scope.

Reviewed the actual diffs: all three changes narrow existing assertions from "the unfiltered
list is empty/exact" to "the accounts/contacts/opportunities this test itself created, filtered
by id, match exactly" — a direct, necessary consequence of seeding no longer leaving the
database empty on startup. No assertion was weakened (each still asserts an exact set/count);
the commit message documents the rationale and notes a prior review cycle tightened a
`>= 6` contacts-count assertion in the new idempotency test to an exact `== 8` specifically to
avoid a loosened check. **This is a legitimate, narrowly-scoped, well-justified scope expansion**,
not gaming — but it is real: the spec's `source-manifest.files` does not list these three files.
Recommended action: update the spec's `source-manifest.files` to include
`tests/test_accounts.py`, `tests/test_contacts.py`, `tests/test_opportunities.py`, or note the
dependency explicitly in the spec's Preconditions.

This sub-finding is why the check's aggregate verdict is **PASS_WITH_NOTES** rather than PASS.

### Constitution Compliance

- **Architecture Boundaries** — PASS. No new service or table created (seed data writes through
  the existing `accounts`/`contacts`/`opportunities` tables); no auth code exists or was touched;
  `grep -rn "course-shared\|open(" src/mock_salesforce/seed.py` returns no matches, and no new
  entry was added to `requirements.txt`/`pyproject.toml` (seed.py only imports `pydantic`,
  `sqlite3`, `datetime`, and the project's own `mock_salesforce.db`/`mock_salesforce.models`,
  all already-used dependencies).
- **Non-Negotiable Principles** — PASS.
  - "No inbound dependencies": confirmed via the grep above — no import of `course-shared` or
    any other repo.
  - "Fixture-backed, offline only": `seed.py` makes no network call and reads no file outside
    this repo; canon reconciliation is hardcoded into the `SEED_*` constants at authoring time
    per the spec's own Preconditions section.
  - "Identifiers reconcile with the shared canon": ids are plain `AUTOINCREMENT` integers
    (`seed.py:107-181`, confirmed by `tests/test_seed_ids.py:9-23`), never `ACCOUNT-NNNN`-shaped.
  - "The HTTP contract is the boundary": seeding is triggered from `on_startup`
    (`app.py:20-24`), not a new endpoint; no HTTP surface changed for this feature.
  - "Breaking API changes are coordinated, not silent": no existing endpoint's request/response
    shape changed; the three out-of-scope test edits (see Scope Expansion above) adjust
    assertions to account for pre-existing data, not endpoint behavior.
- **Coding Standards** — PASS. `seed.py`'s `_insert_account`/`_insert_contact`/`_insert_opportunity`
  helpers mirror `accounts.py`/`contacts.py`/`opportunities.py`'s own insert-then-`lastrowid`
  shape line for line (confirmed by reading both the plan's stated intent and the actual
  `seed.py` code); naming (`stage_name`, `opportunity_type`, `lead_source`, `SeedDataError`)
  mirrors Salesforce vocabulary and the project's existing error-shape convention
  (`errors.py`'s `{error, message}` style, per the plan's Task 5 context notes).

**Synthesized verdict: PASS_WITH_NOTES** — no FAIL-level or uncited findings; one non-blocking,
well-justified scope-expansion finding (declared `source-manifest.files` under-lists three
touched test files). No code defect.

## Check 8: Boundary Compliance — SKIP

`adev boundaries check --json` → `verdict: SKIP`, reason "no boundary rules declared" (64 files
checked, 0 findings). Also true by tier default (would have been skipped as quick-tier reference
information regardless).

## Check 9: Transition Gates — SKIP

`adev gate transitions --transition implement-to-validate --json` → `verdict: SKIP`, reason
"no transitions configured" (`governance/gates.yaml` declares `transitions: {}`). Also true by
tier default.

## Check 11: Visual Verification — N/A

No UI files in this implementation's diff (headless HTTP API only: `.py` source and test files).
"No UI files in implementation diff — visual verification not applicable."

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES (4 warnings, 0 errors)

`adev gate doctor --json` — no error-severity findings.

- `gate-doctor/gate-set-divergence` (warning) — raw `gates.yaml` declares `integration-test`,
  absent from the domain-merged set every consumer reads.
- `gate-doctor/ci-config-missing` (warning) — no CI configuration found in this repo.
- `gate-doctor/runner-unknown` (warning) — `lint` gate (`ruff check .`) has no known test-runner
  signature; collection not verifiable for it (expected — it's a linter, not a test runner).
- `gate-doctor/empty-command` (warning) — `integration-test` declares no command (documented as
  an intentional unwired sentinel in the plan).

None of these affect Check 1's outcome; all are pre-existing, already-acknowledged project
posture (course-fixture repo, no CI, integration tier deliberately unwired).

---

**Summary:** 8 checks ran (Check 1, 1.5, 1.6, synthesized Check 2/4, 8, 9, 14) — all PASS or
PASS_WITH_NOTES. Check 11 recorded N/A (no UI files). 0 failures. One actionable, non-blocking
note: update the spec's `source-manifest.files` to include the three pre-existing CRUD test
files that a follow-on commit had to adjust once seeding made a "fresh" database non-empty.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally reflects the `quick` rigor tier (`graduated-rigor-tiers.spec.md`):
> Checks 2/4 ran as one synthesized dispatch rather than two separate ones. Checks 1.5, 1.6, 8,
> and 9 were run in full despite quick-tier permitting their skip (their results were already
> gathered and all came back clean/SKIP; none contradicts what tier policy would have recorded).
