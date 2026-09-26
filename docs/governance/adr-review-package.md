# ADR review package — Phase 0 architecture review board

Single agenda for the board session required by PRD §24.1 ("Approve ADR-027, the ZCode provider/data policy, root `AGENTS.md`, plugin trust boundary, and agent-assisted development acceptance gates") plus acceptance of the Phase 0 decision set. Approving this package moves the listed ADRs from Proposed to Accepted.

## Decision items

| # | Item | Artifact | Notes for reviewers |
|---|---|---|---|
| 1 | APISIX sole gateway; native dual contracts; BYOK fail-closed; opt-in conversion | [ADR-021](../adr/ADR-021-apisix-single-api-ai-gateway.md)–[024](../adr/ADR-024-opt-in-cross-protocol-conversion.md) | Carried from PRD §30; engineering acceptance §28.2 items 1–6 |
| 2 | Strict TypeScript + generated contracts; runtime schema validation | [ADR-025](../adr/ADR-025-react-native-strict-typescript-contracts.md), [ADR-026](../adr/ADR-026-runtime-schema-validation.md) | §28.2 items 7–10 |
| 3 | ZCode workbench, provider/data policy, AGENTS.md, plugin trust boundary | [ADR-027](../adr/ADR-027-zcode-ai-engineering-workbench.md), [AGENTS.md](../../AGENTS.md), [toolchain guide](../development/zcode-toolchain.md) | Explicit §24.1 approval item; gates §23.5 |
| 4 | API path convention `/api/v1` | [ADR-028](../adr/ADR-028-api-path-convention.md) | PRD v3.2 amended; unblocks OpenAPI authoring (F-01) |
| 5 | Graph store Apache AGE; analytical store Postgres+dbt | [ADR-029](../adr/ADR-029-graph-store-apache-age.md), [ADR-030](../adr/ADR-030-analytical-store-postgres-dbt.md) | Both carry explicit revisit triggers (F-07) |
| 6 | Native CDC connectors on Temporal | [ADR-031](../adr/ADR-031-native-cdc-connectors-temporal.md) | Sandbox validation is a Phase 0 exit item |
| 7 | Voice deferred to Phase 2 (CONV-01 amended) | [ADR-032](../adr/ADR-032-text-first-mvp-voice-phase2.md) | Reduces F-10 schedule risk |
| 8 | Single-tenant deployment; `tenantId` = enterprise instance | [ADR-033](../adr/ADR-033-single-tenant-deployment.md) | Resolves F-05; isolation-test interpretation |
| 9 | Alert delivery FCM/APNs + SMTP; Teams Phase 2 | [ADR-034](../adr/ADR-034-alert-delivery-fcm-apns-smtp.md) | Resolves F-06; metadata-only push |
| 10 | Terraform/RKE2/kind/Argo CD | [ADR-035](../adr/ADR-035-iac-terraform-rke2.md) | §15.1 topology made concrete |
| 11 | Victory Native XL + mandatory table alternatives | [ADR-036](../adr/ADR-036-victory-native-xl-charts.md) | WCAG 2.2 AA structural rule |
| 12 | Phase 1 plan (14 weeks) + de-scope order pre-authorization | [phase-1-plan-validation.md](../discovery/phase-1-plan-validation.md) | F-02/F-10 closure; levers 1–4 to PO |

## Evidence pack

- [Threat model](../security/threat-model.md) — T-01…T-18 mapped to controls and tests.
- [DPIA](dpia.md) and [AI risk assessment](ai-risk-assessment.md) — circulated separately for DPO/forum approval.
- [Discovery artifacts](../discovery/README.md) — questionnaire, pilot plan, connector plan, UX blueprint, assumptions register.
- Draft artifacts: [canonical schema](../../data/canonical-model/schema.sql), [metric catalog](../../data/semantic-layer/metric-catalog.yaml), [acceptance suite](../../tests/golden/acceptance-suite.md).

## Approval mechanics

Each board member records approve/reject per item; rejection of an item requires a written alternative and blocks only that item's ADR acceptance. Accepted ADRs are moved to **Accepted** in `docs/adr/README.md`; this page records attendee names and date. Exceptions after acceptance require security + architecture + product-owner sign-off (PRD §30).

| Attendee | Role | Items approved | Date |
|---|---|---|---|
| | Solution architect | | |
| | Security | | |
| | Product owner | | |
| | Data/privacy owner | | |
