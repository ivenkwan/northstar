# services/byok — BYOK credential service

Owns provider credential onboarding and lifecycle metadata behind the administrative API (PRD §16). Never returns plaintext keys after submission; keys live only in HashiCorp Vault.

## Lifecycle (PRD §16.3)

Register → verify (minimal non-content request) → store in Vault (wipe plaintext buffers) → bind to protocols/models/domains/environments → activate APISIX route config → monitor → rotate (canary → promote → revoke) → suspend/revoke.

## API surface (PRD §16.5)

`POST/GET /api/v2/admin/byok/credentials`, rotate, test, bindings, delete — all writes require idempotency key, immutable audit event, and policy decision. Responses contain only credential ID, fingerprint, and status.

## Fail-closed requirements (PRD §16.4)

Pre-deployment secret-existence validation, synthetic probes after route/secret revision, alerting on secret-resolution failures, credential circuit breaker, no platform-key fallback without explicit opt-in, sanitized `AI_CREDENTIAL_UNAVAILABLE` user error. See ADR-023.

## Build track

Phase 1, Track A Sprint 4 — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
