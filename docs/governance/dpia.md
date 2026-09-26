# Data Protection Impact Assessment (DPIA) — Phase 0 draft

Aligned to the PDPO and the PCPD Model Personal Data Protection Framework (PRD §11.3, footnotes 12–14). Status: draft for Data Protection Officer review. **[INPUT REQUIRED]** before Phase 1 Sprint 4 (first personal-data ingestion beyond org sync).

## 1. Activity and purpose

Sales Northstar processes employee and customer personal data to provide sales intelligence: pipeline analytics, target attainment, activity metadata, and market intelligence. Purpose is limited to the employer's business management of sales operations; the product does not perform automated decisions about individuals (§4.3 exclusions).

## 2. Personal data inventory

| Data class | Data subjects | Fields | Source | Lawful basis / necessity |
|---|---|---|---|---|
| Identity & org | Employees | user id, name, role, team/domain/group membership, manager | IdP/HR (C4) | Employment purposes; effective-dated |
| Sales performance | Employees | owned opportunities, attainment vs target, forecast submissions | CRM/planning | Business management; team-level reporting default |
| Activity metadata | Employees, customers | type, timestamp, related record, outcome; **no content** | CRM/Exchange metadata (C5) | Purpose-limited; content excluded without separate consent |
| Customer contacts | Customers (business) | name, title, email, phone, account link | CRM | Legitimate business purposes; no marketing use |
| Conversation logs | Employees | questions, answers, components returned | Product | Service delivery + audit; retention §6 |
| Device telemetry | Employees | app version, crash, engagement | Product | Service improvement; no location tracking |
| Evaluation datasets | Employees/customers | sampled prompts/records | Product | **Anonymized/pseudonymized** before use (§11.3) |

## 3. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation (PRD) |
|---|---|---|---|
| Function creep into employee surveillance | Medium | High | No hidden behavioral memory (§9.3); no trait inference; team-level pilot analytics; transparency notices; audit of all queries (§11.4) |
| Cross-scope access to peer/customer data | Medium | High | RBAC+ABAC+ReBAC + denied inference (§11.1); leakage goldens gate release (§23.1) |
| Over-collection of activity content | Medium | Medium | Metadata-only C5 design; content ingestion requires separate DPIA addendum |
| Data leakage via model providers | Low-Med | High | BYOK in-tenant credentials (ADR-023); retrieval grounding; payload logging off (§21); provider DPA required |
| Prompt-injection exfiltration | Medium | High | T-06/T-10 controls; red team gate (§23.1) |
| Excessive retention | Medium | Medium | Retention schedule §6 below; news expiry per signal; deletion propagation golden (§23.2) |
| Lost device cache exposure | Low | Medium | Encrypted, time-limited, approved-only cache; remote wipe (§10.2) |

## 4. Data minimization and location

- Tokenization of direct identifiers in the analytical store where analytics do not require identity (pseudonymized analytical marts; identity join kept in the operational store under stricter access).
- All data at rest in the deployment region (questionnaire Q8.3); model egress carries prompts but is governed by provider DPAs and the §15.1 egress allowlist; no Asian data replicated outside the tenant boundary.
- Evaluation datasets anonymized per PCPD guidance before entering `tests/evals`.

## 5. Transparency and data-subject rights

- §11.3 notice to all pilot users: AI use description, data categories, human involvement, correction/appeal channel.
- Access/correction requests route to the source systems (CRM/IdP remain systems of record, §4.1); Northstar reflects corrections through re-sync within the freshness SLA; deletion propagates via connectors and is verified by the §23.2 golden.

## 6. Retention schedule (proposal for DPO)

| Data | Retention | Basis |
|---|---|---|
| Raw landing zone | 30 days | Replay/reconciliation window |
| Canonical + analytical | Life of deployment (org data effective-dated) | Continuity of history |
| Conversation logs + agent traces | 24 months, then aggregate-only | Audit/evaluation |
| News items/signals | Per license + signal expiry (§14.1) | Contractual |
| Device telemetry | 12 months aggregated | Product improvement |

## 7. Sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Data Protection Officer | | | |
| Product owner | | | |
| Security | | | |
