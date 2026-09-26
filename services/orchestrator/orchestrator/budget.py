"""Cost controls (Phase 2, §31 'Variable AI cost'): per-tenant token budgets,
semantic cache keys, and anomaly detection feeding the cost telemetry dashboards.

Cache rule: only deterministic, non-personal scope+metric+period queries are
cacheable; conversational context and write paths never are.
"""

from __future__ import annotations

import hashlib
import json
import time

from pydantic import BaseModel, Field


class BudgetState(BaseModel):
    tenant_id: str
    period_key: str  # e.g. 2026-09
    token_limit: int = Field(ge=1)
    tokens_used: int = Field(default=0, ge=0)
    request_limit: int = Field(ge=1)
    requests_used: int = Field(default=0, ge=0)


class BudgetDecision(BaseModel):
    allowed: bool
    reason: str
    remaining_tokens: int


class BudgetLedger:
    """In-memory reference implementation; production store is per-tenant counters with TTL sweeps."""

    def __init__(self) -> None:
        self._state: dict[tuple[str, str], BudgetState] = {}

    def _get(self, tenant_id: str, period_key: str) -> BudgetState | None:
        return self._state.get((tenant_id, period_key))

    def ensure(self, tenant_id: str, period_key: str, token_limit: int, request_limit: int) -> BudgetState:
        state = self._get(tenant_id, period_key)
        if state is None:
            state = BudgetState(tenant_id=tenant_id, period_key=period_key,
                                token_limit=token_limit, request_limit=request_limit)
            self._state[(tenant_id, period_key)] = state
        return state

    def check(self, tenant_id: str, period_key: str) -> BudgetDecision:
        state = self._get(tenant_id, period_key)
        if state is None:
            return BudgetDecision(allowed=True, reason="no_budget_configured", remaining_tokens=-1)
        if state.requests_used >= state.request_limit:
            return BudgetDecision(allowed=False, reason="request_budget_exhausted",
                                  remaining_tokens=max(state.token_limit - state.tokens_used, 0))
        if state.tokens_used >= state.token_limit:
            return BudgetDecision(allowed=False, reason="token_budget_exhausted",
                                  remaining_tokens=0)
        return BudgetDecision(allowed=True, reason="ok",
                              remaining_tokens=state.token_limit - state.tokens_used)

    def record(self, tenant_id: str, period_key: str, input_tokens: int, output_tokens: int) -> BudgetDecision:
        state = self._get(tenant_id, period_key)
        if state is None:
            return BudgetDecision(allowed=True, reason="no_budget_configured", remaining_tokens=-1)
        state.requests_used += 1
        state.tokens_used += input_tokens + output_tokens
        return self.check(tenant_id, period_key)


def anomaly_detected(window_avg_tokens: float, baseline_avg_tokens: float, factor: float = 5.0) -> bool:
    """Denial-of-wallet detection (T-12): sustained per-request cost far above baseline."""
    if baseline_avg_tokens <= 0:
        return False
    return window_avg_tokens >= factor * baseline_avg_tokens


CACHEABLE_SCOPES = frozenset({"seller", "team", "domain", "group"})


def semantic_cache_key(scope_type: str, scope_id: str, metric_ids: list[str],
                       period: str, as_of_bucket: str, extra_filters: dict | None = None) -> str | None:
    """Stable cache key for deterministic analytics queries; None = not cacheable.

    as_of_bucket is the agreed staleness bucket (e.g. 15-minute floor) so cache
    entries honor freshness targets (§14.3) instead of serving stale data.
    """
    if scope_type not in CACHEABLE_SCOPES:
        return None  # conversational/personal context never cached
    if not metric_ids:
        return None
    payload = json.dumps({
        "scope": f"{scope_type}:{scope_id}",
        "metrics": sorted(metric_ids),
        "period": period,
        "as_of_bucket": as_of_bucket,
        "filters": extra_filters or {},
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def as_of_bucket(timestamp_s: int, bucket_seconds: int = 900) -> str:
    """Floors a timestamp to the staleness bucket (default 15 min per §14.3 CRM freshness)."""
    return str(timestamp_s - (timestamp_s % bucket_seconds))


class TokenUsage(BaseModel):
    """Cost telemetry record (§21): per request, no payload content."""

    tenant_id: str
    route: str  # openai-chat | anthropic-messages | capability
    model_profile: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cached: bool = False
    ts: float = Field(default_factory=time.time)
