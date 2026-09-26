# Phase 0 — Discovery and control design artifacts

Deliverables for PRD §24.1, tracked in `todo.md` (Phase 0). Items marked **[INPUT REQUIRED]** cannot be completed from the repository alone — they need enterprise stakeholders; the artifact here is the instrument and the recorded assumptions.

| Artifact | File | PRD §24.1 item | Status |
|---|---|---|---|
| Landscape questionnaire | [landscape-questionnaire.md](landscape-questionnaire.md) | Confirm CRM, target, activity, news, identity, MDM, deployment landscape | Ready — **[INPUT REQUIRED]** answers |
| Pilot baseline plan | [pilot-baseline-plan.md](pilot-baseline-plan.md) | Select two pilot teams; define baseline measurements | Ready — **[INPUT REQUIRED]** team confirmation |
| Connector plan | [connector-plan.md](connector-plan.md) | Connector plan | Drafted (per ADR-031) — sandbox validation **[INPUT REQUIRED]** |
| UX IA blueprint | [ux-ia-blueprint.md](ux-ia-blueprint.md) | UX prototype | Wireframe-level blueprint — high-fidelity prototype needs designer |
| Canonical schema | [../../data/canonical-model/schema.sql](../../data/canonical-model/schema.sql) | Canonical schema | Draft v0.1 |
| Metric catalog | [../../data/semantic-layer/metric-catalog.yaml](../../data/semantic-layer/metric-catalog.yaml) | Certified metric definitions | Draft v0.1 — **[INPUT REQUIRED]** certification sign-off |
| Threat model | [../security/threat-model.md](../security/threat-model.md) | Threat model | Drafted |
| DPIA + AI risk assessment | [../governance/](../governance/README.md) | Data protection and AI risk assessments | Drafted — approval **[INPUT REQUIRED]** |
| Acceptance suite | [../../tests/golden/acceptance-suite.md](../../tests/golden/acceptance-suite.md) | Acceptance suite | Spec drafted; automation lands with Phase 1 code |
| Open decisions | [../adr/](../adr/README.md) ADR-028–036 | Hierarchy/allocation/store/tooling decisions | Proposed — review-board gate |
| Phase 1 plan validation | [phase-1-plan-validation.md](phase-1-plan-validation.md) | Sprint plan realism (review F-02/F-10) | Drafted |

## Assumptions register

Every assumption below is provisional until the questionnaire returns real answers; each is testable in Phase 0.

| # | Assumption | From | Invalidated by |
|---|---|---|---|
| A-1 | Salesforce is the primary CRM; Dynamics 365 second | PRD §4.1 | Questionnaire Q1 |
| A-2 | Fiscal year = calendar year, HKD reporting currency, monthly+quarterly periods | Assumed default | Questionnaire Q3 |
| A-3 | Single currency (HKD) at MVP; FX reference data still modeled | Review F-08 | Questionnaire Q3 |
| A-4 | Salesforce sandbox with CDC/Pub/Sub API access is available for connector development | ADR-031 | Questionnaire Q5 |
| A-5 | Enterprise OIDC provider exists (Entra ID or equivalent) with group claims | PRD §11.1 | Questionnaire Q6 |
| A-6 | Enterprise SMTP relay exists; FCM/APNs projects can be provisioned | ADR-034 | Questionnaire Q7 |
| A-7 | Private-cloud Kubernetes (RKE2 on 3+ nodes across failure zones) is provisionable | ADR-035 | Questionnaire Q8 |
