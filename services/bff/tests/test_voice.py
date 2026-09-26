from bff.api import VoiceSettings, app
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)
AUTH = {"Authorization": "Bearer u_s1"}


def test_voice_disabled_by_default_returns_typed_403():
    VoiceSettings.enabled = False
    resp = client.post("/api/v1/conversations/c1/voice-transcript",
                       json={"audioRef": "stt-ref-1"}, headers=AUTH)
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "FORBIDDEN"
    assert "ADR-032" in body["message"]


def test_voice_when_enabled_returns_unconfirmed_preview_only():
    VoiceSettings.enabled = True
    try:
        resp = client.post("/api/v1/conversations/c1/voice-transcript",
                           json={"audioRef": "stt-ref-1"}, headers=AUTH)
        assert resp.status_code == 200
        body = resp.json()
        assert body["confirmed"] is False          # never auto-submitted (§10.2)
        assert "Review" in body["notice"]
    finally:
        VoiceSettings.enabled = False              # fail-closed default restored


def test_voice_requires_auth():
    resp = client.post("/api/v1/conversations/c1/voice-transcript", json={"audioRef": "x"})
    assert resp.status_code == 401
