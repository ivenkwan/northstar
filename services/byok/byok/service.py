"""BYOK credential lifecycle (PRD §16; ADR-023).

Plaintext provider keys exist only in the submit call en route to Vault.
Everything after storage is metadata: vault reference, fingerprint, bindings,
status. Fail-closed everywhere: a missing or revoked secret resolves to a
sanitized AI_CREDENTIAL_UNAVAILABLE error, never to the literal reference
string and never to a platform fallback key.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from enum import Enum

from pydantic import BaseModel


class CredentialStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class ApiErrorCode(str, Enum):
    AI_CREDENTIAL_UNAVAILABLE = "AI_CREDENTIAL_UNAVAILABLE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FORBIDDEN = "FORBIDDEN"
    UNAUTHENTICATED = "UNAUTHENTICATED"


class ByokError(Exception):
    def __init__(self, code: ApiErrorCode, message: str, status: int = 503) -> None:
        self.code, self.message, self.status = code, message, status


class Bindings(BaseModel):
    allowed_protocols: list[str]
    allowed_model_patterns: list[str]
    allowed_environments: list[str]
    allowed_domains: list[str]


class CredentialRecord(BaseModel):
    """Metadata only — the §16.2 credential object minus anything resolvable (ADR-023)."""

    credential_id: str
    tenant_id: str
    provider: str
    display_name: str
    vault_reference: str  # vault://byok/<tenant>/<provider>/<slot> — path, never a secret
    bindings: Bindings
    budget_policy_id: str | None = None
    status: CredentialStatus = CredentialStatus.PENDING_VERIFICATION
    fingerprint: str  # sha256 prefix for display; not the key
    last_validated_at: str | None = None
    rotation_due_at: str | None = None


class VaultClientProtocol:
    """What the route config controller needs from Vault (§16.3 step 5)."""

    def resolve(self, vault_reference: str) -> str:
        raise NotImplementedError


class InMemoryVault:
    """Test/dev vault: stores secrets by reference; missing reference is the T-02 case."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def put(self, vault_reference: str, secret: str) -> None:
        self._secrets[vault_reference] = secret

    def resolve(self, vault_reference: str) -> str:
        # Fail-closed (ADR-023): an unresolved reference must NEVER come back as itself.
        secret = self._secrets.get(vault_reference)
        if secret is None:
            raise ByokError(
                ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE,
                "The AI credential for this route is unavailable. Contact your tenant administrator.",
            )
        return secret

    def revoke(self, vault_reference: str) -> None:
        self._secrets.pop(vault_reference, None)


def fingerprint(key: str) -> str:
    return "sha256:" + hmac.new(b"northstar-fp-display", key.encode(), hashlib.sha256).hexdigest()[:12]


def _default_probe(provider: str, key: str) -> bool:
    """Minimal non-content validation request (§16.3 step 2). Test/dev default accepts well-formed keys."""
    return len(key) >= 16


