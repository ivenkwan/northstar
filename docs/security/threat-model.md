# Threat model — Phase 0 baseline

STRIDE-per-trust-boundary model over the PRD §13.1 boundaries, extended with the LLM/agentic threats from PRD §11.2, §20 and mapped to OWASP Top 10 for LLM Applications / Agentic AI threats (PRD footnotes 10–11). Ownership: platform security + solution architect; reviewed by the red-team exercise in Sprint 6.

## Assets

A1 Provider credentials (BYOK keys) · A2 CRM/planning source data · A3 employee identity & hierarchy · A4 pipeline/forecast analytics · A5 news/license content · A6 audit traces · A7 dashboard/alert definitions · A8 mobile device cache · A9 model routing/budget policy.

## Trust boundaries

B1 Mobile → gateway · B2 Gateway → providers (LLM/STT/news egress) · B3 Gateway → BFF/services · B4 Services → data stores (Postgres/AGE/OpenSearch/Vault) · B5 Services → CRM (Temporal actions) · B6 Ingestion → raw landing.

## Threat register

| ID | Boundary | Threat (STRIDE) | Asset | Control (PRD) | Test |
|---|---|---|---|---|---|
| T-01 | B2 | Credential theft via forwarded headers | A1 | Header strip before `ai-proxy`; server-side key injection; client `Authorization` cannot override | GW-2 goldens (§23.3) |
| T-02 | B4 | Vault secret resolution failure leaks literal reference or fails open | A1 | Fail-closed controls: pre-deploy validation, probes, circuit breaker (ADR-023) | GW-4 |
| T-03 | B2 | Tenant/environment credential mix-up | A1,A9 | Tenant-bound credential IDs; bindings checked pre-dispatch (ADR-033) | GW-5 |
| T-04 | B1/B3 | Cross-scope data access (seller → peer, team → domain) | A2,A4 | RBAC+ABAC+ReBAC; scope tokens; denied-inference suppression (§11.1) | Golden perm suite |
| T-05 | B3 | Effective-dating error leaks historical scope or double counts | A4 | Effective-dated memberships; allocation policy; goldens (§6, §23.2) | Golden roll-up cases |
| T-06 | B6→model | **Prompt injection** via news/CRM notes/attachments | A2,A5 | Untrusted-content isolation; retrieval filters pre-model; tool allowlists + typed args (§11.2) | Red team; Scenario C |
| T-07 | B3 | Retrieved content triggers tool calls (excessive agency) | A2 | Deterministic plan authorization per tool call; human confirm for writes (§9.2) | Agent-safety evals |
| T-08 | B5 | Unauthorized/idempotent-breaking CRM write | A2 | Preview→confirm→Temporal receipt; idempotency keys (§8.7) | Scenario E |
| T-09 | B3 | Model hallucinates metric/join (wrong number trusted) | A4 | Semantic layer only; no LLM-generated SQL (§9.2, §14.2) | Analytics gate: exact match |
| T-10 | B2 | Output exfiltration of restricted fields in answers | A2 | Output DLP, field masking, citations masked when source not permitted (CONV-05) | Leakage goldens |
| T-11 | B1 | Deep-link to unauthorized view | A2,A7 | Permission check at open time, not share time (§10.2) | Deep-link nav tests |
| T-12 | B2 | Cost abuse / denial-of-wallet | A9 | Per-tenant request/token budgets, concurrency + output caps, anomaly alerts (§20) | GW-6 rate/budget tests |
| T-13 | B4 | Audit tampering (repudiation) | A6 | Tamper-evident, append-only, access-controlled audit store (§11.4) | Audit integrity test |
| T-14 | B1 | Offline cache leakage on lost device | A2,A8 | Approved-only encrypted time-limited cache; remote wipe; no secrets in cache (§10.2, §23.4) | Mobile offline gate |
| T-15 | B6 | Supply-chain compromise (connector/news source) | A2,A5,A9 | Lockfiles, SBOM, dependency scanning, signed builds (§20); source allow/deny (§8.4) | CI SCA gate |
| T-16 | B3 | Protocol smuggling / schema drift between provider contracts | A9 | Exact content-type + body schema validators per route; 422 on unsupported fields (ADR-022/024) | GW conformance matrix |
| T-17 | B2 | Cross-protocol conversion silently drops semantics | A9 | Opt-in conversion + feature matrix + `x-northstar-protocol-converted` (ADR-024) | GW-7 |
| T-18 | All | AI-agent tooling misuse in development (repo side) | A1,A6 | AGENTS.md controls: no secrets in Git/logs, plan/ask modes, reviewed plugin, independent CI (§17.9, §23.5) | Secret scanning; CI reproducibility |

## Attack-surface notes

- The **mobile app holds no provider keys and no direct LLM routes** (B1 design) — device compromise yields only user-scoped tokens and an encrypted cache.
- **The gateway is the only egress** for model traffic; NetworkPolicy pins provider FQDNs (§15.1), so exfil-via-model has a bounded destination set.
- **Ingested content is the largest persistent untrusted corpus** — it is quarantined behind retrieval filters and never admitted to prompts raw (T-06/T-10 defense in depth).

## Residual risks (accepted, owner, review date)

| Risk | Owner | Review |
|---|---|---|
| AGE maturity (ADR-029) | Architect | Phase 2 entry |
| Native-connector API changes (ADR-031) | Data lead | Quarterly |
| LLM-groundedness on ambiguous questions | ML lead | Sprint 4 eval gate |
| News licensing terms for AI summarization | Legal | Before C6 enablement |
