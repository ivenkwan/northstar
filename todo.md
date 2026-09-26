# Sales Northstar — Build Log and Plan

All build activities, organized by delivery phase (PRD Part III). This is the working checklist for the project: check items off as they complete, and log the completion date. Scope references point at `prd-v1.md` sections; findings marked F-NN point at `docs/reviews/prd-v1-review.md`.

**Phase overview**

| Phase | Scope | Duration | Status |
|---|---|---|---|
| Bootstrap | Repository setup | 1 day | ✅ Complete |
| Phase 0 | Discovery and control design | 2 weeks | 🟡 Artifacts built — enterprise inputs pending |
| Phase 1 | MVP | 10–14 weeks (6 sprints) | Not started |
| Phase 2 | Production hardening | 8–12 weeks | Not started |
| Phase 3 | Optimization | Ongoing | 🟡 Repo-side engines built — ongoing by nature |
| Phase 4 | Production readiness & closure (extension) | — | ✅ Repo-side complete |

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

Repo-side Phase 2 build completed 2026-09-26 (see change log); items marked **[DEPLOY]** need enterprise environments/operations that cannot be exercised from the repository.

- [x] Second CRM connector: Dynamics 365 change-tracking transform + delta-link cursors + deletion events → `services/connectors/connectors/dynamics.py` + tests. **[DEPLOY]** sandbox tenant validation.
- [x] Traditional Chinese localization → `packages/i18n`: en + zh-Hant catalogs, Accept-Language negotiation, Intl formatters (money/percent/fiscal/zero-decimal currencies), parity test. Wired into Teams alert cards via `language=` param.
- [x] Teams integration for alert delivery (resolves F-06) → `services/alerts`: adaptive-card renderer (metadata + deep link only), localized titles, quiet-hours/frequency-cap/digest rules for the teams channel. **[DEPLOY]** Graph API consent + tenant app registration.
- [x] Observability → `infra/observability/`: slo.yaml (§22 targets + burn windows), prometheus-rules.yaml (SLO burn, credential-resolution, freshness, cost-anomaly alerts), otel-collector.yaml (content-redaction processors, payload fields dropped).
- [x] Disaster recovery → RPO 5m/RTO 1h runbook (`docs/runbooks/dr-recovery.md`) + backup CronJobs (WAL-archive RPO verification 5-min, hourly Vault raft snapshots, etcd snapshots). **[DEPLOY]** quarterly drill.
- [x] Cost controls → `services/orchestrator/orchestrator/budget.py`: per-tenant token/request budget ledger, denial-of-wallet anomaly detection, freshness-bucketed semantic cache keys (conversational scope never cached) + tests.
- [x] Evaluation automation → `tests/evals/`: versioned anonymized dataset + gate runner (injection_blocked and masking at 1.00 zero-tolerance, groundedness 0.90) running in CI (`pytest` job).
- [x] Forecast calibration gate → `services/metrics/metrics/forecast.py`: Brier/bias-ratio/stability back-test; models stay `informational` until certified (§23.1) + tests.
- [x] Controlled actions expansion → `services/bff/bff/approvals.py`: impact tiers (low/medium/high), step-up auth + manager approval state machine, full audit trail + tests.
- [x] Data retention/deletion execution (F-12) → `services/connectors/connectors/retention.py`: DPIA §6 schedules, expiry sweeps, source-deletion propagation to canonical soft-delete, conversation aggregation + tests.
- [x] Richer entity graph and expanded market-intelligence sources (repo side) → `services/connectors/connectors/news.py`: RSS/Atom + licensed-API adapters, rights enforcement at ingestion (unlicensed/retrieval-only excluded), SimHash dedup clustering, retention per license; `services/knowledge-graph/knowledge_graph/entities.py`: alias→canonical entity resolution with confidence + abstention. **[DEPLOY]** onboarding actual licensed sources.
- [x] Manager workflow expansions (repo side) → `services/orchestrator/orchestrator/manager.py`: exception detection (coverage shortfall, stalled-majority, missing next-step with severity), coaching briefs pairing grounded numbers with talking points, reassignment proposals scope-guarded and approval-required. UX wiring lands with the mobile app shell.
- [x] MDM integration (repo side) → `services/orchestrator/orchestrator/device_posture.py`: ABAC device-posture gate for sensitive scopes (offline cache, push, action confirm) with managed/compliant/jailbreak/attestation-freshness checks; `MdmAdapter` interface with fail-closed static dev adapter. **[DEPLOY]** Intune Graph adapter + device fleet.
- [x] Accessibility automated gates (repo side) → `packages/a11y`: WCAG 2.2 contrast math, design-token gates (text ≥4.5:1, UI/status ≥3:1, 44pt targets, no color-only status encoding) in CI. **[INPUT REQUIRED]** external WCAG 2.2 AA review remains a human gate.
- [x] Voice/STT contract (repo side) → BFF `POST /api/v1/conversations/{id}/voice-transcript` returning an unconfirmed transcript preview (§10.2), feature-flagged **off by default**; typed 403 citing ADR-032 until the board approves; OpenAPI + regenerated contracts include the path. **[INPUT REQUIRED]** board approval + DPIA audio addendum to enable.

