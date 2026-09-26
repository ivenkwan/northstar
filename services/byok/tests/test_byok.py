import pytest
from byok.api import app
from byok.service import (
    ApiErrorCode,
    Bindings,
    ByokError,
    CredentialService,
    CredentialStatus,
    InMemoryVault,
    redacted,
)
from fastapi.testclient import TestClient

BINDINGS = Bindings(
    allowed_protocols=["anthropic-messages"],
    allowed_model_patterns=["approved-anthropic-*"],
    allowed_environments=["production"],
    allowed_domains=["enterprise-sales"],
)


def make_service(**kw) -> CredentialService:
    return CredentialService(InMemoryVault(), **kw)


def active_service() -> CredentialService:
    svc = make_service()
    rec = svc.register("tenant_a", "anthropic", "prod", "sk-ant-verysecret-123456", BINDINGS, "idem-1", "admin@a")
    svc.activate(rec.credential_id, "admin@a")
    return svc, rec


def test_register_returns_metadata_never_secret():
    svc = make_service()
    rec = svc.register("tenant_a", "anthropic", "prod", "sk-ant-verysecret-123456", BINDINGS, "idem-1", "admin@a")
    dumped = rec.model_dump()
    assert "sk-ant" not in str(dumped)
    assert redacted(rec)["fingerprint"].startswith("sha256:")


def test_register_is_idempotent():
    svc = make_service()
    r1 = svc.register("tenant_a", "anthropic", "prod", "sk-ant-verysecret-123456", BINDINGS, "key-1", "admin@a")
    r2 = svc.register("tenant_a", "anthropic", "prod", "DIFFERENT-ignored-on-replay-123456", BINDINGS, "key-1", "admin@a")
    assert r1.credential_id == r2.credential_id


def test_short_or_failed_validation_rejected():
    svc = make_service(probe=lambda p, k: False)
    with pytest.raises(ByokError) as e:
        svc.register("tenant_a", "anthropic", "prod", "sk-ant-verysecret-123456", BINDINGS, "idem", "a")
    assert e.value.code is ApiErrorCode.VALIDATION_FAILED


def test_missing_secret_fails_closed_with_sanitized_error():
    """ADR-023 / §16.4: unresolved reference never returns the literal string."""
    svc, rec = active_service()
    svc.vault.revoke(rec.vault_reference)  # simulate Vault loss (T-02)
    with pytest.raises(ByokError) as e:
        svc.resolve_for_route(rec.credential_id, "production", "anthropic-messages",
                              "approved-anthropic-x", "tenant_a")
    assert e.value.code is ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE
    assert "vault" not in e.value.message.lower()
    assert rec.vault_reference not in e.value.message


def test_bindings_enforced_before_provider_invocation():
    svc, rec = active_service()
    # wrong protocol
    with pytest.raises(ByokError) as e1:
        svc.resolve_for_route(rec.credential_id, "production", "openai-chat", "approved-anthropic-x", "tenant_a")
    assert e1.value.status == 403
    # wrong model family
    with pytest.raises(ByokError):
        svc.resolve_for_route(rec.credential_id, "production", "anthropic-messages", "gpt-x", "tenant_a")
    # wrong environment
    with pytest.raises(ByokError):
        svc.resolve_for_route(rec.credential_id, "staging", "anthropic-messages", "approved-anthropic-x", "tenant_a")


def test_cross_tenant_isolation_gw05():
    """ADR-033: tenant B cannot invoke tenant A's credential."""
    svc, rec = active_service()
    with pytest.raises(ByokError) as e:
        svc.resolve_for_route(rec.credential_id, "production", "anthropic-messages",
                              "approved-anthropic-x", "tenant_b")
    assert e.value.status == 403


def test_revoke_disables_then_revokes_key():
    svc, rec = active_service()
    svc.revoke(rec.credential_id, "admin@a")
    assert rec.status is CredentialStatus.REVOKED
    with pytest.raises(ByokError):
        svc.resolve_for_route(rec.credential_id, "production", "anthropic-messages",
                              "approved-anthropic-x", "tenant_a")
    assert any(a["action"] == "revoke" for a in svc.audit)  # audit metadata retained


def test_api_error_envelope_shape():
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/v1/admin/byok/credentials",
        json={"provider": "anthropic", "displayName": "x",
              "credential": "sk-ant-verysecret-123456", "bindings": BINDINGS.model_dump()},
        headers={"x-tenant-id": "t", "x-actor": "a", "idempotency-key": "k1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"credentialId", "status", "fingerprint"}
    assert "credential" not in body and "vaultReference" not in body
