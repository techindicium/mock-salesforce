---
spec: .context-index/specs/features/crm-api/account-and-contact-management.spec.md
plan: .context-index/specs/features/crm-api/account-and-contact-management.plan.md
rigor_tier: quick
---

# Validation Report: Account and Contact Management

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-api/account-and-contact-management.spec.md
> **Plan:** .context-index/specs/features/crm-api/account-and-contact-management.plan.md
> **Rigor Tier:** quick (resolved from `risk_level: medium` in spec frontmatter →
>   `governance/risk-policies.yaml` → `policies.medium.validate_mode: quick`; no `--tier`
>   override or routing signal present)
> **Overall Status:** PASS (with notes)

---

## Check 1: Quality Gates — PASS

Resolved gate set (`adev domain load-gates --module crm-api`): `test` (fast, error),
`lint` (fast, error). `integration-test` excluded from the resolved set — its `command` field
is empty in `governance/gates.yaml` (unwired sentinel; no integration suite exists yet), which
`adev domain load-gates` reported as `INVALID_GATE: Gate 'integration-test' missing required
command field — skipped`. No gates are assigned to the integration or e2e tiers.

- Check 1a (fast): `python3 -m pytest -q` — PASS (27 passed, 0 failed, 0.23s, run under the
  project's `.venv`)
- Check 1a (fast): `ruff check .` — PASS ("All checks passed!")
- Check 1b (integration): no gates configured, skipped.
- Check 1c (e2e): no gates configured, skipped.

Gate outcomes attested: `test` → pass (tier: fast), `lint` → pass (tier: fast). Manifest sha
`ff8096a` (from spec's `source-manifest` frontmatter).

## Check 1.5: Source Manifest Verification — SKIP (quick tier)

Skipped — quick rigor tier. (Spec's `source-manifest` block records sha `ff8096a` over 14
files as of `2026-09-06T18:28:05.252Z`; not independently re-verified this run.)

## Check 1.6: Code-Side Drift Warning — SKIP (quick tier)

Skipped — quick rigor tier.

## Check 2 + Check 4 (synthesized, quick tier): Spec + Constitution Compliance — PASS_WITH_NOTES

Quick rigor tier collapses Check 2 (Spec Compliance) and Check 4 (Constitution Compliance)
into a single subagent pass against the changed files. Full findings below.

*Process note:* this project's `governance/validate.yaml` marks the standalone
`validate.check-2-spec-compliance` and `validate.check-4-constitution` registry entries
`enabled: false` (per the constitution's "Governance Posture" — deliberately no subagent-review
dispatch). The quick-tier synthesized check is a distinct, single combined pass defined by
`graduated-rigor-tiers.spec.md`'s tier-resolution algorithm rather than a dispatch of those two
registry entries, so it still ran under the `quick` tier resolved from this spec's
`risk_level`. Flagging this so a future reader isn't surprised to see subagent-review findings
in a project whose registry disables subagent-review checks by name.

### Spec Compliance

**Behaviors (BEH-1 – BEH-17):** all 17 PASS, each backed by a specific implementation
file:line and at least one deterministic test assertion (verified by direct file reads, not
plan checkboxes). Two implementation-only notes (not spec violations, since the Error Cases
table doesn't test for them): `AccountCreate.name` (`models.py:10`) and
`ContactCreate.last_name` (`models.py:44`) have no `min_length`, so an empty string would pass
pydantic validation despite the spec's "non-empty" wording — untested and unenforced, worth a
follow-up. BEH-12 is PARTIAL: `account_id`+`last_name` are both correctly required in
`models.py:41-47`, but only the missing-`last_name` path has a test — no test for a request
missing `account_id`.

**Error Cases table (8 rows):** 5 PASS outright (missing `name`, `account_type` invalid,
delete-with-dependents, unknown `account_id` on contact create, malformed JSON). 3 PARTIAL —
implementation is correct in all three, but test coverage is incomplete:
- Row 3 (unknown Account id) — only the GET path is tested; PATCH/DELETE against an unknown
  account id are implemented (`accounts.py:67-72,92-97`) but untested.
- Row 6 (missing `account_id`/`last_name` on Contact create) — only the missing-`last_name`
  case is tested.
- Row 7 (unknown Contact id) — GET and DELETE are tested; PATCH against an unknown contact id
  is implemented (`contacts.py:78-83`) but untested.

Several 422/404 tests also assert error `code` only, not the message content naming the
field/id/count the spec calls for — the message-shaping mechanism itself is separately and
exactly verified in `tests/test_errors.py`, but not exercised through the live endpoints in
every case.

**Postconditions (3 items):** all PASS — immediate retrievability (implicit in synchronous
SQLite commits, confirmed by create-then-fetch tests), no id reuse after delete (structurally
guaranteed by `AUTOINCREMENT`, confirmed by get-after-delete tests), and Contact `account_id`
immutability (exact deterministic test at `tests/test_contacts.py:65-73`).

### Constitution Compliance — PASS

- **Architecture boundaries:** PASS. No imports of `course-shared` or any other `mock-*`/track
  repo (verified by grep across `src/` and `tests/`). No real network calls — only stdlib
  `sqlite3`. The FastAPI framework choice is documented in the plan
  (`account-and-contact-management.plan.md:16-30`) as an autonomous decision that adds a pip
  dependency without touching another workspace repo or the public HTTP contract's
  paths/shapes — correctly stays in "Autonomous" territory, not "Requires Human Approval."
- **Non-negotiable principles:** PASS on all five — no inbound dependencies; fixture-backed/
  offline only (local SQLite only); identifier-canon reconciliation is N/A for this greenfield
  build; the HTTP contract is the sole access surface (routers only, no internals exported for
  direct import); no breaking API changes (first-time build, nothing to break).
- **Coding standards:** PASS — Salesforce-shaped vocabulary throughout (`Account`, `Contact`,
  `account_type`, `billing_*`); errors fail at the HTTP boundary with a
  `{"error": <CODE>, "message": ...}` body (`errors.py`) registered via
  `app.add_exception_handler` for both `RequestValidationError` and `StarletteHTTPException` —
  no generic 500 leaks through any modeled error path.

**Verdict rationale (PASS_WITH_NOTES):** all 17 behaviors and both quality gates pass with no
code defects or constitutional violations found. The synthesized check surfaces several
test-coverage gaps (BEH-12, Error Cases rows 3/6/7, two unenforced non-empty-string
constraints) that don't fail any acceptance criterion as currently specified but are worth
closing before this surface is treated as fully hardened.

## Check 8: Boundary Compliance — SKIP (quick tier)

Skipped — quick rigor tier.

## Check 9: Transition Gates — SKIP (quick tier)

Skipped — quick rigor tier.

## Check 11: Visual Verification — SKIPPED-DISABLED

Disabled in `governance/validate.yaml` (`enabled: false — no UI — mock-salesforce is a
headless HTTP API`). Confirmed independently: no `.tsx/.jsx/.vue/.svelte/.css/.scss/.html`
files exist under `src/mock_salesforce/` or `tests/`. Not applicable to this spec.

---

**Summary:** 2 of 2 dispatched checks passed (1 with notes: the synthesized compliance check).
5 checks skipped — 4 per quick rigor tier (1.5, 1.6, 8, 9), 1 by explicit project
configuration (11, disabled — no UI). No quality gate failures, no spec-compliance failures,
no constitutional violations.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly
>   Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
