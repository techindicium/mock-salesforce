---
tier: quick
---

# Validation Report: Port mock-jira's visual design system to crm-ui

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/features/crm-ui/visual-design-system.spec.md
> **Plan:** .context-index/specs/features/crm-ui/visual-design-system.plan.md
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS
- Tests: PASS — `python3 -m pytest -q` → 117 passed
- Frontend tests: PASS — `node --test static/js/*.test.mjs` → 46 passed
- Lint: PASS — `ruff check .` → All checks passed!
- Integration tests (`tests/docker`): PASS — 9/9 passed, run with `PORT=8200 MCP_PORT=8201` overrides. Note: the gate's `command` argv (`python3 -m pytest -q tests/docker`) contains no port literals — the `command_sha` attests the argv, not the environment. With the default ports (8000/8001), 4 of 9 tests fail with `port is already allocated`, because the sibling `mock-jira` repo's own containers (`mock-jira-issue-tracker-api-1`, `mock-jira-mcp-server-1`) are persistently bound to `127.0.0.1:8000`/`8001` on this shared dev machine — confirmed via `docker ps`. This branch touches zero files under `docker/` or `docker-compose.yml`; the collision is a pre-existing environmental condition of running two adev-course mock repos side by side, not a regression introduced by this spec.

## Check 1.5: Source Manifest Verification — SKIP
- Skipped — quick rigor tier.

## Check 1.6: Code-Side Drift Warning — SKIP
- Skipped — quick rigor tier.

## Check 2: Spec Compliance — PASS
(run as part of the quick-tier synthesized compliance check, combined with Check 4)
- AC1 Shared `:root` tokens, no hardcoded literals (BEH-1): PASS — `static/css/board.css:1-15`; forbidden legacy literals (`#f4f5f7`, `#ddd`, `#fdecea`, `#611a15`) absent, verified by `tests/test_css_component_coverage.py:44-45`.
- AC2 `[hidden]` guard survives specificity (BEH-2): PASS — `board.css:17-19`, verified by `tests/test_css_design_tokens.py:21-34`.
- AC3 Buttons/inputs/selects/`.form-error` styled consistently (BEH-3): PASS — `board.css:41-51`, `97-123`, verified by rule-isolated assertions in `tests/test_css_component_coverage.py:6-29` (tightened from an initially-weak OR assertion in commit `056d787`).
- AC4 Columns/cards restyled, order/content unchanged (BEH-4): PASS — `board.css:65-95`; `git diff 46f2e9e..HEAD -- static/index.html` is empty.
- AC5 All tests pass unmodified (BEH-5): PASS — 117 pytest (111 pre-existing + 6 new in wholly-new test files, nothing pre-existing modified), 46 node.
- AC6 No id/name/class renamed or removed: PASS — `git diff 46f2e9e..HEAD -- static/index.html static/deal.html static/accounts.html` produces zero output.
- AC7 Quality gates pass: PASS — see Check 1.
- AC8 No constitutional violations: PASS — see Check 4.

## Check 4: Constitution Compliance — PASS
- Architecture boundaries: PASS — diff scope is `static/css/board.css` + 2 test files + spec/plan/review artifacts only; no backend/API code touched.
- Non-negotiable principles: PASS — "No inbound dependencies": `grep -rni "mock-jira" static/ src/ tests/` returns no matches; the ported CSS was a one-time authoring reference, not a runtime/build dependency.
- Coding standards: PASS, with one non-blocking note — CSS token names (`--stamp-red`, `--stamp-gold`, `--stamp-green`) are ported verbatim from mock-jira's vintage-stamp theme rather than mirroring Salesforce's own vocabulary (constitution's "descriptive naming" preference). Accepted as a deliberate, low-stakes token-port choice during code-quality review (Task 1, finding cq-1/minor); not a violation.

## Check 8: Boundary Compliance — SKIP
- Skipped — quick rigor tier. (Project declares `boundaries: []` in `governance/boundaries.yaml` — would SKIP under full tier too, for a different reason: no rules declared.)

## Check 9: Transition Gates — SKIP
- Skipped — quick rigor tier.

## Check 11: Visual Verification — SKIP (disabled)
- `governance/validate.yaml` has `validate.check-11-visual-verification` set `enabled: false` (registry-level disable, stale comment "no UI — mock-salesforce is a headless HTTP API" predates crm-ui's later build). Disabled at the registry, so this run does not attempt browser-based verification regardless of tier. Manual/headless verification of this exact change was already performed live during implementation (real Chrome `--headless=new --dump-dom` checks on all three pages, documented in this session) and separately by direct `curl`/Python HTTP checks of served CSS content in every task's review cycle.

---

**Summary:** 3 passed (Check 1, 2, 4 — synthesized), 6 skipped (1.5, 1.6, 8, 9 per quick tier; 11 disabled at registry level). 0 failed.

**Rigor tier:** quick (this repo's `risk-policies.yaml` sets `validate_mode: quick` at every risk tier, per its deliberately fully-agentic governance posture).

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 12, and 13 have been relocated by `check-set-restructure.spec.md`. See `/adev:review-specs`, `/adev:hygiene` Audit Pass 20, `/adev:reconcile`, and the post-validate heuristics hook.

---

## Addendum (2026-09-07, post-validation): real visual defect found and fixed

The claim above under Check 11 — that headless DOM-structure checks and served-CSS-content checks during implementation substituted adequately for visual verification — was **incomplete**. Those checks confirm a selector exists and references a token; they cannot detect a *rendered contrast* defect, which is exactly the class of bug Check 11 exists to catch.

Taking actual browser screenshots of the running app (`google-chrome --headless=new --screenshot`) after this report's PASS surfaced a real, user-visible bug: `#accounts-list li` and `.account-contacts-list li` set a light `paper-dim`/`paper` background but never set their own `color`, so they inherited `body`'s light `--paper-text-on-rail` (intended for text directly on the dark page background) — producing near-invisible, low-contrast account names on the Accounts page. The identical rule worked correctly on `deal.html` only by accident, because `#contacts-list li` there sits inside `#contacts-section`, which *does* set an explicit paper-text color, and CSS inheritance papered over the missing declaration.

**Fixed in commit `8ec5942`:** explicit `color: var(--ink-text-on-paper)` added to `#contacts-list li, #accounts-list li`, `.account-contacts-list li`, and `details` (defensive, for future content). Added `tests/test_css_component_coverage.py::test_list_row_rule_sets_explicit_text_color`, which isolates the rule and asserts it declares `color:` explicitly rather than relying on ancestor inheritance — this is the kind of check that generalizes; it would have caught this class of bug pre-merge. Re-verified: 118/118 pytest, 46/46 node, ruff clean. Source manifest re-stamped to `sha: 009ccc7`.

**Standing gap, not fixed here:** `governance/validate.yaml`'s `validate.check-11-visual-verification` is still `enabled: false` with a stale comment ("no UI — mock-salesforce is a headless HTTP API") that predates crm-ui's build. This gap is exactly why this defect reached a "validated" spec undetected by the automated pipeline. Recommend a follow-up: re-enable Check 11 now that crm-ui exists, once a Playwright MCP server is available in this environment (it was not available during this session — connection closed).
