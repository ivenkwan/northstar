# infra/vault — HashiCorp Vault (BYOK secrets)

Stores provider API keys for the enterprise BYOK model (PRD §16; ADR-023). Configuration stores only secret references and credential metadata — never plaintext keys.

## Planned contents

- Tenant-scoped secret paths (e.g. `byok/<tenant>/<provider>/<slot>`).
- Least-privilege read policies for the APISIX data plane and config controller.
- Audit device configuration; short-lived workload authentication.
- Rotation runbooks and canary/promote/revoke procedures (PRD §16.3 step 7, §29).

## Rules

- APISIX secret references use the documented `$secret://` form; Vault KV v1 is the documented native manager (PRD §15.6 note).
- Fail-closed controls per PRD §16.4: pre-deployment existence validation, synthetic probes, resolution-failure alerting, circuit breaker, no implicit platform-key fallback.

## Build track

Phase 1, Track A Sprint 1 (paths) and Sprint 4 (lifecycle) — see `todo.md`.
