# apps/admin — Web administration portal

Responsive web application for platform administrators, sales operations, and tenant AI administrators (PRD §4.1, §5). Authenticates through APISIX with OIDC + MFA.

## Planned responsibilities

- BYOK credential onboarding, rotation, binding, and revocation UI (PRD §16.5).
- Metric catalog and certification management (PRD §14.2).
- Connector configuration and data-quality scorecards (PRD §27 "Operations" and "Sales data foundation").
- Policy, audit search, and evaluation dashboards (PRD §11.4, §23).

## Notes

- Framework choice is an open item for Phase 0; it must consume the same generated OpenAPI contracts as mobile (`packages/contracts`).
- Admin screens are in scope from Phase 1 Sprint 4 (BYOK admin APIs) — see `todo.md` Track A.

## Build track

Phase 1, Track A (gateway/BYOK dependencies) and Phase 2 expansions — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
