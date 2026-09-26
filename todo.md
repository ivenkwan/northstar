# Sales Northstar — Build Log and Plan

All build activities, organized by delivery phase (PRD Part III). This is the working checklist for the project: check items off as they complete, and log the completion date. Scope references point at `prd-v1.md` sections; findings marked F-NN point at `docs/reviews/prd-v1-review.md`.

**Phase overview**

| Phase | Scope | Duration | Status |
|---|---|---|---|
| Bootstrap | Repository setup | 1 day | ✅ Complete |
| Phase 0 | Discovery and control design | 2 weeks | 🟡 Artifacts built — enterprise inputs pending |
| Phase 1 | MVP | 10–14 weeks (6 sprints) | Not started |
| Phase 2 | Production hardening | 8–12 weeks | Not started |
| Phase 3 | Optimization | Ongoing | Not started |

**Phase 1 tracks**

| Track | Area | Owns |
|---|---|---|
| A | Gateway and BYOK | `infra/apisix`, `infra/vault`, `services/byok`, `infra/k8s` |
| B | Mobile type safety | `apps/mobile`, `packages/contracts`, `packages/validation`, `tools/codegen` |
| C | Data foundation and semantic layer | `services/connectors`, `services/metrics`, `data/*` |
| D | Agents and conversational analytics | `services/orchestrator`, `services/bff` |
| E | Market intelligence | `services/knowledge-graph`, `services/connectors` (news) |
| F | Dashboards, alerts, briefings | `apps/mobile` (features), `services/bff` |
| G | Controlled actions | `infra/temporal`, orchestrator Action Agent |
| H | Governance, audit, security testing | `tests/golden`, `tests/evals`, `infra/observability` |

---

## Bootstrap — repository setup (2026-09-26)


- [x] Adopt ZCode as the AI coding workbench; add root `AGENTS.md`, ADR-027, and the governed toolchain guide.
- [x] Add a reviewable `northstar` ZCode marketplace plugin with planning, verification, contract, and security workflows; no MCP servers or executable hooks enabled by default.
- [ ] Implement and pin the deterministic developer toolchain: mise, pnpm/Turborepo, uv, Docker Compose, kind/Tilt, GitHub Actions, and Argo CD.
- [ ] Validate ZCode through representative TypeScript, Python, gateway, and documentation tasks; record evidence for PRD §23.5.
- [ ] Security-review the enterprise APISIX model channel, provider data classification, retention/logging behavior, and any future MCP/plugin addition.

- [x] Review `prd-v1.md` and record findings → `docs/reviews/prd-v1-review.md` (13 findings; F-01/F-02/F-03/F-10 flagged as planning blockers for Phase 0).
- [x] Set up directory structure matching the solution architecture, with README stubs (purpose, PRD cross-refs, owning track) in every directory.
- [x] Record architecture decisions ADR-021–027 per PRD §30 → `docs/adr/` (status: Proposed, pending Phase 0 architecture review).
- [x] Create this build log (`todo.md`) organized by phases.

---

## Phase 0 — Discovery and control design (2 weeks, PRD §24.1) — artifacts built 2026-09-26; enterprise inputs pending

### Discovery

- [x] Confirm CRM, target-planning, activity, news, identity, mobile-device, and deployment landscape → instrument ready: `docs/discovery/landscape-questionnaire.md`; **[INPUT REQUIRED]** answers from enterprise stakeholders; assumptions A-1–A-7 registered in `docs/discovery/README.md`.
- [x] Validate hierarchy, domain–group allocation, fiscal calendar, currencies, and certified metric definitions (§6, §8.3) → validation checklist in questionnaire Q3/Q4; metric catalog draft `data/semantic-layer/metric-catalog.yaml` (owners/certification **[INPUT REQUIRED]**).
- [x] Select two pilot teams and define baseline measurements (§32) → selection criteria, matched controls, baseline metrics, thresholds: `docs/discovery/pilot-baseline-plan.md`; **[INPUT REQUIRED]** team nomination by sales ops.
- [x] Complete data protection impact assessment and AI risk assessment (§11.3) → drafts `docs/governance/dpia.md` + `docs/governance/ai-risk-assessment.md`; **[INPUT REQUIRED]** DPO/forum approval.
- [x] Produce UX prototype (five-destination IA, §10.1), canonical schema draft (§14.1), connector plan, threat model, and acceptance suite (§28) → `docs/discovery/ux-ia-blueprint.md` (wireframe-level; high-fidelity needs designer), `data/canonical-model/schema.sql` v0.1, `docs/discovery/connector-plan.md`, `docs/security/threat-model.md`, `tests/golden/acceptance-suite.md`.

