# AI risk assessment — Phase 0 draft

Structured against the NIST AI RMF Generative AI Profile taxonomy (PRD §11.3, footnotes 15–16) and the PCPD Model Framework's governance expectations. Companion to the [DPIA](dpia.md) (privacy) and [threat model](../security/threat-model.md) (security). Status: draft for the AI/data governance forum.

## 1. System characterization

Multi-agent sales assistant: retrieval-grounded generation over governed semantic metrics, knowledge graph, and licensed news; deterministic workflow around models (§9.2); no autonomous external actions without confirmation (§8.7); humans are decision-makers for all consequential sales actions.

## 2. Risk register (NIST GenAI Profile categories)

| ID | Category (GenAI Profile) | Risk in Northstar | Controls (PRD) | Residual | Gate |
|---|---|---|---|---|---|
| R-1 | Human accountability | Unclear ownership of AI outputs | Named metric owners (§14.2); ADR governance (§30); audit traces attribute model/prompt/policy versions (§11.4) | Low | §23.5 |
| R-2 | Harmful bias / fairness | Territory mix baked into "deal health" signals | Transparent indicators; ML scores must show factors + calibration (§8.2); no automated personnel decisions (§4.3) | Medium | Eval layer UX |
| R-3 | Hallucination / confabulation | Wrong pipeline numbers trusted in decisions | Semantic layer only (no invented formulas); citations mandatory; abstention policy; groundedness evals (§23.1) | Medium | Generation gate |
| R-4 | Information integrity | Stale or reconciled-off data presented as current | As-of display mandatory (§14.3); freshness warnings; reconciliation gate (§23.1 data layer) | Low | Data gate |
| R-5 | Information disclosure | Cross-scope leakage in answers | T-04/T-10 controls; denied inference; leakage goldens | Low | Authorization gate (zero critical) |
| R-6 | Prompt injection | T-06/T-07 | Content isolation, typed tools, action confirmation, red team | Medium | Agent-safety gate |
| R-7 | Excessive agency | T-07/T-08 | Read-only default; preview/confirm; Temporal receipts; bulk/price/contract excluded (§8.7) | Low | Scenario E |
| R-8 | Value chain / supply chain | Provider or news-source misuse | BYOK + provider DPAs (DPIA §4); licensed sources with rights metadata; SBOM/scanning (§20) | Medium | C6 enablement check |
| R-9 | Cost/resource (denial of wallet) | T-12 | Budgets, caps, anomaly alerts | Low | GW-6 |
| R-10 | Employee surveillance perception | Adoption collapse / privacy harm | Purpose limitation, no hidden memory (§9.3), team-level analytics, notices + appeals (§11.3) | Medium | Pilot ethics checks |
| R-11 | IP / copyright | News summarization beyond license | Rights metadata; exclude non-AI-summarizable sources; legal review before C6 | Medium | Legal sign-off |
| R-12 | Environment/traceability of decisions | Cannot reconstruct why an answer was produced | Immutable AgentTrace with prompt/model/policy/evidence versions (§11.4) | Low | Audit test |

## 3. Risk-tiered human oversight (PCPD framework)

| Tier | Decisions | Oversight |
|---|---|---|
| T1 informational | Read-only analytics, briefings | User-visible provenance; thumbs feedback; no pre-publication review |
| T2 assisted authoring | Dashboard proposals, drafted tasks/emails, next-step suggestions | Explicit user confirmation before any write |
| T3 consequential | CRM field updates, forecast category changes | Preview + confirmation + receipt; step-up auth or manager approval for high-impact (§8.7) |
| T4 out of scope | Pricing, contracts, autonomous outreach, personnel decisions | Prohibited (§4.3) |

## 4. Monitoring and incident response

- Continuous: adoption/answer-quality telemetry (§25), groundedness sampling, injection-block counters (§25.3).
- AI incident class in the incident process: unsupported-claim reports, leakage suspicions, injection attempts → triage within 1 business day; feed PCPD "system management" expectations (§11.3).
- Quarterly reassessment of this register with the governance forum; ADR exceptions tri-party approved (§30).

## 5. Sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| AI governance forum chair | | | |
| Product owner | | | |
| Security/privacy | | | |
