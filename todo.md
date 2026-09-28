# Sales Northstar — Build Log and Plan

All build activities, organized by delivery phase (PRD Part III). This is the working checklist for the project: check items off as they complete, and log the completion date. Scope references point at `prd-v1.md` sections; findings marked F-NN point at `docs/reviews/prd-v1-review.md`.

**Phase overview**

| Phase | Scope | Duration | Status |
|---|---|---|---|
| Bootstrap | Repository setup | 1 day | ✅ Complete |
| Phase 0 | Discovery and control design | 2 weeks | 🟡 Artifacts built — enterprise inputs pending |
| Phase 1 | MVP | 10–14 weeks (6 sprints) | 🟡 Repo-side built & verified — markers audited 2026-09-27 |
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
- [x] Implement and pin the deterministic developer toolchain: mise (`.mise.toml`), pnpm/Turborepo (`pnpm-workspace.yaml`, `turbo.json`), uv (workspace + lockfile), Docker Compose (stack verified running 2026-09-26), GitHub Actions (`ci.yml`/`security.yml`/`release.yml`), Argo CD app manifest. **[OPEN: kind + Tilt configs — next iteration]**.
- [x] Validate ZCode through representative TypeScript (5 packages, turbo check+test green), Python (7 services, 188 tests), gateway (routes.yaml + GW goldens), and documentation (ADR/discovery/runbook sets) tasks; evidence = CI reproducing all gates from clean checkout (PRD §23.5).
- [x] Security-review the enterprise APISIX model channel (routes.yaml payload logging off, header strip, Vault-only secrets), provider data classification (DPIA §2), retention/logging behavior (retention engine + redacted otel config), MCP/plugins disabled by default (ADR-027). **[BOARD]** formal security sign-off pending.

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

- [x] **A:** APISIX topology → declarative config complete: `infra/apisix/routes.yaml` (plugin chains §15.3), `infra/k8s/base/northstar.yaml` (≥3 replicas, hardened securityContext, LLM-egress NetworkPolicy), compose APISIX + etcd. **[DEPLOY]** live cluster.
- [x] **A:** Vault paths and policies → `infra/vault/policies/northstar.hcl` (least-privilege per workload) + dev Vault in compose; fail-closed resolution verified in byok tests (GW-04). **[DEPLOY]** audit devices + workload auth on real Vault.
- [x] **B:** Strict TypeScript baseline → `tsconfig.base.json` with the full §17.2 flag set; all five packages compile clean. RN 0.87 shell **[DEPLOY]** native toolchain (domain layer built and tested in `apps/mobile`).
- [x] **B:** Monorepo tooling + CI → pnpm workspaces + Turborepo + `ci.yml` running `tsc --noEmit` per package. **[OPEN: ESLint prohibited-pattern rule pack — next iteration]** (§17.3).
- [x] **C:** Canonical schema → `data/canonical-model/schema.sql` v0.1: all §14.1 entities, effective-dated, `DomainGroupMembership` allocation fields; DDL parse-validated (pglast, zero forward-FK errors).
- [x] **C:** Identity/hierarchy model → `orchestrator/scope.py` OrgGraph (effective-dated, transfers) + resolver; connector plan C4. **[DEPLOY]** real IdP/HR sync.
- [x] **H:** Telemetry foundation → otel-collector configs (prod redaction + local), compose wiring, prometheus rules. **[OPEN: in-code OTel SDK instrumentation — next iteration]**.

### Sprint 2 — Contracts — *Exit: golden non-streaming contracts pass*

