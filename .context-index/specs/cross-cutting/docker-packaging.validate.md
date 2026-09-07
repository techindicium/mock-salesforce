---
spec: .context-index/specs/cross-cutting/docker-packaging.spec.md
plan: .context-index/specs/cross-cutting/docker-packaging.plan.md
validated-at: 2026-09-07T05:41:00.976Z
overall-verdict: PASS_WITH_NOTES
---

# Validation Report: Docker packaging and run instructions

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/cross-cutting/docker-packaging.spec.md
> **Plan:** .context-index/specs/cross-cutting/docker-packaging.plan.md
> **Overall Status:** PASS (with notes)

---

## Rigor Tier

Spec `risk_level: low` → `governance/risk-policies.yaml` resolves `validate_mode: quick`
(no explicit `--tier`, no routing signal supplied to this invocation). Under `quick` tier,
Check 1 (Quality Gates) still runs in full, and the remaining checks are normally replaced by
one synthesized spec+constitution compliance check. This project's `governance/validate.yaml`
already sets `enabled: false` on both `validate.check-2-spec-compliance` and
`validate.check-4-constitution` ("dropped for lightweight validation" — matching this project's
documented Governance Posture in `CLAUDE.md`, which states both subagent-review checks are
disabled outright). Since the quick-tier synthesized check exists solely to stand in for those
two disabled checks, it was likewise skipped rather than dispatched — dispatching a subagent
here would contradict the project's explicit, documented intent to run zero subagent-review
checks. Checks 1.5, 1.6, 8, 9, and 14 (all deterministic, non-subagent) ran in full, matching
`CLAUDE.md`'s stated posture: "only the deterministic checks run (quality gates, source-manifest,
boundaries, transition-gates, gate-executability)."

## Check 1: Quality Gates — PASS

Gate set resolved via `adev domain load-gates --module deployment` from the project's
materialized `governance/gates.yaml` (domain: software, source: project).

- Check 1a (fast tier):
  - `test` (`python3 -m pytest -q`): PASS — 111 passed, 3 warnings (pre-existing FastAPI
    `on_event` deprecation warnings, not related to this spec), 0.69s.
  - `lint` (`ruff check .`): PASS — all checks passed.
- Check 1b (integration tier):
  - `integration-test` (`python3 -m pytest -q tests/docker`): PASS — 9 passed, 1 warning,
    61.55s. Run with `PORT=8100`/`MCP_PORT=8101` to avoid colliding with the already-running
    mock-jira stack on 8000/8001 (tests read these as overridable env vars with 8000/8001
    defaults). `docker ps`/`docker compose ps` confirmed no leftover containers after the run.
- Check 1c (e2e tier): no gates configured, skipped.

Per-gate outcome attestation emitted via `adev report --type validator
--validator validate.check-1-quality-gates --gate-outcomes ...` carrying `{id, verdict, tier,
command_sha}` for all three gates, `--manifest-sha c8730d1`.

## Check 1.5: Source Manifest Verification — PASS

`adev source-manifest verify --spec <spec>` → `Check 1.5: PASS — source manifest matches
(sha: c8730d1)`. All 20 files listed in the spec's `source-manifest` frontmatter block were
individually confirmed committed to git (`git log --oneline -1 -- <file>` returned a commit for
every file; none untracked or staged-only).

## Check 1.6: Code-Side Drift Warning — PASS

`adev verify spec --spec <spec> --check-drift` → `{"drifted":false,"drift_source":null,
"drift_at":null}`. No drift detected; non-blocking check.

## Checks 2 & 4: Spec Compliance / Constitution Compliance — SKIPPED (disabled)

Both disabled in `governance/validate.yaml` (`enabled: false`, "subagent-review — dropped for
lightweight validation"), consistent with `CLAUDE.md`'s Governance Posture. See Rigor Tier note
above for why the quick-tier synthesized compliance check was also not substituted.

## Check 8: Boundary Compliance — SKIP

`adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared",
"findings":[],"disabled":[],"warnings":[],"summary":{"errors":0,"warnings":0,"infos":0,
"files_checked":1}}`. No boundary rules declared for this project — SKIP, not an implicit pass.

## Check 9: Transition Gates — SKIP

`adev gate transitions --transition implement-to-validate --spec <spec> --module deployment
--json` → `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions
configured","gates":{}}`. `governance/gates.yaml` declares `transitions: {}` — no transition
gates configured for this project.

## Check 11: Visual Verification — N/A

Disabled in `governance/validate.yaml` ("no UI — mock-salesforce is a headless HTTP API").
Independently confirmed: this spec's source-manifest contains no UI file patterns (Dockerfiles,
compose YAML, Python, docs, tests only) — Trigger Guard Case A/D (no UI files) would SKIP even
if the check were enabled.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES

`adev gate doctor --json` → 0 errors, 2 warnings:
- `gate-doctor/ci-config-missing` (warning): No CI configuration found. Gates only ever run on a
  developer's machine.
- `gate-doctor/runner-unknown` (warning): Gate `lint`'s command (`ruff check .`) has no
  identifiable test runner, so collection cannot be verified for it (expected — `ruff` is a
  linter, not a test collector; only `test` and `integration-test` map to `pytest`, both
  correctly identified).

Both findings are `severity: warning` per this check's registry declaration — non-blocking, but
recorded per the skill's evidence-citation contract.

---

**Summary:** 4 passed (Check 1, 1.5, 1.6), 2 skipped for no-configuration reasons (Check 8, 9),
2 skipped-disabled by project governance (Check 2, 4), 1 N/A/disabled (Check 11), 1 passed with
notes (Check 14). 0 failed checks.

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
>
> Historic `.validate.md` reports continue to use the pre-restructure numbering; the gaps in the
> surviving inventory (Checks 1, 1.5, 1.6, 8, 9, 14) are intentional to preserve report
> readability.
