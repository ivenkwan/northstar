"""End-to-end composition test: BFF → orchestrator → metrics, all real objects."""

from bff.api import app
from fastapi.testclient import TestClient

client = TestClient(app)
AUTH = {"Authorization": "Bearer u_dev"}


def _post_message():
    conv = client.post("/api/v1/conversations", headers=AUTH).json()
    return client.post(f"/api/v1/conversations/{conv['conversationId']}/messages",
                       json={"text": "What is my attainment this quarter?"}, headers=AUTH)


def test_live_pipeline_answers_in_19_3_shape():
    resp = _post_message()
    assert resp.status_code == 200
    body = resp.json()
    # §19.3 wire contract
    assert {"messageId", "answer", "scope", "components", "evidence", "warnings", "suggestedActions"} <= set(body)
    assert body["scope"]["id"] == "u_dev"
    assert body["components"] and body["components"][0]["type"] == "narrative"
    assert any(w.startswith("data_as_of:") for w in body["warnings"])  # freshness always visible (§14.3)


def test_live_pipeline_carries_governed_metrics_with_versions():
    body = _post_message().json()
    kpi = next(c for c in body["components"] if c["type"] == "kpi_table")
    rows = {r["metric_id"]: r for r in kpi["payload"]["rows"]}
    assert rows["attainment_pct"]["value"] == 60.0       # dev Scenario-A data flows through the real engine
    assert rows["attainment_pct"]["version"] >= 3
    evidence_ids = [e["ref"] for e in body["evidence"]]
    assert "attainment_pct" in evidence_ids              # cited metric definitions (CONV-05)


def test_payload_validates_against_typescript_contract_shape():
    """The §19.3 shape is what packages/validation consumes on mobile (ADR-026)."""
    body = _post_message().json()
    allowed = {"narrative", "kpi", "kpi_table", "chart", "table", "evidence_chips"}
    assert all(c["type"] in allowed for c in body["components"])
