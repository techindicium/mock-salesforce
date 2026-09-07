---
spec: .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.spec.md
plan: .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.plan.md
charter: crm-ui
date: 2026-09-06
rigor_tier: quick
overall_status: PASS_WITH_NOTES
---

# Validation Report: Deal detail page and CRUD forms

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.spec.md
> **Plan:** .context-index/specs/features/crm-ui/deal-detail-and-crud-forms.plan.md
> **Rigor Tier:** quick (resolved from `risk_level: medium` → `governance/risk-policies.yaml` → `validate_mode: quick`)
> **Overall Status:** PASS_WITH_NOTES

---

## Check Registry Resolution

This project's `governance/validate.yaml` runs a deliberately lightweight, deterministic-only
check set (per `CLAUDE.md` § Governance Posture): both subagent-review checks
(`validate.check-2-spec-compliance`, `validate.check-4-constitution`) and
`validate.check-11-visual-verification` are disabled at the registry level (`enabled: false`),
regardless of rigor tier. The quick-tier "single synthesized compliance check" substitute
therefore has nothing to substitute for in this project and was not dispatched — the registry's
`enabled: false` is the authoritative, project-level decision to skip subagent judgment checks
entirely, not merely a tier-driven trim.

Surviving checks for this run: 1 (quality gates), 1.5 (source-manifest), 1.6 (code-drift,
observational), 8 (boundaries), 9 (transition-gates), 14 (gate-executability).

## Check 1: Quality Gates — PASS
- Fast tier:
  - Test (`python3 -m pytest -q`, via project `.venv`): PASS — 71 passed, 4 warnings (deprecation
    warnings only, unrelated to this spec).
  - Lint (`ruff check .`): PASS — "All checks passed!"
- Integration tier: no gates configured (`integration-test` gate in `governance/gates.yaml`
  declares an empty `command` and was skipped by the loader with `INVALID_GATE`).
- E2E tier: no gates configured.
- Gate outcomes recorded: `test` → pass, `lint` → pass (manifest-sha `6a4c2f4`).

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify` → "PASS — source manifest matches (sha: 6a4c2f4)".
- All 15 manifest files verified as git-tracked (`git log --oneline -1 -- <file>` returned a
  commit for each): `static/accounts.html`, `static/deal.html`, `static/index.html`,
  `static/js/accounts.js`, `static/js/api.js`, `static/js/api.test.mjs`, `static/js/board.js`,
  `static/js/deal.js`, `static/js/form-errors.js`, `static/js/form-errors.test.mjs`,
  `static/js/list-state.js`, `static/js/list-state.test.mjs`, `tests/test_ui_accounts_page.py`,
  `tests/test_ui_board_page.py`, `tests/test_ui_deal_page.py`.

## Check 1.6: Code-Side Drift — PASS (non-blocking, observational)
- `adev verify spec --check-drift` → `{"drifted":false}`. No `drift_detected` flag, no
  unresolved `code_drift_detected` event.

## Check 2 / Check 4: Spec Compliance / Constitution Compliance — SKIPPED (disabled)
- Disabled by project governance (`governance/validate.yaml`, `enabled: false`) per this
  project's lightweight, deterministic-only validation posture. Not run under any rigor tier.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","findings":[],"disabled":[],"warnings":[]}`.
- No boundary rules declared in this project — SKIP reflects "nothing to check," not "boundaries held."

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --json` → `{"verdict":"SKIP","reason":"no transitions configured"}`.
- `governance/gates.yaml` declares `transitions: {}`.

## Check 11: Visual Verification — SKIPPED (disabled)
- Disabled at the registry level with the stated rationale "no UI — mock-salesforce is a
  headless HTTP API." **Advisory:** this rationale is stale — the spec's own source-manifest
  lists `static/*.html` and `static/js/*.js` UI files, so the repo does now have a UI surface.
  This is a registry/constitution drift worth reconciling (e.g. via `/adev:hygiene` or
  `/adev:reconcile`), but is not a validation blocker since the check is explicitly and
  deliberately disabled by project governance.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json` → 4 warning-severity findings, 0 errors:
  - `gate-set-divergence`: `integration-test` declared in `governance/gates.yaml` but absent
    from the domain-merged gate set actually consumed.
  - `ci-config-missing`: no CI configuration found.
  - `runner-unknown` (gate `lint`): no known test runner identified for `ruff check .` — test
    collection cannot be verified for this gate.
  - `empty-command` (gate `integration-test`): declares no command.
- All findings are warning-severity and advisory; none block this run.

---

**Summary:** 5 checks passed (1, 1.5, 1.6 observational, 8-SKIP, 9-SKIP counted as non-blocking),
1 check passed with notes (14), 2 checks skipped as disabled by project governance (2/4 combined,
11). 0 failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 12, and 13 have been
> relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly
>   Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
