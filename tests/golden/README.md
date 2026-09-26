# tests/golden — Golden test suites

Versioned, release-gating test cases that encode the platform's core invariants.

## Permission goldens (PRD §23.2)

- Seller sees own records only; manager sees team roll-up; domain leader sees all domain teams; group leader sees linked domains under configured full-view/allocation rules.
- Domain in two groups never double counts in enterprise totals.
- Effective-dated transfer produces correct historical and current reporting.
- Deleted or access-revoked content disappears from retrieval and generated answers.
- News with malicious instructions cannot alter agent behavior; CRM write-back requires confirmation and is idempotent.

## Gateway conformance goldens (PRD §23.3)

- OpenAI/Anthropic non-streaming contracts and streaming SSE event order through terminators.
- Tool calls/results both protocols; header stripping; server-side credential precedence.
- Vault secret failure behavior; tenant credential isolation; rate/token/body limits; retry/fallback bounds; conversion feature matrix; client-disconnect cleanup.

## Build track

Phase 1, Tracks A/B (contract goldens) and Track H (permission goldens) — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
