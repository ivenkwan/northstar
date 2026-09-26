# apps/mobile — Sales Northstar mobile application

React Native 0.87+ mobile app with the Strict TypeScript API enabled (PRD §12, §17). Five primary navigation destinations: Today, Ask, Dashboard, Pipeline, Intelligence (PRD §10.1).

## Standards (PRD §17)

- TypeScript 5.x only; no JavaScript source except reviewed build configuration.
- Extends the approved base `tsconfig` with the full strict compiler policy (PRD §17.2).
- TanStack Query with typed query keys; API functions generated from OpenAPI 3.1 via `packages/contracts`.
- Zod validation at every untrusted boundary via `packages/validation`.
- React Navigation with statically typed root and nested parameter lists (PRD §17.7).
- Prohibited patterns per PRD §17.3 fail CI unless a time-bounded waiver is recorded.

## Planned contents

- `src/navigation/` — typed root stack and nested navigators.
- `src/features/` — today, ask, dashboard, pipeline, intelligence feature areas.
- `src/widgets/` — dashboard widget renderers (discriminated union per PRD §17.5).
- `src/transport/` — the only location permitted to touch generated API functions.

## Build track

Phase 1, Track B (Mobile type safety) — see `todo.md`.
