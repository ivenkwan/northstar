import pytest
from bff.api import VoiceSettings, app
from fastapi.testclient import TestClient

AUTH = {"Authorization": "Bearer test_seller_101"}


def test_metric_lineage_endpoint():
    client = TestClient(app, raise_server_exceptions=False)

    # Valid metric
    resp = client.get("/api/v1/metrics/attainment_pct/lineage", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["metricId"] == "attainment_pct"
    assert "version" in data
    assert "formula" in data

    # Invalid metric -> 404
    resp_404 = client.get("/api/v1/metrics/non_existent_metric/lineage", headers=AUTH)
    assert resp_404.status_code == 404
    assert resp_404.json()["code"] == "VALIDATION_FAILED"


def test_dashboard_save_validation_rules():
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Reject uncertified metric
    bad_metric = {
        "title": "Bad Metric Dash",
        "scope": {"type": "seller", "id": "current"},
        "layout": {"mode": "mobile_grid", "columns": 2},
        "cards": [
            {
                "kind": "kpi",
                "id": "c1",
                "title": "Invented Metric",
                "metric": "invented_unapproved_metric",
            }
        ],
    }
    r1 = client.post("/api/v1/dashboards", json=bad_metric, headers=AUTH)
    assert r1.status_code == 422
    assert "not certified" in r1.json()["message"]

    # 2. Reject disallowed dimension
    bad_dim = {
        "title": "Bad Dim Dash",
        "scope": {"type": "seller", "id": "current"},
        "layout": {"mode": "mobile_grid", "columns": 2},
        "cards": [
            {
                "kind": "bar",
                "id": "c1",
                "title": "By Secret Field",
                "metric": "weighted_pipeline",
                "dimension": "secret_field",
            }
        ],
    }
    r2 = client.post("/api/v1/dashboards", json=bad_dim, headers=AUTH)
    assert r2.status_code == 422
    assert "dimension" in r2.json()["message"]

    # 3. Reject invalid layout mode / columns
    bad_layout = {
        "title": "Bad Layout Dash",
        "scope": {"type": "seller", "id": "current"},
        "layout": {"mode": "desktop_flex", "columns": 10},
        "cards": [
            {
                "kind": "kpi",
                "id": "c1",
                "title": "Attainment",
                "metric": "attainment_pct",
            }
        ],
    }
    r3 = client.post("/api/v1/dashboards", json=bad_layout, headers=AUTH)
    assert r3.status_code == 422
    assert "layout must be mobile_grid" in r3.json()["message"]

    # 4. Valid dashboard creation -> 201
    valid_dash = {
        "title": "Valid Dash",
        "scope": {"type": "seller", "id": "current"},
        "layout": {"mode": "mobile_grid", "columns": 2},
        "cards": [
            {
                "kind": "kpi",
                "id": "c1",
                "title": "Attainment",
                "metric": "attainment_pct",
            },
            {
                "kind": "bar",
                "id": "c2",
                "title": "Pipeline by Stage",
                "metric": "weighted_pipeline",
                "dimension": "stage",
            },
        ],
    }
    r4 = client.post("/api/v1/dashboards", json=valid_dash, headers=AUTH)
    assert r4.status_code == 201
    assert "dashboardId" in r4.json()


def test_alert_creation_validation_rules():
    client = TestClient(app, raise_server_exceptions=False)

    # 1. Uncertified metric rejected
    bad_metric_alert = {
        "metricId": "unapproved_metric",
        "predicate": {"op": "gt", "value": 100},
        "channel": "in_app",
    }
    r1 = client.post("/api/v1/alerts", json=bad_metric_alert, headers=AUTH)
    assert r1.status_code == 422

    # 2. Invalid channel rejected
    bad_channel_alert = {
        "metricId": "attainment_pct",
        "predicate": {"op": "lt", "value": 0.5},
        "channel": "unsupported_channel",
    }
    r2 = client.post("/api/v1/alerts", json=bad_channel_alert, headers=AUTH)
    assert r2.status_code == 422

    # 3. Valid alert creation -> 201
    valid_alert = {
        "metricId": "attainment_pct",
        "predicate": {"op": "lt", "value": 0.8},
        "channel": "push",
    }
    r3 = client.post("/api/v1/alerts", json=valid_alert, headers=AUTH)
    assert r3.status_code == 201
    assert "ruleId" in r3.json()


def test_voice_transcript_feature_flag():
    client = TestClient(app, raise_server_exceptions=False)

    # Default: disabled -> 403 per ADR-032
    VoiceSettings.enabled = False
    r_disabled = client.post(
        "/api/v1/conversations/conv_1/voice-transcript",
        json={"audioRef": "ref_audio_123"},
        headers=AUTH,
    )
    assert r_disabled.status_code == 403
    assert "ADR-032" in r_disabled.json()["message"]

    # When enabled -> 200 preview, confirmed=False
    try:
        VoiceSettings.enabled = True
        r_enabled = client.post(
            "/api/v1/conversations/conv_1/voice-transcript",
            json={"audioRef": "ref_audio_123"},
            headers=AUTH,
        )
        assert r_enabled.status_code == 200
        data = r_enabled.json()
        assert data["confirmed"] is False
        assert "ref_audio_123" in data["transcript"]
    finally:
        VoiceSettings.enabled = False


def test_feedback_endpoint():
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        "/api/v1/feedback",
        json={
            "messageId": "msg_999",
            "rating": "positive",
            "correction": "Looks accurate",
        },
    )
    assert resp.status_code == 202
    assert resp.json() == {"status": "recorded", "messageId": "msg_999"}


def test_unauthenticated_request_envelope():
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/api/v1/conversations")
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "UNAUTHENTICATED"
    assert "missing bearer token" in body["message"]
