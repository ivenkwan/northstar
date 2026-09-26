# ADR-033: Single-tenant deployment; `tenantId` denotes the deploying enterprise

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §4.1, §16, §23.3 |
| **Resolves** | PRD review finding F-05 |

## Context

The PRD deploys "single-enterprise private cloud/VPC" (§4.1) yet scopes BYOK credentials and isolation tests by `tenantId` with tenant-A/tenant-B separation (§16, §23.3) — leaving the tenant model undefined (F-05). Ambiguity here leaks into credential isolation, audit partitioning, and cost allocation.

## Decision

**Each deployment serves exactly one tenant.** `tenantId` identifies the deploying enterprise instance (e.g. `tenant_hktdv`), is provisioned at install time, and is carried on every token, credential binding, audit event, and telemetry record. Within a deployment, segregation is by the organizational model (teams/domains/groups, §6) — never by tenant. Multi-tenant SaaS is out of scope; if it ever ships, it requires new ADRs for shard/isolation strategy.

The §23.3 conformance case "Tenant A cannot invoke Tenant B's credential" is interpreted as **cross-deployment isolation**: credentials, Vault paths (ADR-023: `byok/<tenant>/...`), and audit stores are per-deployment, and staging/non-production environments count as separate tenants for isolation testing (e.g. a non-prod credential can never be invoked by the production gateway).

## Consequences

**Positive:** no tenant-sharding complexity in data model, query path, or authorization; Vault path scoping and per-tenant budget/telemetry semantics stay meaningful for cost attribution across environments; isolation tests have a crisp definition.

**Negative / accepted costs:** hosting N enterprises means N deployments — acceptable while the product is private-cloud delivered (§4.1); some multi-tenant-ready guards (tenant claim checks at the gateway) still ship now so a future SaaS posture is not blocked.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Multi-tenant pooled SaaS model now | Contradicts the deployment baseline (§4.1) and adds row-level/shard isolation to every critical path for a market not yet being served. |
| Tenant = business unit within one deployment | Conflates org modeling (§6) with tenancy; would break global roll-ups executives need. |

## Verification

- Gateway conformance: cross-environment credential isolation test per this ADR's interpretation.
- Static check: no schema, config, or query path keyed on multiple tenant IDs within one deployment.
