# packages/contracts — Generated API contracts

The single source of truth for TypeScript API types and transport functions, generated from the backend OpenAPI 3.1 documents (PRD §17.4). Hand-authored copies of backend DTOs are prohibited (PRD §17.3).

## Contract pipeline (PRD §17.4)

1. FastAPI services export OpenAPI 3.1 from the backend build.
2. Spectral lint for operation IDs, discriminators, error envelopes, backward compatibility.
3. `tools/codegen` generates TypeScript types and transport functions into this package.
4. CI fails if generated output differs from committed artifacts.
5. Consumer-driven contract tests run against the API candidate.

## Rules

- OpenAI and Anthropic wire contracts stay **separate** — never merge them into one broad optional-field interface (PRD §17.6, ADR-022).
- The typed error envelope (`ApiError`, PRD §17.8) is defined here.
- Breaking contract changes block release (PRD §17.4 step 7).

## Build track

Phase 1, Track B Sprint 2 — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
