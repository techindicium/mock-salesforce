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
  sha: "e500696"
  files:
    - src/mock_salesforce/app.py
    - src/mock_salesforce/health.py
    - src/mock_salesforce/static.py
    - tests/test_health.py
    - tests/test_openapi.py
    - tests/test_static_hosting.py
  computed-at: "2026-09-06T21:19:35.872Z"
drift_detected: true
---

# Live Spec: Health route, static asset hosting, and OpenAPI contract

<!-- Live Spec within the crm-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/crm-api/charter.md -->

## Behavioral Contract

### Preconditions

- The API process is running and its SQLite database is available.
- No authentication is required to reach any endpoint (per charter: no real auth in scope).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `GET /health` request is sent, **then** the API responds `200` with a
  minimal JSON body (e.g. `{"status": "ok"}`) — no database round trip is required for this
  route to succeed, so it stays meaningful even if the database were briefly unavailable.
- **BEH-2** — **When** `crm-ui`'s built static assets are present on disk at the location this
  process is configured to serve from, **then** a `GET /` request responds `200` with the UI's
  `index.html`, and any other static asset path (JS/CSS) under that build output is served with
  its correct content type.
- **BEH-3** — **When** `crm-ui`'s built static assets are absent (e.g. a local dev run with no
  UI build step), **then** `GET /` responds `404` rather than raising a server error — the API
  is fully usable on its own with no UI present.
- **BEH-4** — **When** a `GET /openapi.json` request is sent, **then** the API responds `200`
  with a valid OpenAPI document describing every route mounted at that time (Account, Contact,
  Opportunity CRUD, plus `/health`) — the document is auto-generated from the implementation,
  never hand-maintained.

### Postconditions

- `GET /openapi.json` always reflects the currently mounted routes; it is regenerated per
  request, never cached stale across a code change.
- `GET /health` never depends on `crm-ui`'s static assets being present — the two capabilities
  fail independently of each other.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Static asset requested but `crm-ui`'s build output is absent | `404 Not Found` | `STATIC_ASSET_NOT_FOUND` |
| Malformed JSON request body (any route in this spec that accepts one) | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because `GET /openapi.json` is
  what makes the whole documented contract discoverable to consuming tracks.
- **Principle:** "Fixture-backed, offline only." — Applies because static asset hosting and the
  health route both stay entirely local; neither reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Implement `GET /health` | Minimal handler, no DB dependency | small |
| Wire static asset hosting | Serve `crm-ui`'s build output at `/` when present; 404 cleanly when absent | small |
| Confirm OpenAPI wiring | Verify the framework's auto-generated OpenAPI document reflects all mounted routes with proper request/response models (no manual OpenAPI authoring) | small |

## Acceptance Criteria

- [x] `GET /health` returns 200 with no DB dependency (BEH-1)
- [x] `GET /` serves crm-ui's `index.html` and static assets when the build output is present (BEH-2)
- [x] `GET /` returns 404 (not a server error) when the build output is absent (BEH-3)
- [x] `GET /openapi.json` returns a valid OpenAPI document listing every mounted route (BEH-4)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
