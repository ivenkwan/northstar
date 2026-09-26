# packages/validation — Zod runtime boundary schemas

TypeScript-first runtime schemas (Zod) validating every untrusted dynamic payload before it reaches UI or domain code (PRD §17.1, ADR-026).

## Required coverage (PRD §17.4 step 5, §23.4)

- Agent conversation components and events (discriminated unions).
- Dashboard definitions produced by the Dashboard Composer.
- Knowledge-graph node/edge payloads (bounded subgraphs).
- Deep-link parameters before navigation (PRD §17.7).
- Forward-compatible and malformed payload test cases for every schema.

## Rules

- Schemas are authored once here and consumed by `apps/mobile`, `apps/admin`, and `apps/mobile`'s transport layer — never duplicated per app.
- Approved exception pattern for unknown data: accept `unknown`, validate with a schema, narrow to a domain type (PRD §17.3).

## Build track

Phase 1, Track B Sprint 2 (introduced with the generated API client) — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
