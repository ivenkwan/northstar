"""Briefing endpoints (§7.1 Today, §9.1 deal brief) — live composition, wire shape."""

from bff.api import app
from fastapi.testclient import TestClient

client = TestClient(app)
AUTH = {"Authorization": "Bearer u_dev"}


def test_today_briefing_returns_scenario_a_content():
    resp = client.get("/api/v1/briefings/today", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert {"asOf", "scopeId", "greeting", "kpis", "topRisks", "marketSignals",
            "overdueActions", "evidence"} <= set(body)
    kpis = {k["metricId"]: k for k in body["kpis"]}
    assert kpis["attainment_pct"]["value"] == 60.0
    risks = body["topRisks"]
    assert risks[0]["opportunityId"] == "opp_1"        # ranked: critical-stale deal first
    assert risks[0]["topSeverity"] == "critical"
    assert risks[0]["nextSteps"][0].startswith("Re-engage")
    assert len(body["marketSignals"]) == 2
    assert body["marketSignals"][0]["source"] == "licensed_wire"   # sourced signals (§8.4)
    assert body["overdueActions"] == 1


def test_deal_brief_endpoint_full_shape():
    resp = client.get("/api/v1/opportunities/opp_2/brief", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["opportunityId"] == "opp_2"
    assert body["indicators"] == []                      # healthy deal
    assert any(e["type"] == "crm_record" for e in body["evidence"])


def test_deal_brief_unknown_id_is_typed_404():
    resp = client.get("/api/v1/opportunities/nope/brief", headers=AUTH)
    assert resp.status_code == 404
    assert resp.json()["code"] == "VALIDATION_FAILED"


def test_briefing_endpoints_require_auth():
    assert client.get("/api/v1/briefings/today").status_code == 401
    assert client.get("/api/v1/opportunities/opp_1/brief").status_code == 401
