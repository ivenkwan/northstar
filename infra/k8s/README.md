# infra/k8s — Kubernetes deployment manifests

Cluster topology and workload manifests for the platform (PRD §15.1): APISIX data/control planes, BFF, orchestrator, metrics, knowledge-graph, BYOK service, Temporal, and storage dependencies.

## Planned contents

- Gateway API / APISIX declarative configuration, GitOps-managed; production changes require review and policy checks.
- NetworkPolicy restricting LLM egress to approved provider FQDNs or enterprise egress proxies.
- Workload identity for service-to-gateway authentication (mTLS/JWT, PRD §15.3 step 2).
- Failure-zone spread, resource quotas, and pod security standards.

## Open decisions

Kubernetes distribution, environment topology, and IaC platform — see Phase 0 list in `todo.md` (review F-07).

## Build track

Phase 1, Track A Sprint 1 — see `todo.md`.