### Open decisions to close (from PRD review §4)

- [x] Resolve API path convention (F-01) → **ADR-028**: `/api/v1/*`; PRD amended to v3.2 (§15.2, §16.5, §19.2).
- [x] Select graph store engine (F-07) → **ADR-029**: Apache AGE on PostgreSQL, Neo4j fallback trigger at Phase 2.
- [x] Select warehouse/lakehouse engine (F-07) → **ADR-030**: PostgreSQL + dbt; lakehouse deferred with explicit triggers.
- [x] Select CDC/ingestion tooling (F-07) → **ADR-031**: native change-capture clients (Salesforce Pub/Sub, Dynamics change tracking) on Temporal.
- [x] Decide voice/STT posture (F-03) → **ADR-032**: text-first MVP; voice reclassified Should/Phase 2; CONV-01 amended in PRD v3.2.
- [x] Define the tenant model (F-05) → **ADR-033**: single-tenant deployment; `tenantId` = enterprise instance; environments are isolation boundaries.
- [x] Select notification service (F-06) → **ADR-034**: in-app + FCM/APNs (metadata-only) + enterprise SMTP; Teams confirmed Phase 2.
- [x] Select IaC platform and Kubernetes distribution → **ADR-035**: Terraform; RKE2 production, kind local; Argo CD GitOps.
- [x] Select mobile chart library (WCAG 2.2 AA) → **ADR-036**: Victory Native XL; table alternative mandatory per widget.
- [x] Confirm Phase 1 sprint plan vs window (F-02/F-10) → `docs/discovery/phase-1-plan-validation.md`: 14-week plan, capacity model, critical path, de-scope levers; **[INPUT REQUIRED]** governance acceptance + lever pre-authorization.

All nine decisions recorded as ADRs (status Proposed); board acceptance pending below.

### Governance

- [ ] Architecture review board approves ADR-021–036, AGENTS.md, ZCode provider/data policy, and plugin trust boundary (§24.1) → agenda + evidence pack ready: `docs/governance/adr-review-package.md`.
- [ ] Stand up AI/data governance forum and product council (§26).
- [ ] DPO approves DPIA; governance forum accepts AI risk assessment (`docs/governance/README.md`).

**Exit:** discovery artifacts approved; open decisions closed and recorded as ADRs where architectural; pilot baselines captured.

**Phase 0 status:** all repository-buildable artifacts delivered (2026-09-26). Remaining exit criteria are enterprise/human inputs: questionnaire answers, pilot team nomination, metric-owner certification, and the three governance approvals. **[INPUT REQUIRED]**

---

## Phase 1 — MVP (10–14 weeks, PRD §24.2)

Sprints are two weeks. Tracks A and B follow the PRD §24.2 sprint table verbatim; tracks C–H extend it (review finding F-02). Each sprint lists its PRD exit condition.

### Sprint 1 — Foundation — *Exit: builds and smoke tests green*

- [ ] **A:** Deploy APISIX non-production topology — data plane (≥3 replicas across failure zones), restricted control plane, private etcd with mTLS and backups, Admin API off public listeners, GitOps declarative config (§15.1).
- [ ] **A:** Establish Vault paths, tenant-scoped policies, audit devices, workload auth (§16; ADR-023).
- [ ] **B:** Upgrade to approved React Native 0.87+ baseline with Strict TypeScript API; commit base `tsconfig` with the full §17.2 compiler policy.
- [ ] **B:** Stand up monorepo tooling (pnpm workspaces + Turborepo) and CI running `tsc --noEmit` + ESLint with prohibited-pattern rules (§17.1–§17.3).
- [ ] **C:** Canonical model schema v1 — all §14.1 entities with effective-dated relationships and `DomainGroupMembership` allocation fields (§6).
- [ ] **C:** Identity and hierarchy ingestion — sync users, teams, domains, groups, delegations (§27 epic 1).
- [ ] **H:** Telemetry foundation — OTel collectors, correlation/trace propagation, redacted access logs (§21).

### Sprint 2 — Contracts — *Exit: golden non-streaming contracts pass*

