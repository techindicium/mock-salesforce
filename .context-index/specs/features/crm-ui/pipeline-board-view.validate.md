---
spec: .context-index/specs/features/crm-ui/pipeline-board-view.spec.md
plan: .context-index/specs/features/crm-ui/pipeline-board-view.plan.md
date: 2026-09-06
overall_status: PASS_WITH_NOTES
rigor_tier: quick
---

# Validation Report: Pipeline board view, account switcher

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/crm-ui/pipeline-board-view.spec.md
> **Plan:** .context-index/specs/features/crm-ui/pipeline-board-view.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

**Rigor tier:** `quick` (resolved from `governance/risk-policies.yaml` — spec `risk_level: medium` → `validate_mode: quick`; no explicit `--tier` or routing override present). Under `quick`, this project's own `governance/validate.yaml` disables both subagent-review checks (`validate.check-2-spec-compliance`, `validate.check-4-constitution`) and visual verification (`validate.check-11-visual-verification`) outright — per this repo's documented governance posture ("only the deterministic checks run"), so no synthesized spec+constitution compliance check was dispatched. The deterministic check set (1, 1.5, 8, 9, 14) ran in full regardless of tier, per that same posture.

**Workspace advisory:** `adev-workspace.yaml` is present one level up, but the spec's `depends-on` entries are same-repo paths (crm-api specs), not `@repo-slug/spec-slug` cross-repo references. Advisory: running repo-scoped inside workspace — cross-repo validation skipped (no cross-repo depends-on references).

---

## Check 1: Quality Gates — PASS

- Check 1a (fast tier):
  - `test` (`python3 -m pytest -q`): PASS — 61 passed, 0 failed (0.57s)
  - `lint` (`ruff check .`): PASS — All checks passed!
- Check 1b (integration tier): SKIP — gate `integration-test` declares no command (unwired sentinel); no other integration-tier gates configured.
- Check 1c (e2e tier): SKIP — no e2e-tier gates configured.
- Informational (not a registered gate): `node --test static/js/*.test.mjs` — 27 passed, 0 failed. The project's `gates.yaml` has no Node/npm gate wired in; this was run for corroboration only, not as part of the gate verdict.

Gate outcomes recorded: `test` → pass (fast, sha `22c558be4a77b6dd61531053c7225bd05830d00bfaf46f14f430e2f0a6a0cb2b`), `lint` → pass (fast, sha `91ede4a4ad8774e8660350d4580b9e41c235ea911f560571d82f5d4f81aba16d`).

## Check 1.5: Source Manifest Verification — PASS_WITH_NOTES (drift, non-blocking)

- `adev source-manifest verify`: WARN — manifest sha `7d18227` (computed-at `2026-09-06T22:37:16.363Z`) no longer matches current content; actual sha `e5d8c3e`.
- Root cause identified: commit `b567f3b` ("wire pipeline board rendering... Plan-task: 7, Review-round: spec-compliance=2, code-quality=1") landed **after** the manifest was stamped (and after the epic-close commit `0613786`). It removed explanatory comments from `static/js/board.js` (9 lines) and `static/js/error-state.test.mjs` (4 lines) as part of a review-round cleanup pass. No functional/behavioral change — verified via `git show b567f3b`.
- Implementation-existence check: every file in the source manifest is git-tracked with commit history (verified via `git log --oneline` per file: `static/css/board.css`, `static/index.html`, `static/js/api.js`, `static/js/board.js`, `tests/test_ui_board_page.py`, etc.). No untracked/uncommitted manifest files.
- Non-blocking per Check 1.5 semantics (drift, not missing files). Recommend re-stamping the manifest on the next implement/revise pass to close the gap.

## Check 1.6: Code-Side Drift Warning — PASS_WITH_NOTES (non-blocking)

- `adev verify spec --check-drift`: `drift_detected: true`, source `tests/test_ui_board_page.py`, at `2026-09-06T22:40:24.017Z`. Consistent with the same post-stamp cleanup commit (`b567f3b`, committed `2026-09-06T22:41:21-03:00` = `22:41:21Z`) identified in Check 1.5.

## Check 2: Spec Compliance — SKIPPED-DISABLED

`validate.check-2-spec-compliance` is `enabled: false` in this project's `governance/validate.yaml` (subagent-review checks are dropped for this repo's lightweight validation posture). Not run; not run as a quick-tier synthesized check either, since the constituent check is disabled at the registry level. Acceptance-criteria checkboxes in the spec (BEH-1 through BEH-6, quality gates, no constitutional violations) are implementer-marked, not independently re-verified by a subagent in this run — see `/adev:review-specs` for anything requiring that judgment.

## Check 4: Constitution Compliance — SKIPPED-DISABLED

`validate.check-4-constitution` is `enabled: false` in this project's `governance/validate.yaml`, for the same reason as Check 2. Not dispatched.

## Check 8: Boundary Compliance — SKIP

- `adev boundaries check --json` → `verdict: "SKIP"`, `reason: "no boundary rules declared"`, `files_checked: 2`, 0 findings, 0 disabled rules, 0 registry warnings.
- SKIP means no rules were declared for this project — not that boundaries held.

## Check 9: Transition Gates — SKIP

- `adev gate transitions --transition implement-to-validate --spec <spec> --module crm-ui --json` → `verdict: "SKIP"`, `reason: "no transitions configured"` (`governance/gates.yaml` declares `transitions: {}`).

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES

- `adev gate doctor --json` → 0 errors, 4 warnings:
  - `gate-set-divergence`: `integration-test` is declared in `gates.yaml` but absent from the merged set every consumer reads (empty command).
  - `ci-config-missing`: no CI configuration found — gates only run on a developer's machine.
  - `runner-unknown` for `lint`: no known test-runner identified for `ruff check .`, so collection cannot be verified (informational, not an error).
  - `empty-command` for `integration-test`: declares no command.
- All findings are warning-severity per this check's registry declaration; 0 errors.

## Check 11: Visual Verification — SKIPPED-DISABLED

`validate.check-11-visual-verification` is `enabled: false` in `governance/validate.yaml` with the note "no UI — mock-salesforce is a headless HTTP API." This particular spec does add UI files (`static/*.html`, `static/*.css`, `static/js/*.js`), so the disable note is stale relative to this specific feature, but the registry disable is project-wide and authoritative per the single-source model — respected as-is. Also worth noting: the Playwright MCP server failed to connect this session (`CONNECTION_CLOSED`), so even an ad hoc visual check was not available as a fallback.

---

**Summary:** 5 checks ran (1, 1.5, 1.6, 8, 9, 14 — six technically, all deterministic/observational), 0 failed, 3 recorded PASS_WITH_NOTES (1.5 drift, 1.6 drift, 14 gate-doctor warnings), 2 recorded SKIP with a declared reason (8, 9), 3 SKIPPED-DISABLED per project registry (2, 4, 11).

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This project's registry also disables Checks 2, 4, and 11 outright (see `governance/validate.yaml`) as a deliberate lightweight-validation posture — those are not "relocated," they are opted out of for this repo.
