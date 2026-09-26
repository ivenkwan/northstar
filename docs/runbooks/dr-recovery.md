# Runbook: Disaster recovery (RPO 5 min / RTO 1 h)

Objective (§22 hardening): recover critical services within 1 hour with at most 5 minutes of committed data loss. Rehearsed quarterly; drill results appended below.

## Critical services (recovery order)

1. PostgreSQL (operational + AGE + pgvector) — everything else depends on it.
2. Vault — BYOK secret resolution (gateway AI routes are down without it).
3. etcd + APISIX control/data plane — north–south traffic.
4. BFF + orchestrator + metrics + alerts.
5. Temporal (actions resume; not user-facing-blocking).

## Detection

- `postgres-wal-archive-check` CronJob failure (RPO breach) → page platform on-call.
- Vault: `AICredentialResolutionFailure` alert (§ prometheus-rules) or probe failures.
- Zone/cluster loss: node NotReady across a failure zone.

## Procedure

1. **Declare incident** (severity-1 if RTO clock is at risk) and start the RTO clock.
2. **PostgreSQL**: promote standby (`pg_ctl promote` on replica) or rebuild from base backup + WAL replay to target recovery point: `recovery_target_time = '<incident_time> - interval '5 minutes'`. Verify with reconciliation report for the last landed day (`data/quality` suite).
3. **Vault**: restore latest raft snapshot — `vault operator raft snapshot restore /backups/vault-<stamp>.snap`; unseal with quorum of keys per key ceremony; verify `vault status` and run the synthetic credential probe for every ACTIVE binding (ADR-023).
4. **etcd/APISIX**: if etcd quorum lost, restore `etcdctl snapshot restore` on a fresh 3-member cluster, restart APISIX data plane, verify route table matches Git (`infra/apisix/routes.yaml` is the source of truth — a full GitOps re-apply is the deterministic path).
5. **Workloads**: Argo CD sync from Git (`argocd app sync northstar --prune`); nothing is hand-patched.
6. **Verify**: healthz on all services; golden smoke (`uv run pytest tests/golden -k smoke`); pilot-user check; reconciliation within tolerance.
7. **Stand down**: close RTO clock, post-incident review within 48h, append drill/incident record below.

## RPO/RTO instrumentation

- WAL lag metric (`northstar_wal_archive_lag_seconds`) alert at >240s.
- RTO drill timestamp template: declare → postgres → vault → gateway → apps → verify.

## Rehearsal log

| Date | RTO achieved | RPO verified | Issues found | Operator |
|---|---|---|---|---|
| _(quarterly drill)_ | | | | |
