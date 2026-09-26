# services/knowledge-graph — Knowledge graph service

Resolves organizations, industries, domains, groups, people, products, events, and relationships from approved public and enterprise sources into versioned graph bundles (PRD §18). Combines structural traversal with keyword and vector retrieval (OpenSearch + pgvector, PRD §13) before the agent synthesizes an answer.

## Hard rules

- Typed `GraphNode`/`GraphEdge` contracts with provenance and confidence (PRD §18).
- Agent-generated graph queries are compiled from a typed intermediate representation; raw Cypher, Gremlin, or SQL from a model is never executed directly.
- Attributes are filtered by user authorization before leaving the service; only bounded subgraphs go to mobile renderers.

## Open decision

Graph store engine is unnamed in the PRD (review finding F-07) — close in Phase 0 before Sprint 3.

## Build track

Phase 1, Track E — see `todo.md`.
