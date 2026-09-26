# Runbook: APISIX route rollback and etcd recovery

PRD §29 required runbook. Owner: platform on-call. Linked alerts: see infra/observability/prometheus-rules.yaml.

## Symptoms

- (fill from on-call experience; link the firing alert)

## Immediate actions

1. Check the relevant dashboard (SLO panel, infra/observability/slo.yaml).
2. Stabilize before diagnosing: prefer rollback (GitOps revert) over hotfix.
3. Record every action with timestamps in the incident channel — the audit trail is part of the runbook contract (§11.4).

## Escalation

- Platform lead → security (if credentials/data implicated) → product owner (user comms).

## Verification of recovery

- Golden smoke suite green, synthetic probes green, SLO burn rate back under budget.

## Post-incident

- Review within 48h; update this runbook and the threat model if a new failure mode appeared.
