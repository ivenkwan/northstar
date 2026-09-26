"""Manifest goldens: the deployment layer is CI-checked like code.

Enforces the PRD's operational invariants on every manifest change:
pinned images, resource requests+limits, probes, hardened securityContext,
and healthchecks in the compose stack.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
K8S_DIR = REPO / "infra" / "k8s"


def k8s_docs() -> list[dict]:
    docs: list[dict] = []
    for f in K8S_DIR.rglob("*.yaml"):
        docs.extend(d for d in yaml.safe_load_all(f.read_text()) if d is not None)
    return docs


def workloads() -> list[tuple[str, dict]]:
    out = []
    for d in k8s_docs():
        if d.get("kind") == "Deployment":
            out.append((f"{d['metadata']['name']}", d))
    return out


def test_images_are_pinned_no_latest():
    for name, d in workloads():
        for c in d["spec"]["template"]["spec"]["containers"]:
            image = str(c["image"])
            assert ":" in image, f"{name}/{c['name']}: image has no tag: {image}"
            assert not image.endswith(":latest"), f"{name}/{c['name']}: :latest forbidden"


def test_every_container_has_resources_requests_and_limits():
    for name, d in workloads():
        for c in d["spec"]["template"]["spec"]["containers"]:
            res = c.get("resources", {})
            assert "requests" in res and "limits" in res, f"{name}/{c['name']} missing resources"
            assert res["limits"]["memory"] != "0", f"{name}/{c['name']} zero memory limit"


def test_every_container_has_liveness_and_readiness_probes():
    for name, d in workloads():
        for c in d["spec"]["template"]["spec"]["containers"]:
            assert "livenessProbe" in c, f"{name}/{c['name']} missing livenessProbe"
            assert "readinessProbe" in c, f"{name}/{c['name']} missing readinessProbe"


def test_security_context_hardened():
    for name, d in workloads():
        for c in d["spec"]["template"]["spec"]["containers"]:
            sc = c.get("securityContext", {})
            assert sc.get("runAsNonRoot") is True, f"{name}/{c['name']} must run as non-root"
            assert sc.get("allowPrivilegeEscalation") is False, f"{name}/{c['name']} privilege escalation"
            assert "ALL" in (sc.get("capabilities", {}).get("drop", [])), f"{name}/{c['name']} caps not dropped"


def test_gateway_has_three_replicas():
    apisix = next(d for _, d in workloads() if "apisix" in _)
    assert apisix["spec"]["replicas"] >= 3  # §15.1: ≥3 data-plane replicas


def test_llm_egress_networkpolicy_exists_and_restricted():
    policies = [d for d in k8s_docs() if d.get("kind") == "NetworkPolicy"]
    llm = next(p for p in policies if p["metadata"]["name"] == "llm-egress-allowlist")
    assert llm["spec"]["policyTypes"] == ["Egress"]
    assert llm["spec"]["egress"], "egress allowlist must not be empty"


def test_argocd_app_is_gitops_locked():
    app = yaml.safe_load((REPO / "infra" / "argocd" / "northstar-app.yaml").read_text())
    sync = app["spec"]["syncPolicy"]
    assert sync["automated"] == {"prune": True, "selfHeal": True}  # drift reverts to Git (ADR-035)


def test_compose_stack_services_have_healthchecks():
    compose = yaml.safe_load((REPO / "docker-compose.yml").read_text())
    for svc, cfg in compose["services"].items():
        assert "healthcheck" in cfg or svc == "otel-collector", f"compose {svc}: no healthcheck"
        if "image" in cfg:  # build-defined services pin their base image in their Dockerfile
            image = str(cfg["image"])
            assert ":" in image and not image.endswith(":latest"), f"compose {svc}: unpinned image"
