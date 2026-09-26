# ADR-023: BYOK credentials use Vault references and fail-closed lifecycle controls

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §16, §15.3, §15.6, §20, §28.2 criteria 3–5 |

## Context

Enterprise tenants supply their own LLM provider keys (BYOK). Keys must never appear in Git, etcd exports, mobile builds, traces, or logs; the mobile app must never receive or forward them. APISIX's documented secret-resolution behavior carries a specific hazard: an unresolved `$secret://` reference can remain as a literal string in configuration while an error is written to the log (PRD §16.4) — a naive deployment would then send the literal reference string as a credential or fail ambiguously.

## Decision

Provider keys reside **only** in HashiCorp Vault under tenant-scoped paths. The BYOK Credential Service (`services/byok`) owns lifecycle metadata and never returns plaintext after submission; APISIX configuration contains only `$secret://` references and credential metadata. On top of basic resolution, the platform adds **fail-closed** controls:

1. Pre-deployment secret-existence validation by the configuration controller.
2. Synthetic authenticated probes after every route or secret revision.
3. Alerting on `failed to resolve secret reference` log events.
4. Circuit-breaker policy marking the credential binding unavailable after authentication failures.
5. **No fallback to a platform-owned key** unless the tenant explicitly opted into that policy.
6. User-facing `AI_CREDENTIAL_UNAVAILABLE` typed error that reveals no secret paths or provider responses.

Header sanitization runs **before** `ai-proxy` (only `Host`, `Content-Length`, `Accept-Encoding` are dropped automatically), and client-supplied `Authorization`/`x-api-key` headers can never override resolved BYOK credentials (PRD §15.3, §15.5).

## Consequences

**Positive:**

- Credential theft surface is limited to Vault with least-privilege read policies, audit devices, and short-lived workload auth; rotation is a versioned secret operation with canary/promote/revoke.
- The known APISIX unresolved-secret behavior is compensated rather than discovered in an incident.
- Tenant credential isolation is testable (tenant A cannot invoke tenant B's credential).

**Negative / accepted costs:**

- Vault becomes critical-path infrastructure for all AI traffic: its availability, backup, and recovery must be operated (runbook §29).
- Synthetic probes and circuit breakers add moving parts to route configuration and require telemetry to distinguish provider outage from credential failure.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Environment-variable or Kubernetes Secret key injection | Plaintext keys in workload configuration; no versioned rotation, audit devices, or tenant scoping; appears in exports and crash dumps. |
| Platform-owned keys with tenant billing | Violates the enterprise BYOK posture and the no-implicit-fallback rule (§16.4). |
| Database-encrypted credential store | Reimplements Vault's threat model (seal, audit, dynamic leases) inside the app tier with weaker guarantees. |

## Verification

- Engineering acceptance criteria 3–4 (PRD §28.2): credentials never appear in Git, etcd exports, mobile builds, traces, or logs; a missing or revoked secret fails closed with a sanitized typed error.
- Gateway conformance goldens: invalid/expired/missing Vault secret behavior; header stripping and server-side credential precedence; tenant A cannot invoke tenant B's credential.
- Acceptance criterion 5: tenant, environment, protocol, model, and domain bindings enforced before provider invocation.
