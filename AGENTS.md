# Sales Northstar Agent Instructions

These instructions govern AI-assisted engineering in this repository. ZCode reads this root file as the workspace instruction source.

## Mission

Build Sales Northstar as a secure, mobile-first enterprise sales intelligence assistant. Preserve deterministic authorization, certified metrics, evidence-bearing retrieval, native OpenAI and Anthropic contracts, fail-closed BYOK, and strict TypeScript boundaries.

## Working method

1. Read `README.md`, the relevant section of `prd-v1.md`, the nearest component `README.md`, and applicable ADRs before proposing changes.
2. Use **Plan mode** before broad, cross-service, schema, security, infrastructure, or dependency changes.
3. Keep edits scoped to the requested outcome; do not perform unrelated refactors.
4. Add or update tests with every behavior change.
5. Run the narrowest relevant checks first, then the repository verification task before completion.
6. Review the final diff and report files changed, commands run, test results, assumptions, and unresolved risks.
7. Never claim a check passed unless the command actually completed successfully.

## Non-negotiable architecture

- Apache APISIX is the sole north-south API and AI gateway.
- OpenAI Chat Completions and Anthropic Messages remain separate native contracts.
- Provider credentials reside only in HashiCorp Vault; no secret or resolvable Vault path may enter Git, logs, fixtures, screenshots, prompts, or mobile bundles.
- Cross-protocol conversion is disabled unless an approved feature-matrix policy explicitly enables it.
- Mobile code uses React Native Strict TypeScript, generated OpenAPI contracts, Zod validation, typed navigation, branded identifiers, and exhaustive discriminated unions.
- Agents never execute raw model-generated SQL, Cypher, Gremlin, shell, or provider payloads.
- All data access is authorized against authenticated tenant, team, domain, group, classification, and purpose context.
- Every market-intelligence or graph claim carries provenance, confidence, and freshness.
- CRM writes require authorization, preview, explicit confirmation, idempotency, and an immutable receipt.

## Repository boundaries

- `apps/mobile`: no direct provider calls, no raw `fetch` outside the transport package, and no duplicated backend DTOs.
- `apps/admin`: administrative actions require strong authorization and auditable APIs.
- `packages/contracts`: generated from OpenAPI; do not hand-edit generated output.
- `packages/validation`: validate every untrusted dynamic boundary.
- `services/orchestrator`: orchestrate bounded tools; do not place business formulas in prompts.
- `services/metrics`: only certified formulas and approved joins.
- `services/knowledge-graph`: typed query IR only; no raw database language from models.
- `services/byok`, `infra/apisix`, `infra/vault`, `infra/k8s`: default to Ask before changes; require explicit human review.
- `data/canonical-model`, `data/semantic-layer`: version schema and metric changes and preserve lineage.

## Quality gates

- TypeScript: strict compilation, lint, unit tests, contract generation drift check, and mobile E2E where affected.
- Python: formatting, lint, type checking, unit/integration tests, and OpenAPI compatibility where affected.
- Gateway/BYOK: native protocol conformance, secret-failure, tenant-isolation, header-sanitization, and streaming tests.
- Agent/RAG: authorization, provenance, groundedness, prompt-injection, output-policy, and regression evaluations.
- Infrastructure: schema/manifest validation, policy checks, secret scanning, and least-privilege review.

The canonical ZCode setup and operating controls are in `docs/development/zcode-toolchain.md`. ZCode output is untrusted until reviewed and accepted by the normal CI/CD gates.
