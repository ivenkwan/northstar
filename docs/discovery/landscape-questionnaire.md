# Landscape questionnaire — Phase 0 discovery

Instrument to confirm the CRM, target-planning, activity, news, identity, mobile-device, and deployment landscape (PRD §24.1). Answer inline; every "No" in the gating questions is an escalation to the architecture review board. Assumptions A-1–A-7 in the [discovery README](README.md) are the provisional answers.

## Q1 — Systems of record

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 1.1 | Which CRM(s) are live? (Salesforce edition/API tier, Dynamics 365 deployment) | | A-1; connector order (Track C) |
| 1.2 | Target/planning system(s) and export surface (API, scheduled file, manual) | | TargetPlan ingestion; freshness (§14.3) |
| 1.3 | Activity sources beyond CRM (Exchange/Graph, Teams, telephony) and consent status | | §8.2 activity analytics; DPIA scope |
| 1.4 | Current BI/reporting estate this must interoperate with (not replace) | | §2 augmentation posture |

## Q2 — Data scale and quality

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 2.1 | Counts: active sellers, teams, domains, groups, accounts, open opportunities | | §22 scale design; seed data sizing |
| 2.2 | Known data-quality issues (stage hygiene, stale close dates, missing next steps) | | §31 risk; quality scorecard baseline |
| 2.3 | Existing duplicate-account / MDM handling | | Entity resolution design (§8.4) |

## Q3 — Fiscal calendar, currencies, allocation

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 3.1 | Fiscal year start, period structure, any 4-4-5 patterns | A-2 provisional: calendar year | Metric grain (§8.3); catalog `fiscal_calendar` |
| 3.2 | Reporting currency; any multi-currency deals and FX policy/source | A-3 provisional: HKD only | Currency treatment; F-08 FX reference |
| 3.3 | Domains that belong to >1 group today, and the intended `aggregation_policy` per membership | | §6.2 double-counting goldens |
| 3.4 | Salesperson transfers in the last 12 months (count) — effective-dating stress cases | | §6.1 history correctness |

## Q4 — Certified metrics baseline

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 4.1 | Approved definitions today for: bookings/actual, commit, best case, pipeline categories | | Metric catalog certification (§14.2) |
| 4.2 | Probability source: CRM field, stage mapping table, or overridden model | | Weighted pipeline formula (§8.3) |
| 4.3 | Who owns metric definitions and signs certification? | | Governance forum (§26) |

## Q5 — Connector feasibility (gating for ADR-031)

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 5.1 | Salesforce API edition + CDC/Pub/Sub enabled? Sandbox tenant available? | A-4 | Track C Sprint 2 start |
| 5.2 | Dynamics 365: change tracking enabled, OData API access, sandbox? | | Second connector timing |
| 5.3 | Volume estimate of daily change events per source | | Connector sizing; §14.3 targets |
| 5.4 | Any middleware/iPaaS mandated by enterprise architecture? | | ADR-031 alternative pressure |

## Q6 — Identity and access

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 6.1 | OIDC provider (Entra ID/Okta/other), MFA availability, group→role claim design | A-5 | §11.1 RBAC binding; gateway OIDC |
| 6.2 | HR source of truth for org hierarchy (manager relationships, effective dates) | | §6 org model sync |
| 6.3 | Existing delegation/temporary-coverage patterns to honor | | ReBAC rules (§11.1) |

## Q7 — Notifications and devices

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 7.1 | Enterprise SMTP relay available for application send? | A-6 | ADR-034 |
| 7.2 | MDM in use (Intune/etc.), managed vs BYOD distribution, app-store or internal channel | | §10.2 device posture; ABAC |
| 7.3 | Apple developer + FCM project provisioning ownership and lead time | | ADR-034; Sprint 1 dependency |

## Q8 — Deployment and network

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 8.1 | Target platform: private cloud (which), VM/bare-metal availability, failure zones | A-7 | ADR-035 topology |
| 8.2 | Approved LLM provider egress path (direct, proxy, private endpoint) and domains allowlist process | | §15.1 NetworkPolicy; BYOK probe |
| 8.3 | Data residency constraints for: CRM replicas, news content, model telemetry, backups | | §11.3 DPIA; ADR-033 |
| 8.4 | Existing Vault/KMS, or new deployment? Backup/DR expectations beyond §22 | | ADR-023 operations |

## Q9 — News and market-intelligence sources

| # | Question | Answer | Why it matters |
|---|---|---|---|
| 9.1 | Licensed news providers today (contracts, API availability, license scope for AI summarization) | | §8.4 ingestion; §31 licensing risk |
| 9.2 | Internal research sources to include | | KG bundle scope |
| 9.3 | Restricted sources/geographies that must be denied | | §8.4 controls |

## Completion rule

Phase 0 discovery is complete when every gating question (5.1, 6.1, 7.1, 8.1, 8.2) has an answer, the assumptions register has no invalidated entry, and the questionnaire answers are transcribed into the canonical model, metric catalog, and connector plan as updates.
