"""Mobile BFF API. Implements the committed OpenAPI contract (services/bff/openapi/openapi.json).

The orchestrator and metrics service are injected dependencies; tests use the
scripted provider. Typed error envelope (§17.8) before any streaming starts.
Dashboard proposals validate against certified metrics only (Scenario D);
actions are preview → confirm with idempotent execution (Scenario E).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="northstar-bff", version="0.1.0")


class ApiErrorBody(BaseModel):
    code: str
    message: str
    correlationId: str
    retryable: bool
    retryAfterSeconds: int | None = None


@app.exception_handler(HTTPException)
async def typed_error(request: Request, exc: HTTPException) -> JSONResponse:
    code = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "VALIDATION_FAILED",
            422: "VALIDATION_FAILED", 503: "DEPENDENCY_UNAVAILABLE"}.get(exc.status_code, "INTERNAL_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorBody(code=code, message=str(exc.detail),
                             correlationId=request.headers.get("x-correlation-id", "unknown"),
                             retryable=exc.status_code >= 500).model_dump(),
    )


def _user(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return authorization.removeprefix("Bearer ")  # gateway-verified JWT subject in production


# ------------------------------------------------------------------ conversations


class ConversationOut(BaseModel):
    conversationId: str
    scopeType: str
    scopeId: str
    createdAt: str


@app.post("/api/v1/conversations", status_code=201)
async def create_conversation(authorization: str | None = Header(default=None)) -> ConversationOut:
    user = _user(authorization)
    return ConversationOut(conversationId=f"conv_{uuid.uuid4().hex[:12]}", scopeType="seller",
                           scopeId=user, createdAt=datetime.now(UTC).isoformat())


class MessageIn(BaseModel):
    text: str = Field(min_length=1)
    clientMessageId: str | None = None


class OrchestratorDep:
    """Bridge to services/orchestrator — swapped in composition root; tests inject a stub."""

    async def converse(self, user: str, text: str) -> dict:
        raise HTTPException(status_code=503, detail="orchestrator unavailable")


_UNSET = object()
_dep: object = _UNSET  # tests may inject a stub by assigning bff.api._dep


def _default_dep() -> OrchestratorDep:
    """Live wiring runs the real pipeline in-process (bff/composition.py); stub mode 503s."""
    import os

    if os.environ.get("NORTHSTAR_BFF_MODE", "live") == "stub":
        return OrchestratorDep()
    from .composition import LiveOrchestratorDep

    return LiveOrchestratorDep()


@app.post("/api/v1/conversations/{conversation_id}/messages")
async def post_message(conversation_id: str, body: MessageIn,
                       authorization: str | None = Header(default=None),
                       accept: str = Header(default="application/json"),
                       orch: OrchestratorDep = Depends(lambda: _dep if _dep is not _UNSET else _default_dep())) -> Response:
    user = _user(authorization)
    result = await orch.converse(user, body.text)
    if "text/event-stream" in accept:
        async def sse():
            yield "event: message_start\ndata: {}\n\n"
            yield f"event: component\ndata: {json.dumps(result['components'][0])}\n\n"
            yield "event: message_stop\ndata: {}\n\n"

        return StreamingResponse(sse(), media_type="text/event-stream")
    return JSONResponse(result)


@app.get("/api/v1/me/context")
async def my_context(authorization: str | None = Header(default=None)) -> dict:
    user = _user(authorization)
    return {"userId": user, "role": "seller", "teamIds": [], "domainIds": [], "groupIds": [],
            "preferences": {"currency": "HKD", "locale": "en-HK"}, "allowedScopes": [f"seller:{user}"]}


# ------------------------------------------------------------------ voice (ADR-032, disabled pending approval)


class VoiceSettings:
    """Feature flag: voice ships only after the board approves the ADR-032 Phase-2
    plan (DPIA addendum for audio + consent copy). Default off — fail-closed."""

    enabled: bool = False


class VoiceTranscriptIn(BaseModel):
    model_config = {"populate_by_name": True}

    audio_ref: str = Field(min_length=1, alias="audioRef")  # transient STT reference; audio never persisted
    language: str | None = None


class VoicePreview(BaseModel):
    transcript: str
    confirmed: bool = False  # user must confirm; nothing reaches the orchestrator before that (§10.2)
    notice: str = "Review and edit the transcript before sending."


@app.post("/api/v1/conversations/{conversation_id}/voice-transcript", response_model=None)
async def voice_transcript(conversation_id: str, body: VoiceTranscriptIn,
                           authorization: str | None = Header(default=None)) -> VoicePreview:
    _user(authorization)
    if not VoiceSettings.enabled:
        raise HTTPException(status_code=403,
                            detail="voice input is not enabled pending governance approval (ADR-032)")
    # Enabled path (deployed behind the approved STT provider route per ADR-032):
    # STT runs behind APISIX; transcript is returned for user correction, never auto-submitted.
    return VoicePreview(transcript="[stt] " + body.audio_ref)


# ------------------------------------------------------------------ analytics (metrics service bridge)


class MetricsDep:
    async def rows(self, path: str, params: dict) -> dict:
        raise HTTPException(status_code=503, detail="metrics service unavailable")


_metrics = MetricsDep()


@app.get("/api/v1/pipeline")
async def query_pipeline(period: str | None = None, asOf: str | None = None,
                         authorization: str | None = Header(default=None),
                         metrics: MetricsDep = Depends(lambda: _metrics)) -> dict:
    _user(authorization)
    return await metrics.rows("pipeline", {"period": period, "asOf": asOf})


@app.get("/api/v1/targets/attainment")
async def query_attainment(assigneeId: str, period: str,
                           authorization: str | None = Header(default=None),
                           metrics: MetricsDep = Depends(lambda: _metrics)) -> dict:
    _user(authorization)
    return await metrics.rows("attainment", {"assigneeId": assigneeId, "period": period})


@app.get("/api/v1/metrics/{metric_id}/lineage")
async def metric_lineage(metric_id: str,
                         authorization: str | None = Header(default=None)) -> dict:
    _user(authorization)
    try:
        from metrics.engine import Catalog
        m = Catalog().metric(metric_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown metric {metric_id}") from None
    return {"metricId": m["metric_id"], "version": m["version"], "name": m["name"],
            "formula": m["formula"], "grain": m["grain"], "owner": m.get("owner"),
            "certification": m.get("certification", "draft")}


# ------------------------------------------------------------------ dashboards (Scenario D)

CERTIFIED_METRICS = {"attainment_pct", "weighted_pipeline", "coverage", "forecast_gap", "remaining_target"}


class DashboardCardIn(BaseModel):
    kind: str
    id: str
    title: str
    metric: str | None = None
    dimension: str | None = None
    query: str | None = None
    position: list[int] | None = None


class DashboardIn(BaseModel):
    dashboardId: str | None = None
    title: str
    scope: dict
    globalFilters: dict | None = None
    layout: dict
    cards: list[DashboardCardIn] = Field(min_length=1)
    refreshPolicy: str | None = None
    sharing: str | None = None


def _validate_dashboard(body: DashboardIn) -> None:
    """Server-side validation before save (§8.5): certified metrics, allowed dims, mobile layout."""
    for card in body.cards:
        if card.kind in ("kpi", "bar") and card.metric not in CERTIFIED_METRICS:
            raise HTTPException(status_code=422, detail=f"metric {card.metric!r} is not certified")
        if card.kind == "bar" and card.dimension not in ("salesperson", "team", "domain", "stage", "close_month"):
            raise HTTPException(status_code=422, detail=f"dimension {card.dimension!r} not allowed")
    if body.layout.get("mode") != "mobile_grid" or not 1 <= int(body.layout.get("columns", 2)) <= 4:
        raise HTTPException(status_code=422, detail="layout must be mobile_grid with 1-4 columns")


class ComposeIn(BaseModel):
    intent: str
    context: dict | None = None


@app.post("/api/v1/dashboards/compose")
async def compose_dashboard(body: ComposeIn, authorization: str | None = Header(default=None)) -> dict:
    """Proposal only — saved exclusively via POST /api/v1/dashboards after user confirmation."""
    _user(authorization)
    return {"dashboardId": None, "title": "Proposed dashboard",
            "scope": {"type": "seller", "id": "current"}, "globalFilters": {},
            "layout": {"mode": "mobile_grid", "columns": 2},
            "cards": [{"kind": "kpi", "id": "c1", "title": "Attainment", "metric": "attainment_pct",
                       "position": [0, 0, 1, 1]}],
            "refreshPolicy": "on_open", "sharing": "private", "_proposal": True}


@app.post("/api/v1/dashboards", status_code=201)
async def save_dashboard(body: DashboardIn, authorization: str | None = Header(default=None)) -> dict:
    _user(authorization)
    _validate_dashboard(body)
    out = body.model_dump()
    out["dashboardId"] = body.dashboardId or f"dash_{uuid.uuid4().hex[:10]}"
    return out


# ------------------------------------------------------------------ alerts


class AlertIn(BaseModel):
    ruleId: str | None = None
    metricId: str
    predicate: dict
    schedule: dict | None = None
    channel: str
    status: str = "active"


@app.post("/api/v1/alerts", status_code=201)
async def create_alert(body: AlertIn, authorization: str | None = Header(default=None),
                       idempotency_key: str | None = Header(default=None)) -> dict:
    _user(authorization)
    if body.metricId not in CERTIFIED_METRICS:
        raise HTTPException(status_code=422, detail=f"metric {body.metricId!r} is not certified")
    if body.channel not in ("in_app", "push", "email"):
        raise HTTPException(status_code=422, detail="channel must be in_app/push/email (Teams: Phase 2)")
    out = body.model_dump()
    out["ruleId"] = body.ruleId or f"rule_{uuid.uuid4().hex[:10]}"
    return out


# ------------------------------------------------------------------ actions (Scenario E)


class ActionIn(BaseModel):
    actionType: str
    targetId: str
    payload: dict | None = None


_executed_actions: dict[str, dict] = {}


@app.post("/api/v1/actions/preview")
async def preview_action(body: ActionIn, authorization: str | None = Header(default=None)) -> dict:
    _user(authorization)
    action_id = f"act_{uuid.uuid4().hex[:10]}"
    changes = [{"field": k, "oldValue": "(current)", "newValue": v, "impact": "forecast impact: recalculated"}
               for k, v in (body.payload or {}).items()]
    return {"actionId": action_id, "actionType": body.actionType, "changes": changes,
            "requiresConfirmation": True, "stepUpAuthRequired": body.actionType == "update_close_date"}


@app.post("/api/v1/actions/{action_id}/confirm")
async def confirm_action(action_id: str, authorization: str | None = Header(default=None)) -> dict:
    _user(authorization)
    if action_id in _executed_actions:  # safe to retry without duplicate effects (§28.1 E)
        prior = _executed_actions[action_id]
        return {"actionId": action_id, "status": "already_executed", "idempotentReplay": True,
                "externalRef": prior["externalRef"], "executedAt": prior["executedAt"]}
    receipt = {"actionId": action_id, "status": "executed", "idempotentReplay": False,
               "externalRef": f"crm_task_{uuid.uuid4().hex[:8]}",
               "executedAt": datetime.now(UTC).isoformat()}
    _executed_actions[action_id] = receipt
    return receipt


# ------------------------------------------------------------------ feedback


class FeedbackIn(BaseModel):
    messageId: str
    rating: str
    correction: str | None = None


@app.post("/api/v1/feedback", status_code=202)
async def feedback(body: FeedbackIn) -> dict:
    return {"status": "recorded", "messageId": body.messageId}


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
