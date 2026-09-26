# docs/runbooks — Operational runbooks

Required operational procedures (PRD §29). Each runbook is a Phase 1 Sprint 6 deliverable ("runbooks" exit condition) and is exercised before production readiness review.

## Required runbooks (PRD §29)

1. Provider credential expiration, compromise, and emergency rotation.
2. Vault or APISIX secret-resolution failure.
3. OpenAI or Anthropic outage, 429 surge, or elevated latency.
4. Streaming connections exceeding duration/size limits.
5. Activation and rollback of an explicit cross-protocol conversion policy.
6. Tenant budget exhaustion and temporary quota override.
7. APISIX route rollback and etcd recovery.
8. Mobile/API contract incompatibility and forced minimum-version policy.
9. Graph ingestion rollback, entity-resolution error, and provenance correction.

## Build track

Phase 1, Track A Sprint 6 and Track H — see `todo.md`.
