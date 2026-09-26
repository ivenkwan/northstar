# infra/temporal — Temporal workflow infrastructure

Temporal hosts durable workflows for CRM mutations and external communications (PRD §13 action boundary): policy checks, human approval steps, idempotent execution, and action receipts (PRD §8.7, §19.2 action endpoints).

## Planned contents

- Temporal cluster deployment and namespace configuration.
- Workflow definitions deployment for controlled actions (Track G).
- Retry, timeout, and compensation policy for write-back actions (safe to retry without duplicate effects — PRD §28.1 Scenario E).

## Build track

Phase 1, Track G — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
