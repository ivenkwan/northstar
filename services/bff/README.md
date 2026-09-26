# services/bff — Mobile BFF (FastAPI)

Backend-for-frontend that the mobile app calls for all sales functions (PRD §13, trust boundary §13.1). The app never calls provider LLM routes directly; the BFF fronts conversational, pipeline, dashboard, alert, and action endpoints.

## Planned responsibilities

- Publish the product API (PRD §19.2) as OpenAPI 3.1 — the source for `packages/contracts`.
- Stream typed conversation components to mobile (PRD §19.3 schema).
- Validate graph responses, filter attributes by user authorization, and send only bounded subgraphs (PRD §18).
- Enforce scope/classification claims end-to-end; cursor pagination and `as_of` timestamps (PRD §19.1).
- Emit OpenTelemetry telemetry (PRD §21).

## Stack

Python / FastAPI. Idempotency keys for writes; typed error envelope before streaming starts (PRD §17.8).

## Build track

Phase 1, Tracks B/D — see `todo.md`.