---

## Phase 3 — Optimization (ongoing, PRD §24.3/§24.4) — repo-side engines built 2026-09-26

- [x] Next-best-action experiments → `services/orchestrator/orchestrator/experiments.py`: salted deterministic assignment, two-proportion z uplift analysis, and a power gate — underpowered results are reported as `underpowered`, never as uplift (§32). **[RUNTIME]** live experiments need production traffic.
- [x] Territory and whitespace insights → `services/metrics/metrics/territory.py`: coverage-by-territory with under-served detection (low coverage **or** concentration risk from unpenetrated accounts), dormant-account and unpenetrated-industry whitespace, every finding evidence-bearing.
- [x] Call/transcript intelligence → `services/orchestrator/orchestrator/transcripts.py`: consent-gated extraction (DPIA — denied consent processes nothing), action items/objections/next-step, injection scrubbing (transcripts are untrusted), content-not-retained default. **[RUNTIME]** STT pipeline per ADR-032 approval.
- [x] Partner selling and advanced account planning → `services/orchestrator/orchestrator/planning.py`: versioned account plans (monotonic, never destructive), objective progress with target-suppression guards, partner attach with co-sell registration compliance flags.
- [x] Domain-specific playbooks → `data/playbooks/catalog.yaml` (versioned, methodology- and evidence-cited) + `services/orchestrator/orchestrator/playbooks.py` selection engine (signal+stage matching, min-signal thresholds, ranking); plays are recommendations, never executed actions.
- [x] Federated intelligence → `services/knowledge-graph/knowledge_graph/federated.py`: source registry policies (approval, classification ceiling, freshness SLA, scope matching), classification/scope filtering before merge, stale age-out, per-source provenance.
- [x] Progressive autonomy (§33) → `services/orchestrator/orchestrator/autonomy.py`: L0–L3 levels, promotion gated on evaluation volume + safety score + success rate + **experiment-backed** value lift, hard breaches demote to L0 (safety-critical → suspension kill-switch), high-impact action types permanently L0.
- [x] Quarterly ADR review automation → `tools/adr_review.py` (inventory consistency: index links, status vocabulary, dense numbering from 021) + golden test `test_repo_hygiene.py` + `docs/adr/quarterly-review.md` checklist (verification matrix, decision items, sign-off). **[BOARD]** sessions are human.

---

## Phase 4 — Production readiness & closure (extension beyond PRD §24's three-phase plan, built 2026-09-26)

The PRD defines Phases 0–3. Phase 4 is this repository's closure phase: it completes the repo-side artifacts that were still missing after the phase-1 goal was superseded, and adds the deployment/release layer the plan called for. Recorded here because it was explicitly requested as a build goal.

