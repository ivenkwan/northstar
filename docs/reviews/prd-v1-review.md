# PRD Review — prd-v1.md

| | |
|---|---|
| **Document reviewed** | `prd-v1.md` — Sales Northstar, Product Proposal and Detailed Technical Specification, v3.0 (consolidated), 26 September 2026 |
| **Review date** | 26 September 2026 |
| **Reviewer** | Engineering bootstrap review (pre-Phase 0) |
| **Verdict** | **Approved as planning baseline, with findings.** No blocking defect in the architecture; the findings below should be resolved or explicitly deferred during Phase 0 discovery. |

## 1. Scope summary

Sales Northstar is a secure, mobile-first, multi-agent sales intelligence platform: CRM-agnostic canonical data model (Salesforce + Dynamics 365 first connectors), governed semantic layer, conversational analytics with evidence and lineage, self-configurable declarative dashboards, market intelligence with citations, and controlled write-back actions. Delivery is phased: 2-week discovery, 12–16 week MVP, 8–12 week hardening, ongoing optimization.

Technology baseline: React Native (Strict TypeScript) mobile app, FastAPI mobile BFF, LangGraph agent orchestrator, Apache APISIX as the sole north–south API and AI gateway with enterprise BYOK in HashiCorp Vault, Temporal workflows, PostgreSQL/OpenSearch + pgvector/graph storage, OpenTelemetry observability.

## 2. Strengths

1. **The hardest domain problem is solved on paper, first.** The effective-dated organization model (§6) with explicit `DomainGroupMembership` allocation policies (`reporting_role`, `pipeline_allocation_pct`, `aggregation_policy`) prevents the classic double-counting and leakage failures of sales roll-ups. Golden tests (§23.2) target exactly this.
2. **Deterministic workflow around probabilistic models.** The 12-step orchestration pattern (§9.2) — authorize every query, no direct LLM database access, mandatory semantic layer, output recheck, confirmation for writes, immutable trace — is the correct posture for enterprise trust.
3. **Fail-closed BYOK with cited failure mode.** §16.4 doesn't just say "use Vault"; it names the specific APISIX behavior (unresolved secret remaining as literal string) and adds pre-deployment validation, synthetic probes, circuit breaking, and no implicit platform-key fallback.
4. **Enforceable mobile engineering standard.** §17 pins exact compiler flags, prohibited patterns, the OpenAPI→TypeScript→Zod contract pipeline, discriminated unions for widgets, branded IDs, and a typed error envelope — all CI-checkable rather than aspirational.
5. **Test strategy with gates, not just test types.** Evaluation layers (§23.1) each carry a gate; gateway conformance (§23.3) and mobile quality gates (§23.4) are concrete and automatable; engineering acceptance criteria (§28.2) are demonstrable true/false.
6. **Governance is integrated, not bolted on.** Zero-trust access model (RBAC + ABAC + ReBAC), denied-inference suppression, PDPO/PCPD alignment, anonymized evaluation datasets, and tamper-evident audit records appear in requirements, not just a compliance appendix.
7. **Honest measurement discipline.** NFRs are labeled as targets; business outcomes are stated as categories to measure rather than unsourced percentages; the commercial section demands a controlled pilot rather than speculative ROI.

## 3. Findings

Severity: **B** = blocks or distorts Phase 0/1 planning if unresolved; **W** = should fix in the next document revision; **N** = note.