- [x] **A:** Native routes with §15.3 plugin chains → `infra/apisix/routes.yaml`; GW goldens validate chains, terminators, tool semantics. **[DEPLOY]** live APISIX run.
- [x] **A:** Header stripping before `ai-proxy` → configured in both native routes; GW-02 goldens assert removal sets + server-side Vault-only credentials.
- [x] **B:** Contract pipeline → committed OpenAPI 3.1 (`services/bff/openapi/openapi.json`) → `openapi-typescript` generation → drift check in CI. **[OPEN: Spectral ruleset — next iteration]** (§17.4 step 2).
- [x] **B:** `packages/validation` Zod boundary + typed `ApiError` (§17.8, mirrored across services) → 10 tests incl. malformed + forward-compatible (§23.4).
- [x] **C:** Salesforce connector → `connectors/transforms.py` + `landing.py` (idempotent, replay-safe) + reconciliation (§23.1 gate). **[DEPLOY]** sandbox tenant.
- [x] **C:** Metric catalog + plan ingestion → `metric-catalog.yaml` (14 governed metrics, lineage endpoint) + `PlanRow` engine support; target-plan source adapter **[INPUT REQUIRED]** questionnaire Q1.2 (connector plan C3).
- [x] **D:** Orchestrator with the 12-step workflow + Identity & Scope Agent (scope tokens, masking) → `orchestrator/pipeline.py` + `scope.py`; wired live via BFF composition root (verified end-to-end). LangGraph adapter is the deploy-time integration point.

### Sprint 3 — Streaming and semantics — *Exit: both streaming protocols pass*

- [x] **A:** SSE + limits → both SSE terminator orders golden-tested (fixtures) + BFF live SSE verified (`message_start → component → message_stop`); token/size/duration caps in routes.yaml (§15.5). **[DEPLOY]** live gateway.
- [x] **A:** Gateway telemetry config → summaries-on/payloads-off logging, cost-anomaly + credential rules (`prometheus-rules.yaml`). **[DEPLOY]** emission from live APISIX.
- [x] **B:** Typed conversation stream + widget discriminated union with exhaustive `never`-checked renderers → `apps/mobile` (5 tests, typecheck clean).
- [x] **C:** Certified metrics service → `metrics/engine.py` + api; every `MetricResult` carries metric_id+version, as_of, scope, null/suppression treatment, reconciliation status (§14.2).
- [x] **C:** Multi-group allocation + non-additive labeling → `metrics/allocation.py`; GPM-05/06 goldens (no double counting; rules surfaced).
- [x] **D:** Analytics over the semantic layer only → GA-05 golden (invented metric refused); evidence chips + lineage endpoint verified end-to-end (composition test + live smoke).

### Sprint 4 — BYOK and agents — *Exit: credential lifecycle E2E passes*

- [x] **A:** BYOK admin APIs → `byok/api.py` (register/list/activate/rotate/revoke) with idempotency keys + audit events (§16.5); redaction tested. **[OPEN: test/bindings endpoint surface — next iteration]**.
- [ ] **A:** APISIX route config controller — validate/policy-check/stage/promote. Partial: pre-deployment secret validation + probes exist inside `byok` activate; the controller service itself is **[OPEN: next iteration]** (§16.3–§16.4).
- [ ] **B:** Typed admin portal screens — `apps/admin` remains a README stub. **[OPEN: next iteration]** (React Hook Form + Zod).
- [ ] **D:** Opportunity Agent (deal brief, risks). Partial: attainment/forecast/scenarios + exception detection built (`engine.py`, `manager.py`); the deal-brief composition is **[OPEN: next iteration]** (§9.1).
- [x] **E:** News ingestion → `connectors/news.py`: rights enforcement, SimHash clustering, taxonomy-adjacent signals with rights metadata; entity resolution in KG (§8.4). **[DEPLOY]** licensed sources.
- [x] **F:** Alerts foundation → `services/alerts`: predicate/certified-metric validation (BFF), quiet hours, frequency caps, digests, metadata-only push + deep links re-authorized at open (scope re-check in pipeline). §8.6.

### Sprint 5 — Resilience and composition — *Exit: chaos and type-quality gates pass*