- [ ] **A:** Implement native routes `/ai/openai/v1/chat/completions` and `/ai/anthropic/v1/messages` with plugin chain order per §15.3.
- [ ] **A:** Header allow-list and sensitive-header stripping before `ai-proxy` (§15.3; ADR-023).
- [ ] **B:** Stand up `tools/codegen` pipeline — OpenAPI 3.1 export, Spectral lint, generated TS types/transport into `packages/contracts` (§17.4).
- [ ] **B:** Introduce `packages/validation` Zod boundary package; typed error envelope `ApiError` (§17.8).
- [ ] **C:** CRM connector (Salesforce) — raw landing zone, canonical transform, reconciliation totals (§14, §27 epic 2).
- [ ] **C:** Target-plan connector and governed metric catalog (attainment, coverage, gap definitions with lineage metadata) (§8.3, §14.2).
- [ ] **D:** Orchestrator skeleton (LangGraph) with the 12-step deterministic workflow; Identity & Scope Agent producing scope tokens and masking policy (§9).

### Sprint 3 — Streaming and semantics — *Exit: both streaming protocols pass*

- [ ] **A:** SSE for both native routes (OpenAI `[DONE]`; Anthropic events through `message_stop`); output-token ceilings, request/response-size and stream-duration limits (§15.5).
- [ ] **A:** Gateway telemetry — tokens, latency, time-to-first-token, stream duration, route revision (§21).
- [ ] **B:** Typed conversation stream consumption; dashboard widget discriminated union with exhaustive renderers (§17.5, §17.6).
- [ ] **C:** Certified metrics service serving governed pipeline/attainment/coverage/gap measures with `metric_definition_id` + version, freshness, scope, null treatment on every response (§14.2).
- [ ] **C:** Multi-group allocation and deduplication logic with non-additive labeling (§6.2; golden tests).
- [ ] **D:** Sales Analytics Agent over the semantic layer — no direct LLM→DB access; evidence chips and lineage (§9.2 step 6, CONV-03–05).

### Sprint 4 — BYOK and agents — *Exit: credential lifecycle E2E passes*

- [ ] **A:** BYOK admin APIs (submit/validate, list, rotate, test, bindings, delete) with idempotency keys and immutable audit events (§16.5).
- [ ] **A:** APISIX route config controller — validate, policy-check, stage, promote; pre-deployment secret-existence validation and synthetic probes (§16.3–§16.4).
- [ ] **B:** Typed admin portal screens and forms for BYOK (React Hook Form + Zod) (§17.1).
- [ ] **D:** Opportunity Agent (deal brief, risks) and Target & Forecast Agent (attainment, scenarios) (§9.1).
- [ ] **E:** News ingestion — licensed feeds, entity resolution, deduplication/clustering, signal taxonomy with rights metadata (§8.4).
- [ ] **F:** Saved views and alerts foundation — threshold rules, quiet hours, frequency caps, deep links permission-checked at open (§8.6).

### Sprint 5 — Resilience and composition — *Exit: chaos and type-quality gates pass*

- [ ] **A:** Approved multi-instance resilience via `ai-proxy-multi` (weighted balancing, health checks, bounded retries/fallback on 429/5xx); explicit conversion policy machinery, disabled by default (§15.4; ADRs 022/024).
- [ ] **B:** Navigation and deep-link hardening; eliminate remaining unsafe assertions — zero `any`/`@ts-ignore`/non-null assertions at boundaries (§17.3, §17.7).
- [ ] **D:** Market Intelligence Agent — relevance scoring, signal-to-opportunity mapping, sourced facts separated from interpretation (§7.3, §8.4).
- [ ] **D:** Dashboard Composer — conversational create/edit with server-side validation (metric compatibility, chart suitability, authorization, query cost) before save (§8.5; Scenario D).
- [ ] **E:** Knowledge-graph service — typed node/edge contracts with provenance; queries compiled from typed IR, never raw model-generated query text (§18; ADR-026).
- [ ] **G:** Controlled actions — preview/confirm flow, Temporal workflows, idempotent task creation, action receipts (§8.7; Scenario E).
- [ ] **F:** Briefings — daily seller briefing composition (§7.1).

### Sprint 6 — Hardening and release — *Exit: production readiness review approved*

- [ ] **A:** Security test, load test, runbooks (all nine §29 runbooks), canary, and rollback rehearsal.
- [ ] **B:** Mobile release candidate and device/compatibility testing; offline cache policy verification (no secrets, wipe-on-logout) (§10.2, §23.4).
- [ ] **H:** Golden permission suite — all §23.2 cases including double-counting, effective-dated transfers, access revocation.
- [ ] **H:** Agent red team — prompt injection, malicious documents, excessive agency, exfiltration (§11.2, §23.1).
- [ ] **H:** Evaluation harness with persona-scoped test sets; anonymized datasets (§23, §11.3).
- [ ] **C/H:** Reconciliation sign-off — certified totals reconcile to source (§27 epic 2 exit).
- [ ] **All:** UAT with pilot teams and pilot training (§24.2).

