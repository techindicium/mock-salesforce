---
spec: .context-index/specs/features/mcp-server/opportunity-tools.spec.md
plan: .context-index/specs/features/mcp-server/opportunity-tools.plan.md
charter: mcp-server
validated-at: 2026-09-07T03:24:12.644Z
overall-status: PASS_WITH_NOTES
rigor-tier: quick
manifest-sha: dbfb39b
---

# Validation Report: Opportunity MCP tools

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/features/mcp-server/opportunity-tools.spec.md
> **Plan:** .context-index/specs/features/mcp-server/opportunity-tools.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Rigor Tier

Resolved via `.context-index/governance/risk-policies.yaml`: spec `risk_level: low` →
`policies.low.validate_mode: quick`. No explicit `--tier` or routing override was present.

Under `quick` tier, Check 1 still runs in full and the remaining registry checks (1.5, 1.6, 8, 9,
14) — being deterministic-check / non-subagent kinds — are unaffected by the tier's subagent
collapse. The tier's "one synthesized compliance check" substitutes only for Checks 2
(spec-compliance) and 4 (constitution-compliance), and both are already `enabled: false` in this
project's `governance/validate.yaml` (project governance posture: "only the deterministic checks
run ... subagent-review checks are disabled"). With no subagent-review checks enabled to
synthesize, the quick-tier synthesized check is a no-op here and was not dispatched.

## Check 1: Quality Gates — PASS
- Tier: fast only (no integration/e2e gates configured in `governance/gates.yaml`; the
  `integration-test` gate declares an empty command and is skipped by the loader with
  `INVALID_GATE: Gate 'integration-test' missing required command field — skipped.`)
- test (`python3 -m pytest -q`, run via project `.venv`): **PASS** — 105 passed, 3 warnings
  (pre-existing FastAPI `on_event` deprecation warnings, unrelated to this spec), 0.62s.
- lint (`ruff check .`): **PASS** — "All checks passed!"
- Gate outcomes attested: `test` (fast, pass), `lint` (fast, pass) — recorded on the
  `validate.check-1-quality-gates` validator_report with `command_sha` for each gate and
  `manifest_sha: dbfb39b`.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify --spec <spec>` → `Check 1.5: PASS — source manifest matches
  (sha: dbfb39b)`.
- Git-tracked check: all 5 manifest files have at least one commit —
  `mcp_server/app.py`, `mcp_server/tools/opportunities.py`,
  `tests/mcp_server/test_connection_handling.py`,
  `tests/mcp_server/test_input_validation.py`, `tests/mcp_server/test_opportunity_tools.py`
  (latest touching commits: `95d247f`, `d7efaba`).

## Check 1.6: Code-Side Drift Warning — PASS
- `adev verify spec --spec <spec> --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}`.
- No drift detected; spec still reflects implementation.

## Check 2: Spec Compliance — SKIPPED (disabled)
- `governance/validate.yaml` marks `validate.check-2-spec-compliance` with
  `enabled: false — subagent-review — dropped for lightweight validation`.
- Not dispatched, per project governance posture (mirrored in `CLAUDE.md` Governance Posture
  section).

## Check 4: Constitution Compliance — SKIPPED (disabled)
- `governance/validate.yaml` marks `validate.check-4-constitution` with
  `enabled: false — subagent-review — dropped for lightweight validation`.
- Not dispatched, per project governance posture.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared", ...}`.
- No rules declared in `governance/boundaries.yaml`; nothing to enforce (not a pass by default —
  a SKIP, per the check's own semantics).

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec <spec> --json` →
  `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions configured","gates":{}}`.
- `governance/gates.yaml` declares `transitions: {}` — no `implement-to-validate` transition
  configured for this project.

## Check 11: Visual Verification — N/A
- `governance/validate.yaml` marks `validate.check-11-visual-verification` with
  `enabled: false — no UI — mock-salesforce is a headless HTTP API`. No UI files in the source
  manifest either way (all 5 files are Python server/test modules).

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json` → 4 findings, all `severity: warning`, 0 errors:
  - `gate-doctor/gate-set-divergence` — `integration-test` declared in `gates.yaml` but absent
    from the domain-merged set (empty command, filtered by the loader).
  - `gate-doctor/ci-config-missing` — no CI configuration found; gates only run locally.
  - `gate-doctor/runner-unknown` — `lint` gate's runner (`ruff check .`) is not a known test
    runner, so test collection cannot be verified for it (expected — it's a linter, not a test
    suite).
  - `gate-doctor/empty-command` — `integration-test` gate declares no command (documented as
    intentionally unwired in `gates.yaml`'s own comments — "no integration-test suite yet").
- No errors; all four findings describe known, already-documented project state rather than new
  regressions introduced by this spec.

---

**Summary:** 4 checks PASS (1, 1.5, 1.6, 8/9 recorded as SKIP-not-blocking), 1 check
PASS_WITH_NOTES (14), 2 checks SKIPPED-DISABLED by project governance (2, 4), 1 check N/A (11).
0 failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding — not run here since Check 2 is
>   disabled for this project).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check
>   13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This project's `governance/validate.yaml` additionally disables Checks 2, 4, and 11 as a
> deliberate lightweight-validation posture (see `CLAUDE.md` Governance Posture) — their absence
> here is a project configuration choice, not a restructure artifact.
