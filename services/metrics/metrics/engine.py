"""Certified metric engine (PRD §8.3, §14.2).

Executes governed formulas over canonical records. Every result carries the
metric id + version, scope, as-of, null treatment and reconciliation status —
the mandatory response fields of PRD §14.2. No LLM ever computes these.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "semantic-layer" / "metric-catalog.yaml"


class Opportunity(BaseModel):
    opportunity_id: str
    owner_id: str
    account_id: str
    amount_minor: int = Field(ge=0)
    currency: str = "HKD"
    stage: str = "open"
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    forecast_category: str = "pipeline"
    is_open: bool = True


class PlanRow(BaseModel):
    assignee_id: str
    period: str
    target_minor: int = Field(ge=0)
    approval_status: str = "approved"


class MetricResult(BaseModel):
    metric_id: str
    version: int
    value: float | None  # None = suppressed per null treatment (§8.3)
    suppressed_reason: str | None = None
    scope: str
    as_of: str
    currency: str = "HKD"
    reconciliation_status: str = "reconciled"


class Catalog:
    """Loads the governed catalog (data/semantic-layer/metric-catalog.yaml)."""

    def __init__(self, path: Path = CATALOG_PATH) -> None:
        self._doc = yaml.safe_load(path.read_text())

    def metric(self, metric_id: str) -> dict:
        for m in self._doc["metrics"]:
            if m["metric_id"] == metric_id:
                return m
        raise KeyError(f"unknown metric {metric_id!r} — LLMs cannot invent metrics (§14.2)")

    def ids(self) -> list[str]:
        return [m["metric_id"] for m in self._doc["metrics"]]


def actual(opps: list[Opportunity], *, closed_category: str = "closed") -> int:
    """Actual: Σ recognized measure (closed-won bookings by default; catalog 'actual')."""
    return sum(o.amount_minor for o in opps if not o.is_open and o.forecast_category == closed_category)


def target(plans: list[PlanRow], assignee_id: str, period: str) -> int | None:
    """Approved target for assignee/period; None when no approved plan exists (suppressed, not 0)."""
    approved = [
        p.target_minor
        for p in plans
        if p.assignee_id == assignee_id and p.period == period and p.approval_status == "approved"
    ]
    return approved[0] if approved else None


def attainment_pct(actual_minor: int, target_minor: int | None) -> float | None:
    if target_minor is None or target_minor <= 0:
        return None  # suppressed: no approved target → attainment is undefined, never 0%
    return actual_minor / target_minor * 100.0


def remaining_target(actual_minor: int, target_minor: int | None) -> int | None:
    if target_minor is None:
        return None
    return max(target_minor - actual_minor, 0)


def weighted_pipeline(opps: list[Opportunity]) -> int:
    """Σ(amount × approved probability). Missing probability → stage_map default (0.2 here)."""
    total = 0
    for o in opps:
        if not o.is_open:
            continue
        p = o.probability if o.probability is not None else 0.2
        total += round(o.amount_minor * p)
    return total


def coverage(weighted_minor: int, remaining_minor: int | None) -> float | None:
    if remaining_minor is None or remaining_minor <= 0:
        return None
    return weighted_minor / remaining_minor


def forecast_gap(target_minor: int | None, actual_minor: int, forecast_minor: int) -> int | None:
    if target_minor is None:
        return None
    return target_minor - (actual_minor + forecast_minor)


def compute_attainment_report(
    opps: list[Opportunity], plans: list[PlanRow], assignee_id: str, period: str, as_of: str
) -> list[MetricResult]:
    """Assembles the Scenario-A response set (§28.1): every number with its guard behavior."""
    cat = Catalog()
    act = actual(opps)
    tgt = target(plans, assignee_id, period)
    open_opps = [o for o in opps if o.is_open]
    wp = weighted_pipeline(open_opps)
    rem = remaining_target(act, tgt)
    forecast = weighted_pipeline([o for o in open_opps if o.forecast_category in ("commit", "best_case")])
    rows: list[tuple[str, float | int | None]] = [
        ("actual", act),
        ("target", tgt),
        ("attainment_pct", attainment_pct(act, tgt)),
        ("remaining_target", rem),
        ("weighted_pipeline", wp),
        ("coverage", coverage(wp, rem)),
        ("forecast_gap", forecast_gap(tgt, act, forecast)),
    ]
    out: list[MetricResult] = []
    for metric_id, value in rows:
        m = cat.metric(metric_id)
        out.append(
            MetricResult(
                metric_id=metric_id,
                version=m["version"],
                value=value,
                suppressed_reason="no approved target for period" if value is None and tgt is None else None,
                scope=assignee_id,
                as_of=as_of,
            )
        )
    return out
