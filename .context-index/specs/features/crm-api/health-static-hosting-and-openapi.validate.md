---
spec: .context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md
plan: .context-index/specs/features/crm-api/health-static-hosting-and-openapi.plan.md
validated-at: 2026-09-06
rigor-tier: quick (deterministic checks run in full per project governance; see note below)
overall-status: PASS_WITH_NOTES
---

# Validation Report: Health route, static asset hosting, and OpenAPI contract

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-api/health-static-hosting-and-openapi.spec.md
> **Plan:** .context-index/specs/features/crm-api/health-static-hosting-and-openapi.plan.md
> **Rigor Tier:** quick (resolved via `governance/risk-policies.yaml` — `risk_level: low` → `validate_mode: quick`; no explicit `--tier` or routing override supplied)
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS

Gate set resolved via `adev domain load-gates` from `.context-index/governance/gates.yaml` (2 usable gates; `integration-test` excluded — `INVALID_GATE: missing required command field`).

- **Check 1a (fast tier):**
  - `test` — `python3 -m pytest -q` — **PASS** (57 passed, 4 warnings, 0.58s)
  - `lint` — `ruff check .` — **PASS** (All checks passed!)
- **Check 1b (integration tier):** no gates configured — skipped, not failed.
- **Check 1c (e2e tier):** no gates configured — skipped.

Gate outcomes attested: `test` → pass, `lint` → pass (manifest-sha: `e500696`).

## Check 1.5: Source Manifest Verification — PASS

`adev source-manifest verify` reports `PASS — source manifest matches (sha: e500696)`. All 6 listed files verified present on disk and each confirmed committed to git via `git log --oneline -1 -- <file>`:

- `src/mock_salesforce/app.py` — commit `05103ca`
- `src/mock_salesforce/health.py` — commit `390c2d2`
- `src/mock_salesforce/static.py` — commit `05103ca`
- `tests/test_health.py` — commit `390c2d2`
- `tests/test_openapi.py` — commit `ad8dd49`
- `tests/test_static_hosting.py` — commit `05103ca`

## Check 2 / Check 4 — Spec & Constitution Compliance — SKIPPED (disabled per governance)

`.context-index/governance/validate.yaml` sets `enabled: false` on both `validate.check-2-spec-compliance` and `validate.check-4-constitution`, with the comment "subagent-review — dropped for lightweight validation." This matches the project's documented Governance Posture in the constitution/`CLAUDE.md`: *"Both subagent-review checks (spec-compliance, constitution-compliance) and visual-verification are disabled."* Per Step 0's disabled-check handling, these are recorded SKIPPED-DISABLED and do not contribute to the aggregate verdict — this applies independent of the `quick` rigor tier's own synthesized-check behavior, since the checks are absent from the registry entirely rather than merely deferred to a fused dispatch.

## Check 1.6: Code-Side Drift Warning — PASS (no drift)

`adev verify spec --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}`. No non-blocking drift warning to surface.

## Check 8: Boundary Compliance — SKIP

`adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","files_checked":68}`. No boundary rules are declared for this project — SKIP reflects that nothing was read, not that boundaries held.

## Check 9: Transition Gates — SKIP

`adev gate transitions --transition implement-to-validate --module crm-api --json` → `{"verdict":"SKIP","reason":"no transitions configured"}`. Project declares no `implement-to-validate` transition gates.

## Check 11: Visual Verification — N/A

`validate.check-11-visual-verification` is `enabled: false` in governance ("no UI — mock-salesforce is a headless HTTP API"). No UI files in this implementation's diff either (`.py` source and test files only), so both the registry disable and the trigger-guard's Case A ("No UI files... No Playwright") independently support N/A.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES (4 warnings, 0 errors)

`adev gate doctor --json` — no error-severity findings.

- `gate-doctor/gate-set-divergence` (warning) — raw `gates.yaml` declares `integration-test`, absent from the domain-merged set every consumer reads.
- `gate-doctor/ci-config-missing` (warning) — no CI configuration found in this repo.
- `gate-doctor/runner-unknown` (warning) — `lint` gate (`ruff check .`) has no known test-runner signature; collection not verifiable for it (expected — it's a linter, not a test runner).
- `gate-doctor/empty-command` (warning) — `integration-test` declares no command (pre-existing, unwired sentinel).

None of these affect Check 1's outcome; all are pre-existing, already-acknowledged project posture (course-fixture repo, no CI, integration tier deliberately unwired).

**Note on rigor-tier deviation:** The `quick` tier's default behavior skips Checks 1.5, 1.6, 8, and 9 as an optimization. This project's governance posture (`CLAUDE.md` Governance Posture section) explicitly names these same checks — quality gates, source-manifest, boundaries, transition-gates, gate-executability — as the deterministic set that *does* run regardless of tier, reserving only the AI-judgment subagent-review checks (spec-compliance, constitution-compliance, visual-verification) for disablement. All five deterministic checks were therefore run in full above rather than skipped, consistent with that explicit project intent; none surfaced a blocking finding.

---

**Summary:** 4 checks ran and passed or passed-with-notes (Check 1, Check 1.5, Check 1.6, Check 14). 2 checks returned SKIP as a factual outcome, not a gap (Check 8: no boundary rules declared; Check 9: no transitions configured). 3 checks are disabled per project governance and did not run (Check 2, Check 4, Check 11). 0 failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally reflects the project's `governance/validate.yaml` posture, which disables both subagent-review checks (spec-compliance, constitution-compliance) and visual-verification for lightweight validation on this course-fixture repo. Check 2's scope-expansion sub-finding was therefore not evaluated this run — spec/constitution/charter-scope compliance for this feature has not been independently reviewed by an AI judge, only by the deterministic gates above.