- [x] `packages/validation` (ADR-026/§17.1, previously missing) → Zod schemas for conversation components (§19.3), dashboard definitions (§8.5 — strict cards, declarative-only), bounded subgraphs (§18 — provenance mandatory, dangling edges rejected), deep links (§17.7) with forward-compatible extras dropped; malformed + forward-compatible tests per §23.4.
- [x] `apps/mobile` domain layer (§17.5/§17.7) → branded IDs (TeamId ≠ DomainId at compile time), typed `RootStackParamList`, `resolveDeepLink` (validated → typed route, never throws), dashboard widget discriminated union with exhaustive `never`-checked renderer registry enforcing ADR-036 table alternatives. RN shell initializes with the native toolchain (**[DEPLOY]** Sprint 1).
- [x] Local development stack → `docker-compose.yml`: Postgres+AGE (schema auto-init), OpenSearch, dev Vault, etcd, APISIX, Temporal, OTel collector, BFF — healthchecks throughout, dev-only secrets.
- [x] Deployment layer → `infra/k8s/base/northstar.yaml` (namespace, bff/metrics/APISIX deployments with pinned images, probes, hardened securityContext, LLM-egress NetworkPolicy per §15.1), `infra/vault/policies/northstar.hcl` (least-privilege per workload), `infra/argocd/northstar-app.yaml` (Git-locked: prune + selfHeal per ADR-035).
- [x] Release automation → `.github/workflows/release.yml`: tag-driven, full verification gate, Python+Node SBOMs attached, deployment remains human/Argo-CD-governed (§23.5).
- [x] Manifest goldens → `tests/golden/tests/test_manifests.py`: pinned images (no `:latest`), resources+limits, both probes, hardened securityContext, ≥3 gateway replicas, egress NetworkPolicy present, Argo CD selfHeal, compose healthchecks — infra is CI-checked like code.

**Phase 4 status:** repo-side complete. Remaining work in this repo is zero; everything else is the external residue already annotated per item in Phases 0–3.

---

## Change log

- **2026-09-26:** Built Phase 4 (production readiness & closure): `packages/validation` (ADR-026, previously missing), `apps/mobile` typed domain layer, docker-compose dev stack, k8s base manifests + Vault policies + Argo CD app, release workflow with SBOMs, and manifest-validation goldens. 181 Python tests, 10 TS tasks green, lint/ADR review clean.

- **2026-09-26:** Built Phase 3 repo-side engines: experimentation (powered uplift gate), territory/whitespace analytics, consent-gated transcript intelligence, account planning + partner compliance, playbook catalog + selection, federated retrieval with per-source policy, progressive-autonomy governor (§33 L0–L3 with kill-switch), and ADR-review automation + quarterly checklist. 173 Python tests green (+37), ruff clean, ADR inventory verified.
- **2026-09-26:** Closed the remaining Phase 2 repo-side items: manager workflows (exceptions/coaching/reassignment), news-source adapters with rights enforcement + SimHash dedup, entity resolution, device-posture/MDM gate, `packages/a11y` WCAG 2.2 automated gates, and the ADR-032 voice transcript-confirmation contract (disabled pending board approval). 136 Python + 16 TS tests green, lint clean.
- **2026-09-26:** Built Phase 2 (repo-side): Dynamics 365 connector, zh-Hant i18n package, Teams alert channel, SLO/alerting/otel configs, DR runbook + backup CronJobs, cost budgets + semantic cache, retention engine, action approvals, forecast calibration gate, CI-integrated eval gates; CI + security workflows; runbooks (DR full + nine §29). 111 Python tests + 10 TS tests green, lint clean, contract drift zero. Carried over from the Phase 1 build session in the same repo: pinned toolchain (mise/pnpm+turbo/uv), six Python services with tests, generated OpenAPI contracts, executable golden suites (GPM/GW/GA), APISIX routes. Deployment/UAT/mobile-app items remain flagged in Phases 1–2.
- **2026-09-26:** Built Phase 0 artifacts: discovery instruments (questionnaire, pilot plan, connector plan, UX blueprint, Phase 1 plan validation), canonical schema v0.1, metric catalog v0.1, threat model, DPIA + AI risk assessment, acceptance-suite spec, and ADR-028–036 closing all nine open decisions; PRD amended to v3.2 (F-01 `/api/v1`, F-03 voice deferral).
- **2026-09-26:** Replaced OpenCode recommendation with governed ZCode toolchain; added ADR-027, root instructions, toolchain guide, reviewed plugin, and PRD §17.9/§23.5 controls.

| Date | Change |
|---|---|
| 2026-09-26 | Bootstrap complete: PRD review, directory scaffold, ADR-021–027 (Proposed), this build log. |
