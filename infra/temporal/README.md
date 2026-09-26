# infra/temporal — Temporal workflow infrastructure

Temporal hosts durable workflows for CRM mutations and external communications (PRD §13 action boundary): policy checks, human approval steps, idempotent execution, and action receipts (PRD §8.7, §19.2 action endpoints).

## Planned contents

- Temporal cluster deployment and namespace configuration.
- Workflow definitions deployment for controlled actions (Track G).
- Retry, timeout, and compensation policy for write-back actions (safe to retry without duplicate effects — PRD §28.1 Scenario E).

## Build track

Phase 1, Track G — see `todo.md`.
