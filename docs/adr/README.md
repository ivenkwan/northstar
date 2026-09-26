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

## Numbering note

Numbering begins at **ADR-021** to remain traceable to PRD §30, which names these decisions ADR-021–026. ADR-001–020 belonged to the superseded Product Proposal v1.0 / Technical Architecture v2.1 documents and were not carried into this repository. New decisions continue from ADR-027.

## Governance

These are **release-governing** decisions (PRD §30): an exception requires security, architecture, and product-owner approval. Each ADR carries verification criteria that map into the golden and conformance test suites (`tests/golden`) and the engineering acceptance criteria (PRD §28.2).

## Status legend

- **Proposed** — written and reviewed against the PRD; awaiting formal approval at the Phase 0 architecture review.
- **Accepted** — approved; exceptions need tri-party sign-off.
- **Superseded** — replaced by a later ADR (link retained).
