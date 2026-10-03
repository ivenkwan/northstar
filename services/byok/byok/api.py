"""BYOK admin API (§16.5) — /api/v1/admin/byok/credentials per ADR-028."""

from __future__ import annotations

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .service import ApiErrorCode, Bindings, ByokError, CredentialService, InMemoryVault, redacted

app = FastAPI(title="northstar-byok", version="0.1.0")


class ApiError(BaseModel):
    code: str
    message: str
    correlationId: str
    retryable: bool


@app.exception_handler(ByokError)
async def byok_error(request: Request, exc: ByokError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content=ApiError(code=exc.code.value, message=exc.message,
                         correlationId=request.headers.get("x-correlation-id", "unknown"),
                         retryable=False).model_dump(),
    )


class RegisterRequest(BaseModel):
    provider: str
    displayName: str
    credential: str = Field(min_length=16)  # one-time payload; never stored by the service
    bindings: Bindings


svc = CredentialService(InMemoryVault())


def _svc() -> CredentialService:
    return svc


@app.post("/api/v1/admin/byok/credentials")
async def register_credential(
    body: RegisterRequest,
    request: Request,
    x_tenant_id: str = Header(alias="x-tenant-id"),
    x_actor: str = Header(alias="x-actor"),
    idempotency_key: str = Header(alias="idempotency-key"),
) -> dict:
    record = _svc().register(
        tenant_id=x_tenant_id, provider=body.provider, display_name=body.displayName,
        plaintext_key=body.credential, bindings=body.bindings,
        idempotency_key=idempotency_key, actor=x_actor,
    )
    return redacted(record)  # credentialId, fingerprint, status only (§16.2)


@app.get("/api/v1/admin/byok/credentials")
async def list_credentials(x_tenant_id: str = Header(alias="x-tenant-id")) -> dict:
    return {"credentials": [redacted(r) for r in _svc().records.values() if r.tenant_id == x_tenant_id]}


@app.get("/api/v1/admin/byok/credentials/{credential_id}/bindings")
async def get_bindings(credential_id: str, x_tenant_id: str = Header(alias="x-tenant-id")) -> dict:
    rec = _svc()._get(credential_id)
    if rec.tenant_id != x_tenant_id:
        raise ByokError(ApiErrorCode.FORBIDDEN, "credential not accessible", 403)
    return {"credentialId": credential_id, "bindings": rec.bindings.model_dump()}


@app.post("/api/v1/admin/byok/credentials/{credential_id}/test")
async def test_credential(credential_id: str, x_tenant_id: str = Header(alias="x-tenant-id")) -> dict:
    rec = _svc()._get(credential_id)
    if rec.tenant_id != x_tenant_id:
        raise ByokError(ApiErrorCode.FORBIDDEN, "credential not accessible", 403)
    secret = _svc().vault.resolve(rec.vault_reference)
    passed = _svc().probe(rec.provider, secret)
    return {"credentialId": credential_id, "status": "ok" if passed else "failed", "probePassed": passed}


@app.post("/api/v1/admin/byok/credentials/{credential_id}/activate")
async def activate(credential_id: str, x_actor: str = Header(alias="x-actor")) -> dict:
    return redacted(_svc().activate(credential_id, x_actor))


@app.post("/api/v1/admin/byok/credentials/{credential_id}/rotate")
async def rotate(credential_id: str, body: RegisterRequest, x_actor: str = Header(alias="x-actor")) -> dict:
    return redacted(_svc().rotate(credential_id, body.credential, x_actor))


@app.delete("/api/v1/admin/byok/credentials/{credential_id}")
async def revoke(credential_id: str, x_actor: str = Header(alias="x-actor")) -> dict:
    return redacted(_svc().revoke(credential_id, x_actor))


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
