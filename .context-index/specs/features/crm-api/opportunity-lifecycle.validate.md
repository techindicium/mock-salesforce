---
spec: .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
plan: .context-index/specs/features/crm-api/opportunity-lifecycle.plan.md
validated-at: 2026-09-06
rigor-tier: quick
overall-status: PASS_WITH_NOTES
---

# Validation Report: Opportunity Lifecycle CRUD

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-api/opportunity-lifecycle.spec.md
> **Plan:** .context-index/specs/features/crm-api/opportunity-lifecycle.plan.md
> **Rigor Tier:** quick (resolved via `governance/risk-policies.yaml` — `risk_level: medium` → `validate_mode: quick`; no explicit `--tier` or routing override supplied)
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS

Gate set resolved via `adev domain load-gates` from `.context-index/governance/gates.yaml` (2 usable gates; `integration-test` excluded — `INVALID_GATE: missing required command field`).

- **Check 1a (fast tier):**
  - `test` — `python3 -m pytest -q` — **PASS** (41 passed, 4 warnings, 0.39s)
  - `lint` — `ruff check .` — **PASS** (All checks passed!)
- **Check 1b (integration tier):** no gates configured (unwired sentinel `command: ""`) — skipped, not failed.
- **Check 1c (e2e tier):** no gates configured — skipped.

Gate outcomes attested: `test` → pass, `lint` → pass (manifest-sha: `1a4d668`).

## Check 1.5: Source Manifest Verification — SKIPPED (quick rigor tier)

Skipped per quick-tier execution rules. For reference, the spec's frontmatter carries a source-manifest (sha `1a4d668`, 6 files, computed 2026-09-06T19:30:20.200Z); all 6 listed files exist on disk and are present in git history via the 5 opportunity-lifecycle commits inspected during Check 2/4 below.

## Check 2 / Check 4 — Synthesized Compliance Check (quick tier) — PASS_WITH_NOTES

Quick rigor tier fuses Spec Compliance (Check 2) and Constitution Compliance (Check 4) into a single subagent dispatch against the changed files. All citations below come from files read in that dispatch.

### Spec Compliance

| Criterion | Verdict | Notes |
|---|---|---|
| BEH-1 (create, defaults Prospecting, 201) | PASS | `models.py` default + `opportunities.py` `_derive_closed_won`; test asserts full body |
| BEH-2 (unknown account_id → 404) | PASS | `opportunities.py` account lookup; test confirms no row persisted via follow-up GET |
| BEH-3 (missing required field → 422) | PASS | Pydantic required fields; test loops all 3 fields |
| BEH-4 (GET list filters) | PASS | dynamic WHERE clause; test asserts exact filtered sets |
| BEH-5 (GET by id, 200) | PASS | test only checks status + name (response_model guarantees shape) |
| BEH-6 (GET by id, 404) | PASS | |
| BEH-7 (PATCH updates + recompute + immutability) | PASS | strongest test in suite (`test_patch_opportunity_ignores_immutable_fields`) proves account_id immutability directly |
| BEH-8 (invalid stage_name → 422) | PARTIAL | code is structurally correct (Literal validated before handler runs, so no-persisted-change is guaranteed by control flow); tests don't assert message names allowed values or explicitly re-GET to confirm no persisted change |
| BEH-9 (DELETE, 204) | PASS | test proves both re-GET 404 and list-empty |
| Postconditions (immediate retrievability, id non-reuse, account_id immutable, is_closed/is_won never stale) | PASS (all 4) | AUTOINCREMENT id non-reuse; immutability test as above; recompute only touches flags when stage_name is part of the update |
| Error Cases: unknown account_id → 404 | PASS | |
| Error Cases: missing required field → 422 | PASS | |
| Error Cases: unknown id on get/patch/delete → 404 | PARTIAL | GET and DELETE not-found paths are tested; **PATCH-not-found has zero test coverage** despite the code path existing |
| Error Cases: invalid stage_name → 422 | PARTIAL | same gap as BEH-8 |
| Error Cases: malformed JSON → 400 | PASS (structural) | handled globally via `errors.py`/`app.py`, route-agnostic; no opportunity-specific test, but mechanism is provably shared |

**Scope Expansion sub-finding:** No scope expansion. Verified via `git show --stat` on all 5 opportunity-lifecycle commits — only the 6 declared source-manifest files were touched; `accounts.py`/`contacts.py` untouched.

### Constitution Compliance

- **Architecture Boundaries** — PASS. One new table (`opportunities`), matching the chartered scope; no auth code exists or was touched; no new dependencies added to `requirements.txt`; `accounts.py`/`contacts.py` confirmed untouched by git history.
- **Non-Negotiable Principles** — PASS. No inbound dependencies (grep confirms only `fastapi`/`mock_salesforce.*`/stdlib imports); fixture-backed/offline only (SQLite only, no network client); HTTP contract is the boundary (feature exposed only via `APIRouter`); no breaking changes to existing endpoints (additive only).
- **Coding Standards** — PASS. Naming mirrors Salesforce vocabulary (`stage_name`, `opportunity_type`, `lead_source`, etc.); router/connection-handling/error-shape patterns match `accounts.py`/`contacts.py` line-for-line as the plan intended.

**Synthesized verdict: PASS_WITH_NOTES** — no FAIL-level or uncited findings; two non-blocking test-quality gaps noted above (PATCH-404 untested; invalid-stage-name tests underspecified). Neither reflects a code defect.

## Check 1.6: Code-Side Drift Warning — SKIPPED (quick rigor tier)

## Check 8: Boundary Compliance — SKIPPED (quick rigor tier)

For reference: `.context-index/governance/boundaries.yaml` declares no rules for this project, so a full-mode run would have recorded SKIP regardless.

## Check 9: Transition Gates — SKIPPED (quick rigor tier)

For reference: `governance/gates.yaml` declares `transitions: {}` (empty) — a full-mode run would have recorded SKIP (no transitions configured) regardless.

## Check 11: Visual Verification — N/A

No UI files in this implementation's diff (headless HTTP API only: `.py` source and test files). "No UI files in implementation diff — visual verification not applicable."

## Check 14: Gate Executability and Test Collection — PASS (4 warnings, 0 errors)

`adev gate doctor --json` — no error-severity findings.

- `gate-doctor/gate-set-divergence` (warning) — raw `gates.yaml` declares `integration-test`, absent from the domain-merged set every consumer reads.
- `gate-doctor/ci-config-missing` (warning) — no CI configuration found in this repo.
- `gate-doctor/runner-unknown` (warning) — `lint` gate (`ruff check .`) has no known test-runner signature; collection not verifiable for it (expected — it's a linter, not a test runner).
- `gate-doctor/empty-command` (warning) — `integration-test` declares no command (documented as an intentional unwired sentinel in the plan).

None of these affect Check 1's outcome; all are pre-existing, already-acknowledged project posture (course-fixture repo, no CI, integration tier deliberately unwired).

---

**Summary:** 3 checks ran (Check 1, synthesized Check 2/4, Check 14) — all PASS or PASS_WITH_NOTES. 5 checks skipped under the quick rigor tier (1.5, 1.6, 8, 9) or as not applicable (11, no UI). 0 failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally reflects the `quick` rigor tier (`graduated-rigor-tiers.spec.md`): Checks 1.5, 1.6, 8, and 9 were skipped by tier policy rather than by project configuration, and Checks 2/4 ran as one synthesized subagent dispatch rather than two separate ones.
