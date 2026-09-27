"""Metrics service API (FastAPI). Paths under /api/v1 per ADR-028."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .allocation import Membership, enterprise_total, group_view
from .engine import Catalog

app = FastAPI(title="northstar-metrics", version="0.1.0")


class ApiError(BaseModel):
    """Typed error envelope (PRD §17.8) — identical contract to the BFF."""

    code: str
    message: str
    correlationId: str
    retryable: bool


def _err(request: Request, status: int, code: str, message: str, retryable: bool = False) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ApiError(
            code=code,
            message=message,
            correlationId=request.headers.get("x-correlation-id", "unknown"),
            retryable=retryable,
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return _err(request, exc.status_code, "VALIDATION_FAILED", str(exc.detail))


@app.get("/api/v1/metrics/{metric_id}/lineage")
async def metric_lineage(metric_id: str) -> dict:
    """Formula, owner, version, sources, quality (§19.2; §27 exit: lineage visible in UI)."""
    try:
        m = Catalog().metric(metric_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown metric {metric_id}") from None
    return {
        "metric_id": m["metric_id"],
        "version": m["version"],
        "name": m["name"],
        "formula": m["formula"],
        "grain": m["grain"],
        "owner": m.get("owner"),
        "certification": m.get("certification", "draft"),
    }


class AllocationQuery(BaseModel):
    domain_amounts_minor: dict[str, int]
    memberships: list[Membership]


@app.post("/api/v1/allocation/enterprise-total")
async def allocation_total(q: AllocationQuery) -> dict:
    """Enterprise total with §6.2 policies applied (GPM-06 engine-side anchor)."""
    return {"total_minor": enterprise_total(q.domain_amounts_minor, q.memberships)}


@app.post("/api/v1/allocation/group-view")
async def allocation_groups(q: AllocationQuery) -> dict:
    """Operational group views; shared domains labeled non-additive with their rule."""
    return {"groups": [g.model_dump() for g in group_view(q.domain_amounts_minor, q.memberships)]}


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
