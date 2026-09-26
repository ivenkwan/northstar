# Connector plan — Phase 0

Per-source ingestion plan implementing ADR-031 (native change-capture clients on Temporal). Each connector: source → raw landing → canonical transform → analytical/read models (PRD §14). Freshness targets per §14.3.

## Connector inventory (MVP)

| # | Source | Change mechanism | Cadence → freshness | Canonical entities fed | Sprint |
|---|---|---|---|---|---|
| C1 | Salesforce — core objects (Account, Opportunity, Contact, Task/Event, User) | CDC via Pub/Sub API (Platform Events), replay by offset | Continuous | Account, Opportunity, OpportunityTeam, Activity, SalesPerson, User | 2 |
| C2 | Salesforce — custom/metadata (record types, stage mappings) | Metadata API poll | Daily | Stage/probability mappings (semantic-layer config) | 2 |
| C3 | Target planning system | API pull with watermark (mechanism per questionnaire Q1.2) | 15 min poll → ≤30 min | TargetPlan, ForecastSnapshot | 3 |
| C4 | Org hierarchy (HR/IdP) | Scheduled export or Graph delta | Hourly | Team, Domain, SalesGroup, DomainGroupMembership, SalesPerson assignments | 1 |
| C5 | Activity metadata (Exchange/Teams) | Graph API delta + consent filter | 30 min | Activity (metadata only; no content) | 4 (if consented; else Phase 2) |
| C6 | Licensed news feeds | Feed API/webhook per provider SLA | Per SLA | NewsItem | 4 |
| C7 | Microsoft Dynamics 365 | Change Tracking tokens (Web API delta) | Continuous | Same as C1 | Phase 2 (per A-1) |

## Common connector architecture (all sources)

1. **Auth:** per-source credentials in Vault (`byok/…` or `connectors/<source>/…` paths, ADR-023 pattern); least-privilege read scopes; no credentials in config or logs.
2. **Temporal workflow per source:** durable cursor (source offset/token/watermark), bounded retry with backoff, poison-message quarantine table, dead-letter review UI in admin portal (Phase 2).
3. **Raw landing:** append-only, partitioned by ingestion date; event ID = idempotency key (replay-safe); PII fields tokenized at landing where policy requires (DPIA §4).
4. **Canonical transform:** deterministic pure functions (dbt for analytical models; service code for operational projections); full reprocessing of any landing window must reproduce identical canonical output.
5. **Reconciliation:** per §27 — totals per object per day (counts, sums by currency) vs source reports; breach of tolerance blocks the release gate (§23.1).
6. **Freshness telemetry:** per connector last-event and landing timestamps vs target; SLA breach alerts (§22).

## Salesforce specifics (C1/C2) — validation in Phase 0 sandbox

- Confirm CDC events exist for all objects in scope (custom objects may need Platform Event enablement).
- Confirm Pub/Sub API gRPC access on the sandbox API tier; measure typical event volume (Q5.3).
- Map picklists → canonical enums (stage, forecast category); unmapped values quarantine with a data-quality warning, never silently defaulted.

## News specifics (C6)

- Rights metadata (license, permitted use, retention) stored on every NewsItem; sources without AI-summarization rights are excluded at ingestion (§8.4, §31 licensing risk).
- Deduplication: SimHash on normalized text + entity overlap → canonical cluster; first-published item is canonical source.
- Untrusted-content handling: raw text never reaches prompts unfiltered; summarization uses extraction + citation, and injection detection runs pre-indexing (§11.2; see threat model T-12).

## Open items

- [ ] **[INPUT REQUIRED]** Sandbox credentials and CDC availability per questionnaire Q5.
- [ ] Target planning system API surface unknown until Q1.2 — C3 design finalized in Phase 0 week 2.
- [ ] Activity consent posture (C5) decided by DPIA outcome.