- [ ] **A:** `ai-proxy-multi` resilience policies (weighted balancing, health checks, bounded retries) — single-provider policies configured; the multi policy config + GW-10 retry-bound goldens are **[OPEN: next iteration]** (§15.4; ADRs 022/024; conversion machinery already disabled-by-default and golden-tested).
- [x] **B:** Navigation/deep-link hardening → runtime-validated links → typed routes (`packages/validation` + `apps/mobile`); strict compilation clean. **[OPEN: ESLint rule enforcement for §17.3 — next iteration]**.
- [x] **D:** Market intelligence → relevance (recency/entity/signal types), signal-to-opportunity mapping (entity_keys), sourced-vs-interpretation separation (pipeline + quarantined evidence) (§7.3, §8.4).
- [x] **D:** Dashboard Composer → `POST /api/v1/dashboards/compose` proposal (never auto-saved) + server-side save validation (certified metrics, allowed dimensions, layout) — Scenario D tests in `test_compose.py` (§8.5).
- [x] **E:** Knowledge-graph service → typed IR → parameterized Cypher, provenance-bearing nodes/edges, bounded subgraphs, raw-query rejection golden (§18; ADR-026).
- [x] **G:** Controlled actions → preview (old/new/impact) → confirm with idempotent receipts + impact-tier approvals; Temporal workers are the **[DEPLOY]** execution tier (§8.7; Scenario E).
- [ ] **F:** Briefings (daily seller composition, §7.1) — **[OPEN: next iteration]**; inputs exist (metrics, signals, exceptions).

### Sprint 6 — Hardening and release — *Exit: production readiness review approved*

- [ ] **A:** Security test, load test, canary, rollback rehearsal — runbooks ✓ (DR full + nine §29), security suites ✓ (goldens/evals); load test + canary **[DEPLOY]** on real infrastructure.
- [ ] **B:** Mobile release candidate + device/compat testing — domain layer green; RC requires the RN shell **[DEPLOY]** (§10.2, §23.4).
- [x] **H:** Golden permission suite → GPM-01..09 executable: scope isolation, roll-ups, double-counting, effective-dated transfers, access-revocation masking (§23.2).
- [x] **H:** Agent red team → GA-01..07 + zero-tolerance eval gates (injection/masking at 1.00) (§11.2, §23.1).
- [x] **H:** Evaluation harness → `tests/evals` with versioned anonymized dataset and CI gates (§23, §11.3). **[OPEN: expand persona-scoped corpus — next iteration]**.
- [ ] **C/H:** Reconciliation sign-off — mechanism + tolerance tests built; certified sign-off is **[INPUT REQUIRED]** (data-owner signature, §27 epic 2 exit).
- [ ] **All:** UAT with pilot teams — **[INPUT REQUIRED]** pilots + training (§24.2).

### Phase 1 acceptance gate (PRD §28)

**Product scenarios (§28.1):**

- [x] Scenario A: personal target gap — attainment report with guards/suppression, freshness, evidence (composition test + live smoke 2026-09-26).
- [x] Scenario B: group roll-up — GPM-06 no-double-count + non-additive labels with allocation rules (`group_view` tests).
- [x] Scenario C: malicious news article — GA-01: quarantined, logged, never executed.
- [x] Scenario D: dashboard creation — certified metrics only, proposal preview, validated save (`test_compose.py`).
- [x] Scenario E: CRM update — preview with old/new/impact, confirm-gated, idempotent retry (GA-04 + BFF confirm tests).

**Engineering criteria (§28.2):**

- [x] 1. APISIX is the only AI gateway in the repo/runtime config; golden OpenAI + Anthropic contract suites pass (fixtures). **[DEPLOY]** live-gateway run.
- [x] 2. Native Anthropic traffic preserves content blocks and SSE events without conversion (GW-08/09 wire models).
- [x] 3. Provider credentials only in Vault: `$SECRET://` references, secret-scan in CI, no plaintext paths (GW-02, security.yml).
- [x] 4. Missing/revoked secret fails closed with sanitized typed error (byok tests, ADR-023).
- [x] 5. Tenant/environment/protocol/model bindings enforced before provider invocation (byok `resolve_for_route` tests).
- [ ] 6. Retry/fallback bounded and tested — **[OPEN: retry bounds config + GW-10 golden — next iteration]**; no platform-key fallback is enforced and tested.
- [x] 7. Mobile source TypeScript-only; strict compilation passes with no waivers (5 packages, `tsc --noEmit` clean). RN shell **[DEPLOY]**.
- [x] 8. API clients generated from OpenAPI (drift-checked); runtime Zod validation on all untrusted dynamic payloads (§23.4 tests).
- [x] 9. Navigation/dashboards/graph/conversation types are discriminated or branded (validation + mobile packages).
- [x] 10. Graph queries compiled from typed IR, provenance-bearing; raw model-generated query text rejected by golden (GA-06).
- [ ] 11. Full release gate — security/streaming/tenant-isolation ✓ (goldens); performance + chaos **[DEPLOY]** load environment.

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

