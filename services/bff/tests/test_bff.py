import json
from pathlib import Path

from bff.api import app
from fastapi.testclient import TestClient

OPENAPI_SPEC = Path(__file__).resolve().parents[1] / "openapi" / "openapi.json"

client = TestClient(app, raise_server_exceptions=False)
AUTH = {"Authorization": "Bearer u_s1"}


def test_error_envelope_is_typed_401():
    resp = client.post("/api/v1/conversations")
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "UNAUTHENTICATED"
    assert {"code", "message", "correlationId", "retryable"} <= set(body)


def test_conversation_creation_and_message_unauthorized():
    resp = client.post("/api/v1/conversations", headers=AUTH)
    assert resp.status_code == 201
    conv_id = resp.json()["conversationId"]
    resp2 = client.post(f"/api/v1/conversations/{conv_id}/messages", json={"text": "hi"})
    assert resp2.status_code == 401  # permission checked per request


def test_sse_stream_has_start_component_stop_order():
    """GW-03/GW-08 semantics at the BFF layer: event order through message_stop."""

    class Stub:
        async def converse(self, user, text):
            return {"components": [{"type": "narrative", "payload": {"text": "ok"}}],
                    "evidence": [], "warnings": [], "suggestedActions": [],
                    "answer": "ok", "scope": {"type": "seller", "id": user, "asOf": "2026-09-26T00:00:00Z"},
                    "messageId": "m1"}

    import bff.api as api

    api._dep = Stub()
    resp = client.post("/api/v1/conversations/c1/messages", json={"text": "hi"},
                       headers={**AUTH, "Accept": "text/event-stream"})
    assert resp.status_code == 200
    events = [line.removeprefix("event: ") for line in resp.text.splitlines() if line.startswith("event: ")]
    assert events == ["message_start", "component", "message_stop"]  # terminator last


def test_committed_spec_paths_match_app_routes():
    """§17.4 drift check (service level): every spec path+method exists on the FastAPI app."""
    spec = json.loads(OPENAPI_SPEC.read_text())
    app_routes = {(route.path, method.lower()) for route in app.routes
                  for method in getattr(route, "methods", set())}
    missing = []
    for path, ops in spec["paths"].items():
        fastapi_path = path.replace("{conversationId}", "{conversation_id}") \
                           .replace("{metricId}", "{metric_id}").replace("{actionId}", "{action_id}")
        for method in ops:
            if (fastapi_path, method.lower()) not in app_routes:
                missing.append(f"{method} {path}")
    assert not missing, f"spec/app drift: {missing}"
