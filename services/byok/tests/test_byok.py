import pytest
from byok.api import app, _svc
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


def test_byok_api_full_surface():
    """Tests list, get_bindings, test, activate, rotate, and revoke endpoints (§16.5)."""
    client = TestClient(app, raise_server_exceptions=False)
    headers = {"x-tenant-id": "tenant_api", "x-actor": "admin_api", "idempotency-key": "idem_api_1"}

    # 1. Register
    resp = client.post(
        "/api/v1/admin/byok/credentials",
        json={"provider": "anthropic", "displayName": "Primary Anthropic",
              "credential": "sk-ant-verysecret-999999", "bindings": BINDINGS.model_dump()},
        headers=headers,
    )
    assert resp.status_code == 200
    cred_id = resp.json()["credentialId"]
    assert resp.json()["status"] == "pending_verification"

    # 2. List credentials
    list_resp = client.get("/api/v1/admin/byok/credentials", headers={"x-tenant-id": "tenant_api"})
    assert list_resp.status_code == 200
    creds = list_resp.json()["credentials"]
    assert any(c["credentialId"] == cred_id for c in creds)

    # 3. Get bindings
    bindings_resp = client.get(
        f"/api/v1/admin/byok/credentials/{cred_id}/bindings",
        headers={"x-tenant-id": "tenant_api"},
    )
    assert bindings_resp.status_code == 200
    assert bindings_resp.json()["bindings"]["allowed_protocols"] == ["anthropic-messages"]

    # Cross-tenant get_bindings rejected
    forbidden_bindings = client.get(
        f"/api/v1/admin/byok/credentials/{cred_id}/bindings",
        headers={"x-tenant-id": "other_tenant"},
    )
    assert forbidden_bindings.status_code == 403

    # 4. Test credential
    test_resp = client.post(
        f"/api/v1/admin/byok/credentials/{cred_id}/test",
        headers={"x-tenant-id": "tenant_api"},
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["probePassed"] is True

    # 5. Activate
    activate_resp = client.post(
        f"/api/v1/admin/byok/credentials/{cred_id}/activate",
        headers={"x-actor": "admin_api"},
    )
    assert activate_resp.status_code == 200
    assert activate_resp.json()["status"] == "active"

    # 6. Rotate
    rotate_resp = client.post(
        f"/api/v1/admin/byok/credentials/{cred_id}/rotate",
        json={"provider": "anthropic", "displayName": "Primary Anthropic Rotated",
              "credential": "sk-ant-verysecret-888888", "bindings": BINDINGS.model_dump()},
        headers={"x-actor": "admin_api"},
    )
    assert rotate_resp.status_code == 200

    # 7. Revoke
    revoke_resp = client.delete(
        f"/api/v1/admin/byok/credentials/{cred_id}",
        headers={"x-actor": "admin_api"},
    )
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"
