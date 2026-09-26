# ADR-031: Ingestion uses native change-capture clients orchestrated by Temporal

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, data engineering, security |
| **PRD references** | §14, §14.3, §13 |
| **Resolves** | PRD review finding F-07 (CDC tooling unnamed) |

## Context

Connectors must ingest Salesforce, Microsoft Dynamics 365, target-planning systems, activity metadata, and licensed news into the raw landing zone with freshness targets of 5–15 minutes for CRM data (§14.3), inside an enterprise VPC with strict data-egress control. The PRD left the ingestion framework unnamed (F-07).

## Decision

`services/connectors` implements **native change-capture clients** rather than deploying a third-party integration platform:

- **Salesforce:** Platform Events / Change Data Capture via the Pub/Sub API (gRPC subscription), replay-from-offset for reliability.
- **Dynamics 365:** Change Tracking tokens via the Web API (delta queries).
- **Target planning / activity systems:** scheduled API pulls with watermark cursors where no push CDC exists.
- **News:** licensed feed APIs and webhooks per source SLA.

Each connector is a **Temporal workflow** (§13 already adopts Temporal for actions): durable per-source cursors, bounded retries with backoff, poison-message quarantine, and exactly-once landing keyed by source event ID. Canonical transforms run in the same service after raw landing, so raw and canonical are independently replayable. Debezium is reserved for future database-source (JDBC CDC) integrations and is not part of MVP.

## Consequences

**Positive:** no third-party data egress or SaaS integration platform in the trust boundary; freshness is directly controllable to meet §14.3; reconciliation and replay are first-class (Temporal history + raw landing); connector code lives in the same governed repo and review process.

**Negative / accepted costs:** we own the connector code for two CRM APIs (the largest share of Track C effort); Salesforce Pub/Sub and Dynamics change-tracking semantics must be tested against sandbox tenants in Phase 0 discovery (see connector plan).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Airbyte OSS | Broad connector catalog, but heavy self-hosted footprint and data flows through a generic platform whose upgrade/security posture we would own anyway; our sources are few. |
| Fivetran / managed ELT | SaaS egress of CRM data conflicts with the single-enterprise VPC posture (§4.1). |
| Debezium for everything | Debezium covers JDBC/Kafka sources, not Salesforce/Dynamics CDC protocols; would still require the native clients above. |

## Verification

- Connector plan discovery tasks validate CDC availability per source (sandbox tenants) before Sprint 2.
- Freshness telemetry per connector with SLA breach alerts (§14.3, §22); reconciliation totals per §27 "Sales data foundation" exit criterion.
- Replay test: reprocessing a raw-landing window produces identical canonical output (idempotency).
