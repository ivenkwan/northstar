# Architecture Decision Records

Architecture decisions for Sales Northstar, in the format defined by [TEMPLATE.md](TEMPLATE.md).

## Index

| ADR | Title | Status | PRD ref |
|---|---|---|---|
| [ADR-021](ADR-021-apisix-single-api-ai-gateway.md) | Apache APISIX is the sole enterprise API and AI gateway | Proposed | §12, §15 |
| [ADR-022](ADR-022-separate-native-llm-contracts.md) | OpenAI Chat Completions and Anthropic Messages remain separate native contracts | Proposed | §12, §15.5, §17.6 |
| [ADR-023](ADR-023-byok-vault-fail-closed.md) | BYOK credentials use Vault references and fail-closed lifecycle controls | Proposed | §16 |
| [ADR-024](ADR-024-opt-in-cross-protocol-conversion.md) | Cross-protocol conversion is opt-in and feature-matrix governed | Proposed | §15.5 |
| [ADR-025](ADR-025-react-native-strict-typescript-contracts.md) | React Native uses the Strict TypeScript API and generated end-to-end contracts | Proposed | §12, §17 |
| [ADR-026](ADR-026-runtime-schema-validation.md) | Dynamic agent/dashboard/graph payloads require runtime schema validation | Proposed | §17.1, §17.4, §18 |
| [ADR-027](ADR-027-zcode-ai-engineering-workbench.md) | ZCode is the standard AI engineering workbench | Proposed | §17.9, §20, §23.5, §28.2 |
| [ADR-028](ADR-028-api-path-convention.md) | Product APIs are versioned under `/api/v1` | Proposed | §15.2, §16.5, §19 |
| [ADR-029](ADR-029-graph-store-apache-age.md) | Knowledge-graph store is Apache AGE on PostgreSQL | Proposed | §13, §18 |
| [ADR-030](ADR-030-analytical-store-postgres-dbt.md) | Analytical store is PostgreSQL with dbt; lakehouse deferred | Proposed | §14, §22 |
| [ADR-031](ADR-031-native-cdc-connectors-temporal.md) | Ingestion uses native change-capture clients orchestrated by Temporal | Proposed | §14, §14.3 |
| [ADR-032](ADR-032-text-first-mvp-voice-phase2.md) | Text-first MVP; voice input deferred to Phase 2 | Proposed | §8.1, §10.2 |
| [ADR-033](ADR-033-single-tenant-deployment.md) | Single-tenant deployment; `tenantId` denotes the deploying enterprise | Proposed | §4.1, §16 |
| [ADR-034](ADR-034-alert-delivery-fcm-apns-smtp.md) | MVP alert delivery: FCM/APNs push + enterprise email; Teams Phase 2 | Proposed | §8.6, §24.3 |
| [ADR-035](ADR-035-iac-terraform-rke2.md) | Terraform IaC; RKE2 production Kubernetes; kind local; Argo CD GitOps | Proposed | §15.1, §17.9 |
| [ADR-036](ADR-036-victory-native-xl-charts.md) | Mobile charts use Victory Native XL with mandatory accessible data tables | Proposed | §8.5, §10.2, §17.5, §22 |

ADR-028–036 close the Phase 0 open decisions from the [PRD review](../reviews/prd-v1-review.md) (F-01, F-03, F-05, F-06, F-07 and the tooling selections); they remain **Proposed** until the architecture review board accepts them — see the [ADR review package](../governance/adr-review-package.md).

## Numbering note

Numbering begins at **ADR-021** to remain traceable to PRD §30, which names these decisions ADR-021–026. ADR-001–020 belonged to the superseded Product Proposal v1.0 / Technical Architecture v2.1 documents and were not carried into this repository. New decisions continue from ADR-037.

## Governance

These are **release-governing** decisions (PRD §30): an exception requires security, architecture, and product-owner approval. Each ADR carries verification criteria that map into the golden and conformance test suites (`tests/golden`) and the engineering acceptance criteria (PRD §28.2).

## Status legend

- **Proposed** — written and reviewed against the PRD; awaiting formal approval at the Phase 0 architecture review.
- **Accepted** — approved; exceptions need tri-party sign-off.
- **Superseded** — replaced by a later ADR (link retained).