**Phase 4 status:** repo-side complete; stack runs end-to-end locally (see addendum). Remaining work in this repo is zero; everything else is the external residue already annotated per item in Phases 0–3.

### Phase 4 addendum — local end-to-end run (2026-09-26)

- [x] BFF composition root (`services/bff/bff/composition.py`): live wiring of orchestrator + metrics engines in-process (§13 split deferred to deploy), §19.3 serializer, `NORTHSTAR_BFF_MODE=live` default.
- [x] Dockerfiles for bff/metrics/byok (uv workspace-aware, frozen lockfile) + `uvicorn` as a declared dependency + metrics `/healthz`; python-based compose healthchecks (slim images ship no curl); local OTel collector config (prod config untouched).
- [x] **Stack verified running**: `docker compose up` → healthz green on all three services; metric lineage serving the governed catalog; a full conversation through `/api/v1/conversations/{id}/messages` returning the §19.3 wire shape with real governed numbers (attainment 60% v3 from the certified engine); SSE event order `message_start → component → message_stop`; unauthenticated call returning the typed `UNAUTHENTICATED` envelope. 184 Python tests green.

### Phase 4 addendum 2 — Android app shell via Expo Go (2026-09-27)

- [x] `apps/mobile` is now a runnable Expo SDK 57 app (React Native 0.86.3, TypeScript ~6.0.3, React Navigation native-stack, pnpm hoisted layout via `.npmrc`): entry + `app.json` (northstar:// scheme, dev-only cleartext for LAN), Home screen (backend health + editable API base) and Conversation/Ask screen (question → §19.3 answer with KPI rows, evidence, warnings). Transport confined to `src/transport.ts` (the only fetch site, §17.3); responses Zod-validated at the boundary (ADR-026); errors mapped through `USER_FACING_MESSAGES` (§17.8). **Android bundle verified headlessly: `expo export --platform android` — 838 modules.** Test on a phone: install Expo Go (Play Store), same Wi-Fi, `pnpm --filter @northstar/mobile start`, scan the QR. Bare-RN production build (JDK + Android Studio + adb) migrates from this shell per §17.1.

---

## Next build iteration — verified 2026-09-27 audit

Full-marker audit against repository state (this date). Everything repo-side that could be ticked with evidence has been; the lists below are what remains, consolidated from every `[OPEN]` tag and external annotation above.

### Repo-side gaps to finish next build iteration

1. **ESLint prohibited-pattern rule pack** (§17.3) — no ESLint config exists yet; CI currently enforces `tsc --noEmit` only.
2. **Spectral ruleset** for the OpenAPI lint step (§17.4 step 2) — pipeline generates + drift-checks, does not lint.
3. **kind + Tilt configs** — the last unpinned piece of the §17.9 toolchain row.
4. **In-code OTel SDK instrumentation** — collectors/rules are configured; services do not yet emit spans/metrics.
5. **APISIX route config controller** (§16.3–§16.4) — validate/policy-check/stage/promote service; today the checks live inside `byok.activate`.
6. **BYOK `test` + `bindings` endpoint surface** (§16.5) — lifecycle methods exist; two API routes missing.
7. **Opportunity Agent deal-brief composition** (§9.1) — inputs exist (engine + exceptions), the brief itself is unbuilt.
8. **Briefings** — daily seller briefing composition (§7.1).
9. **`ai-proxy-multi` resilience policy config + GW-10 retry-bound golden** (§15.4; criterion 6).
10. **GW-04..07 goldens as live-route tests** — currently config-level + fixture-based.
11. **`apps/admin` typed portal** (React Hook Form + Zod) — still a README stub.
12. **Expand eval corpus** — persona-scoped sets beyond the current 6-case dataset (§23).

### External gates (human/enterprise — cannot be built from this repo)

- Architecture review board: ADR-021–036 acceptance (`docs/governance/adr-review-package.md`).
- DPO + AI governance forum: DPIA and AI-risk approval; ADR-032 voice enablement.
- Enterprise inputs: landscape questionnaire answers, pilot teams, metric-owner certification, target-plan source surface (Q1.2), Dynamics sandbox, Teams Graph consent, Intune fleet, licensed news sources.
- Operational drills: DR rehearsal, load/chaos/canary on real infrastructure, UAT with pilots, external WCAG review.

---

## Change log

- **2026-09-27:** Android app shell: Expo SDK 57 wired into `apps/mobile` (RN 0.86.3, TS ~6.0.3, React Navigation), Home + Ask screens against the local stack, fetch confined to the transport module, Zod boundary at the response edge; Metro import fixes (extensionless relative imports in mobile/contracts/validation); Android bundle export verified (838 modules). 188 Python tests + 10 turbo tasks green.
- **2026-09-27:** Full todo.md marker audit: Phase 1 sprints/scenarios/criteria re-tickd against verified evidence (188 tests after adding Scenario D composer tests); Bootstrap toolchain/validation/security items ticked with annotations; genuinely open items re-marked with reasons; "Next build iteration" section consolidates all remaining repo-side gaps (12 items) and external gates.
- **2026-09-27:** README updated to system snapshot v1.0 (2026-09-27): as-built system diagram and data-flow diagram (Mermaid), build-state key, status line and ADR range refreshed to Phases 0–4.
- **2026-09-26:** Made the stack run end-to-end locally: BFF↔orchestrator↔metrics composition root, three service Dockerfiles with entrypoints, compose fixes (build contexts, curl-free healthchecks, local otel config), and a live smoke (healthz, lineage, §19.3 conversation with governed metrics, SSE order, typed 401). 184 tests green.
- **2026-09-26:** Built Phase 4 (production readiness & closure): `packages/validation` (ADR-026, previously missing), `apps/mobile` typed domain layer, docker-compose dev stack, k8s base manifests + Vault policies + Argo CD app, release workflow with SBOMs, and manifest-validation goldens. 181 Python tests, 10 TS tasks green, lint/ADR review clean.

- **2026-09-26:** Built Phase 3 repo-side engines: experimentation (powered uplift gate), territory/whitespace analytics, consent-gated transcript intelligence, account planning + partner compliance, playbook catalog + selection, federated retrieval with per-source policy, progressive-autonomy governor (§33 L0–L3 with kill-switch), and ADR-review automation + quarterly checklist. 173 Python tests green (+37), ruff clean, ADR inventory verified.
- **2026-09-26:** Closed the remaining Phase 2 repo-side items: manager workflows (exceptions/coaching/reassignment), news-source adapters with rights enforcement + SimHash dedup, entity resolution, device-posture/MDM gate, `packages/a11y` WCAG 2.2 automated gates, and the ADR-032 voice transcript-confirmation contract (disabled pending board approval). 136 Python + 16 TS tests green, lint clean.
- **2026-09-26:** Built Phase 2 (repo-side): Dynamics 365 connector, zh-Hant i18n package, Teams alert channel, SLO/alerting/otel configs, DR runbook + backup CronJobs, cost budgets + semantic cache, retention engine, action approvals, forecast calibration gate, CI-integrated eval gates; CI + security workflows; runbooks (DR full + nine §29). 111 Python tests + 10 TS tests green, lint clean, contract drift zero. Carried over from the Phase 1 build session in the same repo: pinned toolchain (mise/pnpm+turbo/uv), six Python services with tests, generated OpenAPI contracts, executable golden suites (GPM/GW/GA), APISIX routes. Deployment/UAT/mobile-app items remain flagged in Phases 1–2.
- **2026-09-26:** Built Phase 0 artifacts: discovery instruments (questionnaire, pilot plan, connector plan, UX blueprint, Phase 1 plan validation), canonical schema v0.1, metric catalog v0.1, threat model, DPIA + AI risk assessment, acceptance-suite spec, and ADR-028–036 closing all nine open decisions; PRD amended to v3.2 (F-01 `/api/v1`, F-03 voice deferral).
- **2026-09-26:** Replaced OpenCode recommendation with governed ZCode toolchain; added ADR-027, root instructions, toolchain guide, reviewed plugin, and PRD §17.9/§23.5 controls.

| Date | Change |
|---|---|
| 2026-09-26 | Bootstrap complete: PRD review, directory scaffold, ADR-021–027 (Proposed), this build log. |
