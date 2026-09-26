# data/quality — Reconciliation and data-quality tests

Data-layer evaluation and reconciliation suite (PRD §23.1: completeness, freshness, duplication, hierarchy validity, reconciliation). Gate: no release with unresolved critical reconciliation errors.

## Planned contents

- Source-to-canonical reconciliation totals per connector (PRD §27).
- Hierarchy validity: effective-dated membership consistency, single primary team/domain, one primary account-domain mapping (PRD §6.1).
- Multi-group double-counting checks across configured allocation policies (PRD §6.2, golden test §23.2).
- Freshness SLA checks per connector with breach alerts (PRD §14.3, §22).
- Data-quality scorecards for the admin portal (PRD §31 "Poor CRM quality" mitigation).

## Build track

Phase 1, Track C and Track H — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