class CredentialService:
    def __init__(self, vault: InMemoryVault, probe=_default_probe) -> None:
        self.vault = vault
        self.probe = probe  # minimal non-content validation request (§16.3 step 2)
        self.records: dict[str, CredentialRecord] = {}
        self.audit: list[dict] = []
        self._idempotency: dict[str, CredentialRecord] = {}

    def register(self, tenant_id: str, provider: str, display_name: str, plaintext_key: str,
                 bindings: Bindings, idempotency_key: str, actor: str) -> CredentialRecord:
        existing = self._idempotency.get(idempotency_key)
        if existing is not None:
            return existing
        if not plaintext_key or len(plaintext_key) < 16:
            raise ByokError(ApiErrorCode.VALIDATION_FAILED, "credential rejected by provider validation", 422)
        # 2. Verify: minimal non-content request.
        if not self.probe(provider, plaintext_key):
            raise ByokError(ApiErrorCode.VALIDATION_FAILED, "credential rejected by provider validation", 422)
        credential_id = "cred_" + secrets.token_urlsafe(8)
        vault_reference = f"vault://byok/{tenant_id}/{provider}/{credential_id}"
        # 3. Store in Vault; plaintext is dropped from this frame immediately after.
        self.vault.put(vault_reference, plaintext_key)
        record = CredentialRecord(
            credential_id=credential_id, tenant_id=tenant_id, provider=provider,
            display_name=display_name, vault_reference=vault_reference, bindings=bindings,
            fingerprint=fingerprint(plaintext_key),
        )
        self.records[credential_id] = record
        del plaintext_key  # no attribute ever holds it beyond this point
        self._audit("register", actor, credential_id, tenant_id)
        self._idempotency[idempotency_key] = record
        return record

    def activate(self, credential_id: str, actor: str) -> CredentialRecord:
        rec = self._get(credential_id)
        # 5. Activate only after schema + connectivity checks (ADR-023 pre-deploy validation).
        try:
            self.vault.resolve(rec.vault_reference)
        except ByokError:
            raise ByokError(ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE,
                            "Cannot activate: secret missing at configured reference") from None
        rec.status = CredentialStatus.ACTIVE
        self._audit("activate", actor, credential_id, rec.tenant_id)
        return rec

    def rotate(self, credential_id: str, new_plaintext_key: str, actor: str) -> CredentialRecord:
        rec = self._get(credential_id)
        if not self.probe(rec.provider, new_plaintext_key):
            raise ByokError(ApiErrorCode.VALIDATION_FAILED, "replacement credential rejected", 422)
        self.vault.put(rec.vault_reference, new_plaintext_key)  # new version under same path
        rec.fingerprint = fingerprint(new_plaintext_key)
        self._audit("rotate", actor, credential_id, rec.tenant_id)
        del new_plaintext_key
        return rec

    def revoke(self, credential_id: str, actor: str) -> CredentialRecord:
        # §16.3 step 8: disable binding first, then revoke key, retain audit metadata.
        rec = self._get(credential_id)
        rec.status = CredentialStatus.REVOKED
        self.vault.revoke(rec.vault_reference)
        self._audit("revoke", actor, credential_id, rec.tenant_id)
        return rec

    def resolve_for_route(self, credential_id: str, environment: str, protocol: str,
                          model: str, tenant_id: str) -> str:
        """Gateway-side resolution: bindings enforced BEFORE provider invocation (§28.2 criterion 5)."""
        rec = self._get(credential_id)
        if rec.tenant_id != tenant_id:
            raise ByokError(ApiErrorCode.FORBIDDEN, "credential not accessible", 403)
        if rec.status is not CredentialStatus.ACTIVE:
            raise ByokError(ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE, "The AI credential for this route is unavailable.")
        if environment not in rec.bindings.allowed_environments or protocol not in rec.bindings.allowed_protocols:
            raise ByokError(ApiErrorCode.FORBIDDEN, "credential binding does not permit this route", 403)
        if not any(_match(p, model) for p in rec.bindings.allowed_model_patterns):
            raise ByokError(ApiErrorCode.FORBIDDEN, "model not permitted for this credential", 403)
        return self.vault.resolve(rec.vault_reference)  # fail-closed inside

    def _get(self, credential_id: str) -> CredentialRecord:
        rec = self.records.get(credential_id)
        if rec is None:
            raise ByokError(ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE, "unknown credential")
        return rec

    def _audit(self, action: str, actor: str, credential_id: str, tenant_id: str) -> None:
        self.audit.append({"action": action, "actor": actor, "credential_id": credential_id,
                           "tenant_id": tenant_id})  # immutable in production store (§16.5)


def _match(pattern: str, value: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(value, pattern)


def redacted(record: CredentialRecord) -> dict:
    """API responses never include the secret, Vault token, or resolvable internal path (§16.5).

    The vault reference is internal; external responses carry id + fingerprint + status only.
    """
    return {
        "credentialId": record.credential_id,
        "tenantId": record.tenant_id,
        "provider": record.provider,
        "displayName": record.display_name,
        "status": record.status.value,
        "fingerprint": record.fingerprint,
        "bindings": record.bindings.model_dump(),
    }
