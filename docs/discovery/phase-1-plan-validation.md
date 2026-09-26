# Phase 1 plan validation — capacity, critical path, de-scope order

Resolves review findings F-02 (sprint plan covered only gateway/mobile) and F-10 (scope vs window risk) by validating the all-track plan in `todo.md` against the 12–16 week window.

## Capacity model

Squad (PRD §26): 2 mobile, 2 backend/platform, 2 data/analytics, 1 ML/LLM, 1 QA/AI-eval, plus shared specialists (security, SRE, designer) at ~20%. Assuming ~9 focused weeks per engineer in a 12-week window (ceremonies, support, absence), total ≈ **90 engineer-weeks**; at 14 weeks ≈ 105.

## Track sizing (engineering-weeks, includes tests)

| Track | Scope | Estimate | Confidence |
|---|---|---|---|
| A Gateway/BYOK | APISIX topology, both native routes, SSE, BYOK lifecycle, resilience | 16 | High (PRD table) |
| B Mobile type safety | RN baseline, contracts/Zod, conversation stream, widgets, admin screens, hardening | 20 | High (PRD table) |
| C Data foundation + semantic layer | connectors C1–C4, canonical+dbt marts, metrics service, allocation logic | 18 | Medium (source-API risk) |
| D Agents + conversational analytics | orchestrator 12-step, Identity/Analytics/Opportunity/Target agents | 14 | Medium (eval-loop risk) |
| E Market intelligence | news ingestion, entity resolution, signals, KG service | 10 | Medium |
| F Dashboards/alerts/briefings | composer, saved views, alert rules, briefing | 8 | Medium |
| G Controlled actions | preview/confirm, Temporal, task creation | 5 | High |
| H Governance/audit/testing | policy engine wiring, goldens, red team, evals, runbooks | 12 | Medium |
| **Total** | | **103** | |

103 engineer-weeks vs 90–105 available: **the 12-week floor does not fit; 14 weeks fits with ~2 weeks' slack only if C and D hold their estimates.** The PRD's 10–14 week MVP is therefore realistic at the top of its range, and only with the de-scope levers armed.

## Critical path

Sprint 1 topology/identity → Sprint 2 contracts + C1 connector → Sprint 3 semantic layer + streaming → Sprint 4 agents over metrics + BYOK → Sprint 5 composer/actions → Sprint 6 hardening/gates. **C (data) and D (agents) serialize the analytics value chain; A/B are parallel-safe.** Any C slip in Sprints 2–3 cascades directly into D — this is where the buffer belongs.

## Watch items (weekly review)

1. Salesforce CDC sandbox access not granted by end of week 1 → escalate; ADR-031 fallback is scheduled-pull (freshness 15 min, still in §14.3 range).
2. Semantic-layer reconciliation >2 days of slack in Sprint 3 → pull the second data engineer from E.
3. Agent eval pass-rate <80% at end of Sprint 4 → trigger de-scope lever 4/5 below to protect quality gates.

## De-scope order (from review §5; armed in this priority)

1. Voice — already deferred by ADR-032.
2. Relationship-graph widget (keep list/table views).
3. Scheduled briefings (keep threshold alerts + Today).
4. Scenario controls (keep core attainment/coverage).
5. Controlled write-back actions (read-only intelligence ships without G; task-creation is the only G item before this lever).
6. Second CRM connector — already Phase 2 (A-1).

**Never de-scoped:** identity/hierarchy, semantic layer, policy enforcement, audit, evidence/citations (retrofit cost is the largest failure mode).

## Decision requested from governance

- [ ] Accept the 14-week Phase 1 plan (Sprints 1–7 effective, or extend Sprint 6 to 4 weeks) with the de-scope order above.
- [ ] Pre-authorize levers 1–4 for the product owner without further board review (levers 5–6 need board sign-off).
