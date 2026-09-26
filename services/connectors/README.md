# services/connectors — Source system ingestion

Connector and CDC layer for CRM (Salesforce, Microsoft Dynamics 365 first), target-planning, activity, ERP, and licensed news/filings sources (PRD §14 data architecture, §4.1).

## Planned responsibilities

- Land raw source data in the raw landing zone; normalize into canonical sales data products (`data/canonical-model`).
- Freshness targets: CRM 5–15 min; targets ≤30 min; activity metadata 15–60 min; news per feed SLA (PRD §14.3).
- Feed the content processing and vector index for external sources (PRD §14).
- Reconciliation totals back to source systems (PRD §27 "Sales data foundation" exit criterion).

## Hard rules

- External content is untrusted input: retrieved text cannot supply agent instructions, select tools, or override policies (PRD §8.4).
- Source allow/deny lists, geography rules, retention, and license status metadata travel with news items (PRD §8.4).

## Open decisions

CDC/ingestion tooling and second-connector timing — see review findings F-07 and the Phase 0 list in `todo.md`.

## Build track

Phase 1, Track C (CRM/plans) and Track E (news) — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
