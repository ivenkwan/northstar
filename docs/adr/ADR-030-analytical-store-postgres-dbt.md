# ADR-030: Analytical store is PostgreSQL with dbt; lakehouse deferred

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, data engineering, product owner |
| **PRD references** | §14, §22 |
| **Resolves** | PRD review finding F-07 (warehouse/lakehouse unnamed) |

## Context

PRD §14 requires a warehouse/lakehouse tier between the canonical data products and the semantic layer, but names no engine (F-07). MVP scale is defined in §22: 5,000 users, 500 concurrent sessions, 10 million opportunities/activities in analytical storage — comfortably OLTP-to-mid scale, not petabyte lakehouse scale. Deployment is a single-enterprise private cloud where each additional engine carries real operating cost.

## Decision

For MVP (Phases 0–2), the analytical store is **PostgreSQL**: the same cluster pattern as the operational read model, in a dedicated analytics database with a dedicated role, partitioned by period for fact tables. Transformations from canonical data products to analytical marts are written in **dbt** (version-controlled models, tests, and lineage), so the semantic layer's certified metrics (§14.2) compile from reviewed SQL with documented lineage.

**Lakehouse deferral:** Apache Iceberg + Trino (or equivalent) is explicitly out of scope until a trigger fires: analytical volume beyond ~10⁹ fact rows, multi-region data residency, or second-enterprise deployments. Because all access flows through dbt models and the semantic layer, migrating the storage engine later does not change product APIs or metric definitions.

## Consequences

**Positive:** one engine family for operational, graph (ADR-029), vector, and analytical data; dbt gives reconciliation tests, freshness checks, and metric lineage required by §23.1; no cluster-ops burden in Phase 1.

**Negative / accepted costs:** columnaranalytics-style scans are slower than a lakehouse at the top of the scale range — accepted within §22 targets, verified by load test in Sprint 6; dbt introduces a build/runtime tool teams must learn.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| ClickHouse | Excellent scan performance but another engine to secure/operate; premature at 10M rows. |
| Iceberg + Trino now | Sizing mismatch; adds object-store, catalog, and cluster operations to a 12–16 week MVP. |
| DuckDB (embedded) | No concurrent multi-service access model; wrong shape for a shared warehouse. |

## Verification

- dbt tests implement the reconciliation gate (§23.1 data layer: no release with unresolved critical reconciliation errors).
- Load test in Sprint 6 validates §22 dashboard/analytical latency at 10M-row scale.
- Trigger conditions for lakehouse migration documented in this ADR and revisited quarterly (ADR review cadence, todo.md Phase 3).