| # | Severity | PRD ref | Finding | Recommendation |
|---|---|---|---|---|
| F-01 | B | §15.2 vs §19.2 | **API path inconsistency.** Route table defines sales APIs as `/api/v2/*`, but §19.2 core endpoints are `/v1/conversations`, `/v1/pipeline`, etc. Two conventions, two version numbers. | Pick one convention (suggest: `/api/v1/...` for product APIs, reserving `/ai/*` and `/internal/*` prefixes) before any OpenAPI document is authored. |
| F-02 | B | §24.2 | **Sprint plan covers only two of ~eight tracks.** The 6-sprint table budgets gateway/BYOK and mobile only. Data foundation, semantic layer, agent roster, market intelligence, dashboards, alerts, and governance — the majority of MVP scope — have no time budget. | Expand the sprint plan to all tracks (done provisionally in `todo.md` Track C–H) and reconcile the total against the 12–16 week window in Phase 0. |
| F-03 | B | §8.1 (CONV-01), Part II | **Voice is "Must" with no architecture.** Text and voice input is a must-have acceptance condition, but no STT provider, pipeline, consent handling, or latency budget appears anywhere in Part II. | Either add an STT architecture decision (provider behind APISIX, transcript-confirmation flow per §10.2) or reclassify voice as "Should" for MVP. Feed into ADR list. |
| F-04 | W | §30 | **ADR numbering starts at 021 with no 001–020 in this repo.** The numbering implies a prior ADR series in the superseded v2.1 specification that was not carried over. | Resolved for this repo: keep PRD numbering for traceability, note the gap in the ADR index (`docs/adr/README.md`). |
| F-05 | W | §4.1 vs §16, §23.3 | **Tenant model tension.** Deployment is "single-enterprise private cloud/VPC", yet BYOK is tenant-scoped (`tenantId`, tenant A/B isolation tests). Whether "tenant" means enterprise, region, or business unit is undefined. | Define the tenant model in Phase 0 (single-tenant deploy with tenant-ready isolation is the likely intent); record as an open decision. |
| F-06 | W | §8.6 vs §24.3 | **Teams delivery ambiguity.** §8.6 lists Teams among alert delivery channels; §24.3 defers Teams integration to Phase 2. | State explicitly that MVP delivery is in-app push + email, with Teams in Phase 2. |
| F-07 | W | §13, §14 | **Two core stores are unnamed boxes.** The graph projection and the warehouse/lakehouse engine have no product selection, sizing, or ADR. The canonical model and semantic layer depend on both. | Add to Phase 0 open decisions (see §4 below); candidate ADRs required before Sprint 3. |
| F-08 | W | §8.3, §14.1 | **FX rate source unspecified.** Currency appears in scenario controls, targets, and opportunities, but no FX rate table, source, or as-of policy is defined. | Add an FX rate reference dataset and policy to the semantic layer backlog (Track C). |
| F-09 | W | §10.2 | **Offline mode has no NFRs.** Requirements say "approved, encrypted, time-limited summaries" but there are no sync, conflict, expiry, or remote-wipe behavioral specs beyond the mobile gate "no secrets in cache". | Write offline behavior NFRs before Track B implements caching (Sprint 3+). |
| F-10 | B | §4.2, §9.1 | **MVP scope vs window is high risk.** Ten agents, eight personas, five navigation areas, two CRM connectors, knowledge graph, BYOK service, dashboard composer, alerts, and controlled actions in 12–16 weeks with a ~10-person squad assumes near-perfect execution, and the 6-sprint table implies 12 weeks for gateway + mobile alone. | Agree an explicit de-scope order now (see §5) and treat Phase 1 exit criteria (§28) as the contract, not the feature list. |
| F-11 | N | file name | **File named `prd-v1.md` but document version is 3.0** (consolidated, superseding v1.0 and v2.1). Confusing when cross-referencing. | Rename to `prd-v3.md` at next revision, or note the mapping in the README. |
| F-12 | N | §11.3, §27 | **Retention/deletion is policy-level only.** PDPO alignment implies data retention and deletion obligations, but no backlog epic covers retention execution (news expiry exists for signals only). | Add a retention/deletion story to Track H (governance) in Phase 1 or Phase 2. |
| F-13 | N | §19.1 | **GraphQL "may be added" without a guardrail story.** The principle "must not bypass policy enforcement" is right, but no test or gate is defined for it. | If GraphQL is ever taken, extend the golden authorization suite to it; otherwise strike it to reduce surface. |

## 4. Open decisions to close in Phase 0

These are required inputs to sprint planning and are carried into `todo.md` Phase 0:

1. **Graph store** — engine and product for the entity/relationship graph (§13, §18).
2. **Warehouse/lakehouse engine** — analytical store product and provisioning model (§14).
3. **CDC/ingestion tooling** — connector framework for CRM/planning/news sources (§14).
4. **STT pipeline** — provider, consent, and latency budget for voice (F-03).
5. **Tenant model** — meaning of `tenantId` in a single-enterprise deployment (F-05).
6. **Notification service** — in-app push + email provider for MVP alerts (§8.6).
7. **IaC platform** — Terraform/Pulumi/other for infra in `infra/` (§15.1 implies GitOps).
8. **Kubernetes distribution and environment topology** — non-prod/prod clusters, failure zones (§15.1).
9. **API path convention** — resolve F-01 before authoring the first OpenAPI document.
10. **Chart/rendering library for mobile** — must satisfy WCAG 2.2 AA table-alternative requirement (§8.5, §22).

## 5. Suggested de-scope order (if Phase 1 compresses)

Highest confidence last — cut from the top:

1. Voice input (after F-03 resolution; text-only MVP).
2. Relationship-graph dashboard widget (§8.5) — keep list/table views.
3. Scheduled briefings (§8.6) — keep threshold alerts only.
4. Second CRM connector (Dynamics 365) — ship Salesforce-only.
5. Controlled write-back actions (§8.7) — read-only intelligence first (already the PRD's stated instinct, §4.1).
6. Scenario controls (§8.2) — core attainment/coverage metrics stay.

Do **not** de-scope: identity/hierarchy, semantic layer, policy enforcement, audit, evidence/citations — they are the product's durable advantage (§33) and retrofitting them is the most expensive failure mode.

## 6. Review conclusion

The specification is unusually complete for a proposal: decisions are named, testable, and mostly already mapped to ADRs. The material risks are schedule realism (F-10, F-02), two unspecified core stores (F-07), and a handful of consistency defects (F-01, F-03, F-06) that are cheap to fix now and expensive to fix after contract generation begins. Proceed to Phase 0 with the open-decision list as a mandatory input to discovery.