### Phase 1 acceptance gate (PRD §28)

**Product scenarios (§28.1):**

- [ ] Scenario A: personal target gap — scenario-based assessment with assumptions, freshness, evidence.
- [ ] Scenario B: group roll-up — no double counting; non-additive labels with allocation rules.
- [ ] Scenario C: malicious news article — content treated as evidence only; attempt logged.
- [ ] Scenario D: dashboard creation — certified metrics only; preview; save after confirmation.
- [ ] Scenario E: CRM update — old/new values shown; execute after confirm; idempotent retry.

**Engineering criteria (§28.2):**

- [ ] 1. APISIX is the only AI gateway and passes golden OpenAI + Anthropic contract suites.
- [ ] 2. Native Anthropic traffic preserves content blocks and SSE events without conversion.
- [ ] 3. Provider credentials exist only in Vault — never in Git, etcd exports, mobile builds, traces, or logs.
- [ ] 4. Missing/revoked secret fails closed with sanitized typed error.
- [ ] 5. Tenant, environment, protocol, model, and domain bindings enforced before provider invocation.
- [ ] 6. Retry/fallback bounded and tested; no silent platform-key fallback.
- [ ] 7. Mobile source is TypeScript-only; strict compilation passes with no waivers.
- [ ] 8. API clients generated from OpenAPI; runtime validation on all untrusted dynamic payloads.
- [ ] 9. Navigation, dashboards, graph views, conversation events use discriminated/branded types.
- [ ] 10. Graph queries authorized, provenance-bearing; no raw model-generated database code executed.
- [ ] 11. Security, performance, streaming, chaos, and tenant-isolation tests pass the release gate.

---

## Phase 2 — Production hardening (8–12 weeks, PRD §24.3)

- [ ] Add second CRM and/or region connectors where required (Dynamics 365).
- [ ] Traditional Chinese localization (locale-aware dates, numbers, currency, fiscal calendar; §22).
- [ ] Richer entity graph and expanded market-intelligence sources.
- [ ] Teams integration for alert delivery and briefings (resolves F-06 deferral).
- [ ] Manager workflow expansions (coaching, exception management, reassignment).
- [ ] Observability improvements — SLO-driven alerting, capacity forecasts, cost telemetry dashboards (§21, §22).
- [ ] Disaster recovery — RPO 5 min / RTO 1 hour for critical services; DR rehearsal (§22).
- [ ] Cost controls — routing, caching, token budgets, anomaly alerts (§31).
- [ ] Mobile device management integration and app-attestation hardening (§20).
- [ ] Accessibility — WCAG 2.2 AA external review (§22).
- [ ] Evaluation automation — CI-integrated retrieval/generation/agent-safety suites (§23).
- [ ] Approved forecast models only after back-testing meets calibration threshold (§23.1).
- [ ] Expand controlled actions and approval workflows (§8.7).
- [ ] Data retention/deletion execution (review F-12) and privacy operational reviews (§11.3).
- [ ] Voice/STT delivery if approved in Phase 0 (F-03).

---

## Phase 3 — Optimization (ongoing, PRD §24.3/§24.4)

- [ ] Next-best-action experiments with measured uplift (no causality claims without experiments).
- [ ] Territory and whitespace insights.
- [ ] Call/transcript intelligence.
- [ ] Partner selling and advanced account planning.
- [ ] Domain-specific playbooks and sales methodologies.
- [ ] Federated intelligence across approved internal knowledge sources.
- [ ] Controlled multi-agent workflow automation with progressive autonomy gated on measured safety and value (§33).
- [ ] Quarterly architecture and ADR review; supersede/extend ADRs from ADR-028 onward as decisions change.

---

## Change log

- **2026-09-26:** Built Phase 0 artifacts: discovery instruments (questionnaire, pilot plan, connector plan, UX blueprint, Phase 1 plan validation), canonical schema v0.1, metric catalog v0.1, threat model, DPIA + AI risk assessment, acceptance-suite spec, and ADR-028–036 closing all nine open decisions; PRD amended to v3.2 (F-01 `/api/v1`, F-03 voice deferral).
- **2026-09-26:** Replaced OpenCode recommendation with governed ZCode toolchain; added ADR-027, root instructions, toolchain guide, reviewed plugin, and PRD §17.9/§23.5 controls.

| Date | Change |
|---|---|
| 2026-09-26 | Bootstrap complete: PRD review, directory scaffold, ADR-021–027 (Proposed), this build log. |
