# data/canonical-model — Canonical sales data model

CRM-agnostic canonical entities that all connectors normalize into and all services read from (PRD §14.1). The canonical model is a Phase 0 deliverable (PRD §24.1).

## Entity inventory (PRD §14.1)

User, SalesPerson, Team, Domain, SalesGroup, DomainGroupMembership, Account, AccountDomain, Opportunity, OpportunityTeam, Activity, TargetPlan, ForecastSnapshot, MetricDefinition, NewsItem, Signal, Dashboard, AlertRule, AgentTrace.

## Modeling rules

- Organization membership, record ownership, and reporting scope are distinct concepts (PRD §6).
- All membership and allocation relationships are effective-dated (`valid_from`/`valid_to`) to support transfers and historical reporting (PRD §6.1).
- `DomainGroupMembership` carries `reporting_role`, `pipeline_allocation_pct`, `target_allocation_pct`, and `aggregation_policy` (PRD §6.2).
- Accounts may map to multiple domains; exactly one mapping is primary for default attribution (PRD §6.1).

## Build track

Phase 0 (schema design) → Phase 1, Track C (implementation) — see `todo.md`.
