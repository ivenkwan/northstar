# infra/observability — Telemetry and monitoring

OpenTelemetry collector, Prometheus metrics, and dashboards (PRD §13, §21). Payload/prompt logging is disabled by default; prompts can contain customer, pipeline, or market-intelligence data.

## Captured signals (PRD §21)

Correlation/trace IDs, tenant, calling workload; public route protocol (`openai-chat` / `anthropic-messages`); provider, credential fingerprint, model profile, conversion flag; request count, input/output tokens, latency, time to first token, stream duration; retry/fallback counts and upstream status class; credential validation/rotation/auth failures; budget consumption and rejected requests; mobile app/contract versions and typed error codes.

## Planned contents

- OTel collector pipelines for gateway, BFF, orchestrator, and services.
- SLO dashboards and alerting aligned to NFRs (PRD §22).
- Cost telemetry: token/tool cost per tenant and per successful task (PRD §25.3).

## Build track

Phase 1, Track A Sprint 3 and Track H — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
