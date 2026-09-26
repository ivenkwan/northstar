# Sales Northstar

Enterprise sales intelligence assistant — a secure, mobile-first, multi-agent platform that turns CRM, target, activity, organizational, and market data into a conversational, self-configurable dashboard. CRM-agnostic, deployable in a private cloud or enterprise VPC.

**Status:** Pre-Phase 0 (bootstrap complete). Specification: [`prd-v1.md`](prd-v1.md) (v3.0 consolidated). Working plan: [`todo.md`](todo.md).

## Key documents

| Document | Purpose |
|---|---|
| [`prd-v1.md`](prd-v1.md) | Product proposal and detailed technical specification |
| [`todo.md`](todo.md) | Build log and plan — all activities by phase |
| [`docs/reviews/prd-v1-review.md`](docs/reviews/prd-v1-review.md) | PRD review: strengths, findings, open decisions |
| [`docs/adr/`](docs/adr/README.md) | Architecture decision records (ADR-021–026) |
| [`docs/runbooks/`](docs/runbooks/README.md) | Operational runbooks (Phase 1, Sprint 6) |

## Repository structure

```
apps/
  mobile/             React Native 0.87+ app, Strict TypeScript (PRD §12, §17)
  admin/              Web administration portal (BYOK, metrics, connectors, audit)
packages/
  contracts/          Generated OpenAPI 3.1 → TypeScript types and transport
  validation/         Zod runtime schemas for all untrusted boundaries
services/
  bff/                Mobile BFF (FastAPI) — publishes the product API
  orchestrator/       Agent orchestrator (LangGraph) + agent roster
  metrics/            Certified semantic metrics service
  knowledge-graph/    Graph + hybrid retrieval service
  byok/               BYOK credential lifecycle service
  connectors/         CRM / target-plan / news ingestion
data/
  canonical-model/    Canonical entity schemas (effective-dated org model)
  semantic-layer/     Governed metric catalog, fiscal calendars
  quality/            Reconciliation and data-quality tests
infra/
  apisix/             Apache APISIX API + AI gateway (sole north–south gateway)
  vault/              HashiCorp Vault paths and policies (BYOK secrets)
  k8s/                Kubernetes manifests, Gateway API, NetworkPolicy
  temporal/           Temporal workflow infrastructure (controlled actions)
  observability/      OpenTelemetry, metrics, dashboards
tools/
  codegen/            OpenAPI → TypeScript contract pipeline
tests/
  golden/             Permission and gateway conformance suites
  evals/              AI evaluation datasets and harnesses
docs/
  adr/                Architecture decision records
  reviews/            Specification reviews
  runbooks/           Operational runbooks
```

Each directory contains a README describing its purpose, the governing PRD sections, and its owning build track in [`todo.md`](todo.md).

## Architecture baseline

- **Apache APISIX** is the sole north–south API and AI gateway with two first-class native LLM routes (OpenAI Chat Completions; Anthropic Messages) — [ADR-021](docs/adr/ADR-021-apisix-single-api-ai-gateway.md), [ADR-022](docs/adr/ADR-022-separate-native-llm-contracts.md).
- **Enterprise BYOK**: provider keys live only in HashiCorp Vault; fail-closed lifecycle controls — [ADR-023](docs/adr/ADR-023-byok-vault-fail-closed.md).
- **Mobile** is React Native with the Strict TypeScript API and generated end-to-end contracts — [ADR-025](docs/adr/ADR-025-react-native-strict-typescript-contracts.md).
- Dynamic agent/dashboard/graph payloads are runtime-validated — [ADR-026](docs/adr/ADR-026-runtime-schema-validation.md); cross-protocol conversion is opt-in — [ADR-024](docs/adr/ADR-024-opt-in-cross-protocol-conversion.md).

## Delivery phases

Phase 0 discovery (2 weeks) → Phase 1 MVP (10–14 weeks, 6 sprints, tracks A–H) → Phase 2 production hardening (8–12 weeks) → Phase 3 optimization (ongoing). Details, checklists, and acceptance gates: [`todo.md`](todo.md).

## License

See [LICENSE](LICENSE).
