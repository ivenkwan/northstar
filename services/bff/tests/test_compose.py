"""Scenario D (§28.1): conversational dashboard creation — certified metrics only,
preview before save, save validates server-side."""

from bff.api import app
from fastapi.testclient import TestClient

client = TestClient(app)
AUTH = {"Authorization": "Bearer u_dev"}


def test_compose_returns_proposal_not_saved():
    resp = client.post("/api/v1/dashboards/compose",
                       json={"intent": "monthly attainment and coverage by rep"}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("_proposal") is True            # proposal only — never auto-saved
    assert body["cards"][0]["metric"] == "attainment_pct"


def test_save_rejects_uncertified_metric():
    bad = {"title": "X", "scope": {"type": "seller", "id": "u"},
           "layout": {"mode": "mobile_grid", "columns": 2},
           "cards": [{"kind": "kpi", "id": "c1", "title": "vibes", "metric": "pipeline_vibes_score"}]}
    resp = client.post("/api/v1/dashboards", json=bad, headers=AUTH)
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_FAILED"


def test_save_rejects_disallowed_dimension_and_bad_layout():
    base = {"title": "X", "scope": {"type": "team", "id": "t1"}}
    dim = {**base, "layout": {"mode": "mobile_grid", "columns": 2},
           "cards": [{"kind": "bar", "id": "c", "title": "t", "metric": "coverage", "dimension": "vibes"}]}
    assert client.post("/api/v1/dashboards", json=dim, headers=AUTH).status_code == 422
    layout = {**base, "layout": {"mode": "hologram", "columns": 2},
              "cards": [{"kind": "kpi", "id": "c", "title": "t", "metric": "coverage"}]}
    assert client.post("/api/v1/dashboards", json=layout, headers=AUTH).status_code == 422


def test_save_accepts_certified_definition_and_assigns_id():
    good = {"title": "Monday Review", "scope": {"type": "team", "id": "team_12"},
            "layout": {"mode": "mobile_grid", "columns": 2},
            "cards": [
                {"kind": "kpi", "id": "c1", "title": "Attainment", "metric": "attainment_pct"},
                {"kind": "bar", "id": "c2", "title": "Coverage", "metric": "coverage", "dimension": "salesperson"},
            ]}
    resp = client.post("/api/v1/dashboards", json=good, headers=AUTH)
    assert resp.status_code == 201
    assert resp.json()["dashboardId"].startswith("dash_")
