# tools/codegen — API contract generation pipeline

Tooling for the OpenAPI → TypeScript contract pipeline (PRD §17.4): export OpenAPI 3.1 from FastAPI builds, Spectral lint (operation IDs, discriminators, error envelopes, backward compatibility), generate TypeScript types and transport functions into `packages/contracts`, and verify committed artifacts are current.

## CI sequence owned here (PRD §17.4)

1. Generate OpenAPI from the backend build.
2. Lint.
3. Generate TypeScript types and transport functions.
4. Fail if generated output differs from committed artifacts.
5. Support runtime validation test harnesses (`packages/validation`).
6. Run consumer-driven contract tests against the API candidate.
7. Block release on unapproved breaking contract changes.

## Build track

Phase 1, Track B Sprint 2 — see `todo.md`.
