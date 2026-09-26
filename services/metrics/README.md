# services/metrics — Certified metrics / semantic layer service

Serves governed measures, dimensions, joins, fiscal calendars, currencies, aggregation behavior, classifications, synonyms, and row-level policies (PRD §13, §14.2). The LLM may select allowed semantic objects but can never invent a production formula or arbitrary join.

## Planned responsibilities

- Execute governed pipeline, attainment, coverage, forecast-gap, velocity, aging, and movement metrics (PRD §8.2, §8.3).
- Attach to every analytical response: `metric_definition_id` + version, source refresh timestamp, effective scope, filters/grain/currency, null treatment, reconciliation status (PRD §14.2).
- Multi-group allocation and deduplication per `DomainGroupMembership` policy (PRD §6.2).
- Lineage endpoint: formula, owner, version, sources, quality (PRD §19.2 `/v1/metrics/{id}/lineage`).

## Storage

PostgreSQL (PRD §13). Metric definitions are versioned in `data/semantic-layer`.

## Build track

Phase 1, Track C — see `todo.md`.
