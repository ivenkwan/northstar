# ADR-035: Terraform IaC; RKE2 production Kubernetes; kind for local; Argo CD GitOps

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, DevOps/SRE, security |
| **PRD references** | §15.1, §17.9 |
| **Resolves** | PRD review open decision: IaC platform and K8s distribution |

## Context

The PRD mandates Kubernetes deployment with GitOps, ≥3 APISIX data-plane replicas across failure zones, private etcd, and declarative configuration in Git (§15.1); §17.9 already fixes kind+Tilt locally and Argo CD (or approved GitOps controller) for deployment. Unresolved: the IaC tool and the production Kubernetes distribution for a single-enterprise private cloud (no managed cloud control plane assumed).

## Decision

- **IaC: Terraform** (HCL, version-pinned, state in a locked backend with encryption and change audit). All infrastructure — clusters, Vault, databases, network, DNS, load balancers — is Terraform-managed; no console-provisioned resources (drift detection in CI).
- **Production Kubernetes: RKE2** — CIS-benchmarked defaults, embedded containerd, HA control plane on-prem or in private cloud, no vendor lock-in; etcd bundled and hardened per §15.1 (private subnet, encryption, mTLS, backups, no client access).
- **Local development: kind** (already fixed by §17.9) with the same Gateway API/manifests promoted through environments.
- **GitOps: Argo CD** (per §17.9) — the only path to production changes; APISIX route/config revisions ship as reviewed Git changes (§15.1).

## Consequences

**Positive:** declarative, reviewable, reproducible infrastructure matching the PRD's GitOps posture; RKE2's hardening and air-gap support fit enterprise VPC constraints; one K8s skill set from laptop (kind) to production (RKE2).

**Negative / accepted costs:** we operate the control plane ourselves (etcd backup/restore drills are mandatory runbook §29 items); Terraform state security becomes critical infrastructure.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Managed K8s (EKS/AKS/GKE) | Deployment target is single-enterprise private cloud/VPC (§4.1); not universally available there. |
| kubeadm clusters | More assembly and hardening burden than RKE2 for the same result. |
| Pulumi | Viable; Terraform chosen for team familiarity and provider maturity — not a technical rejection. |
| OpenShift | Strong product, but license cost and platform opinions beyond our requirements. |

## Verification

- CI: `terraform plan` on PRs; drift detection nightly; RKE2 CIS profile conformance in the hardening checklist.
- Runbook drill: etcd backup/restore and full cluster rebuild from Git + Terraform state (§29).
