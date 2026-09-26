# ADR-029: Knowledge-graph store is Apache AGE on PostgreSQL

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §13, §18 |
| **Resolves** | PRD review finding F-07 (graph store unnamed) |

## Context

The knowledge-graph service needs a graph projection of organizations, industries, domains, groups, people, products, events, and relationships with provenance, confidence, and effective dating (§18). The PRD left the engine unnamed (F-07). Expected scale is modest at MVP: roughly 10⁵–10⁷ nodes/edges (org model + accounts + opportunities + news entities), single-enterprise deployment, queried via a typed IR — never raw model-generated Cypher.

## Decision

The graph projection runs on **Apache AGE** (openCypher extension) inside the existing PostgreSQL cluster, in a dedicated database with a dedicated role. Rationale:

- One database engine to operate, back up, secure, and audit — PostgreSQL is already the certified-metrics store (§13) and carries pgvector for embeddings.
- openCypher covers the traversal patterns the typed IR generates (bounded neighborhood expansion, path filters, attribute filters).
- Open-source Apache-2.0; no enterprise license for clustering/RBAC inside a private-cloud deployment.

**Revisit trigger (Phase 2):** if graph query p95 exceeds the §22 dashboard latency target at production volume, or the entity graph grows to rich multi-hop analytics beyond ~10⁷ edges, migrate to Neo4j Enterprise via the versioned graph-bundle export format (§18) — bundles are the interchange contract, so the engine remains swappable.

## Consequences

**Positive:** minimal new infrastructure; SQL-level backup/restore, row-level security, and audit tooling apply to graph data; export/import through graph bundles keeps engine neutrality.

**Negative / accepted costs:** AGE is younger than dedicated graph databases — accepted risk, mitigated by the typed-IR boundary (queries are generated, bounded, and parameterized, not ad-hoc) and the migration trigger above. Hybrid retrieval still combines AGE traversal with OpenSearch keyword and pgvector similarity (§18).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Neo4j Enterprise | Strongest graph engine, but per-core licensing cost in a single-enterprise VPC for a modest graph; adds a second operational stack now. Approved fallback at the revisit trigger. |
| NebulaGraph / Memgraph | Distributed-scale or in-memory engines sized for problems larger than ours; more operational surface than needed. |
| Plain relational tables + recursive CTEs | Workable for shallow traversals but multi-hop allocation and relationship queries (§6.2) become unwieldy and unbounded without a graph model. |

## Verification

- Golden test: typed-IR queries only — raw Cypher/Gremlin/SQL from models never executes (§28.2 criterion 10).
- Graph conformance suite in `tests/golden`: provenance and confidence preserved on every returned node/edge; bounded subgraph size enforced at the BFF.
- Performance check against the §22 dashboard latency target with a production-sized synthetic graph before Phase 1 exit.
