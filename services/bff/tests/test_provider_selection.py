"""Provider selection at the composition seam (FR-1; NFR-4/NFR-5).

Default stays `scripted` so the pre-existing suite is untouched; `deepseek` opts
in per-deployment; any other value fails closed with a typed ConfigError at
startup — never a silent fallback.
"""

import pytest
from bff.api import app
from bff.composition import LiveOrchestratorDep
from fastapi.testclient import TestClient
from orchestrator.errors import ConfigError
from orchestrator.pipeline import ScriptedProvider
from orchestrator.provider_deepseek import DeepSeekProvider

AUTH = {"Authorization": "Bearer u_dev"}


def test_t12_unset_provider_resolves_scripted_default(monkeypatch):
    monkeypatch.delenv("NORTHSTAR_PROVIDER", raising=False)
    dep = LiveOrchestratorDep()
    assert isinstance(dep._provider, ScriptedProvider)


def test_t12b_explicit_scripted_resolves_scripted_default(monkeypatch):
    monkeypatch.setenv("NORTHSTAR_PROVIDER", "scripted")
    dep = LiveOrchestratorDep()
    assert isinstance(dep._provider, ScriptedProvider)


def test_t13_deepseek_resolves_deepseek_provider(monkeypatch):
    monkeypatch.setenv("NORTHSTAR_PROVIDER", "deepseek")
    dep = LiveOrchestratorDep()
    assert isinstance(dep._provider, DeepSeekProvider)


@pytest.mark.parametrize("bad", ["DeepSeek", " deepseek", "deepseek ", "openai", "SCRIPTED", "", "anthropic"])
def test_t14_invalid_values_fail_closed_at_startup(monkeypatch, bad):
    monkeypatch.setenv("NORTHSTAR_PROVIDER", bad)
    with pytest.raises(ConfigError) as exc:
        LiveOrchestratorDep()
    assert exc.value.code.value == "CONFIG_INVALID"
    assert exc.value.retryable is False


def test_deepseek_without_credentials_fails_closed_at_call_time(monkeypatch):
    """ADR-023: no Vault env → sanitized AI_CREDENTIAL_UNAVAILABLE envelope, no fallback answer."""
    monkeypatch.setenv("NORTHSTAR_PROVIDER", "deepseek")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)

    import bff.api as api

    api._dep = api._UNSET  # force live composition for this test
    client = TestClient(app, raise_server_exceptions=False)
    conv = client.post("/api/v1/conversations", headers=AUTH).json()
    resp = client.post(f"/api/v1/conversations/{conv['conversationId']}/messages",
                       json={"text": "What is my attainment?"}, headers=AUTH)
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "AI_CREDENTIAL_UNAVAILABLE"
    assert body["retryable"] is False
    assert {"code", "message", "correlationId", "retryable"} <= set(body)
