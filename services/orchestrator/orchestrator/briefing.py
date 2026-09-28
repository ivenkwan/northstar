"""Opportunity Agent deal brief (§9.1) and daily briefing composition (§7.1).

Deterministic composition over canonical deal snapshots and metric-engine
output: transparent indicators, ranked risks, recommended next steps, and
evidence on every claim (§28.1 Scenario-A posture: no definitive outcomes).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DealSnapshot(BaseModel):
    """Canonical deal fields the brief reasons over — no free text from the model."""

    opportunity_id: str
    account_id: str
    name: str
    owner_id: str
    amount_minor: int = Field(ge=0)
    stage: str                      # early | middle | late | closed_won | closed_lost
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    close_date: str
    stage_age_days: int = Field(default=0, ge=0)
    days_since_activity: int = Field(default=0, ge=0)
    close_date_push_count: int = Field(default=0, ge=0)
    has_next_step: bool = True


class HealthIndicator(BaseModel):
    kind: str                       # stale | close_date_push | missing_next_step | stage_age | late_stage_low_prob
    detail: str
    severity: str                   # warning | critical


class EvidenceItem(BaseModel):
    type: str                       # crm_record | metric_definition | activity
    ref: str
    label: str


class RiskItem(BaseModel):
    """Deal-level risk (distinct from the rep-level ManagerException shape)."""

    kind: str
    detail: str
    severity: str                     # warning | critical


class OpportunityBrief(BaseModel):
    opportunity_id: str
    account_id: str
    name: str
    owner_id: str
    as_of: str
    headline: str
    summary: list[str]
    indicators: list[HealthIndicator]
    risks: list[RiskItem]
    next_steps: list[str]
    evidence: list[EvidenceItem]


STALE_DAYS = 21  # shared with manager.py thresholds


def deal_indicators(d: DealSnapshot) -> list[HealthIndicator]:
    out: list[HealthIndicator] = []
    if d.days_since_activity >= STALE_DAYS:
        out.append(HealthIndicator(kind="stale", severity="critical",
                                   detail=f"no activity for {d.days_since_activity}d"))
    if d.close_date_push_count >= 2:
        out.append(HealthIndicator(kind="close_date_push", severity="warning",
                                   detail=f"close date pushed {d.close_date_push_count}x"))
    if not d.has_next_step:
        out.append(HealthIndicator(kind="missing_next_step", severity="warning",
                                   detail="no concrete next step recorded"))
    if d.stage_age_days >= 60 and d.stage in ("middle", "late"):
        out.append(HealthIndicator(kind="stage_age", severity="warning",
                                   detail=f"{d.stage_age_days}d in {d.stage} stage"))
    if d.stage == "late" and d.probability is not None and d.probability < 0.4:
        out.append(HealthIndicator(kind="late_stage_low_prob", severity="critical",
                                   detail=f"late stage at {d.probability:.0%} probability"))
    return out


NEXT_STEP_MAP: dict[str, str] = {
    "stale": "Re-engage: schedule a working session with the champion this week.",
    "close_date_push": "Inspect the push pattern; agree a written, dated commit criterion.",
    "missing_next_step": "Add a concrete next step with an owner and a date.",
    "stage_age": "Decide: advance, re-qualify, or close out — do not let it idle.",
    "late_stage_low_prob": "Multi-thread to the economic buyer or de-risk the forecast category.",
}


def compose_deal_brief(d: DealSnapshot, as_of: str) -> OpportunityBrief:
    indicators = deal_indicators(d)
    summary = [
        f"{d.stage} stage, {d.amount_minor} minor units, closing {d.close_date}",
        *(f"{ind.severity}: {ind.detail}" for ind in indicators),
    ]
    risks = [
        RiskItem(kind=ind.kind, detail=ind.detail, severity=ind.severity)
        for ind in indicators
    ]
    severity_rank = {"critical": 0, "warning": 1}
    return OpportunityBrief(
        opportunity_id=d.opportunity_id, account_id=d.account_id, name=d.name, owner_id=d.owner_id,
        as_of=as_of,
        headline=f"{d.name}: {'needs attention' if indicators else 'healthy'}",
        summary=summary, indicators=indicators, risks=risks,
        next_steps=[NEXT_STEP_MAP[ind.kind] for ind in sorted(indicators, key=lambda i: severity_rank[i.severity])],
        evidence=[
            EvidenceItem(type="crm_record", ref=d.opportunity_id, label="Opportunity record"),
            EvidenceItem(type="activity", ref=f"last_activity:{d.days_since_activity}d", label="Activity recency"),
        ],
    )


def risk_score(brief: OpportunityBrief) -> int:
    score = 0
    for ind in brief.indicators:
        score += 3 if ind.severity == "critical" else 1
    return score


def select_top_risks(briefs: list[OpportunityBrief], owner_ids: set[str], limit: int = 3) -> list[OpportunityBrief]:
    """Top risks within an authorized owner set only (§11.1; masked elsewhere)."""
    visible = [b for b in briefs if b.owner_id in owner_ids]
    visible.sort(key=lambda b: (-risk_score(b), b.opportunity_id))
    return visible[:limit]


# ------------------------------------------------------------------ daily briefing (§7.1)


class SignalItem(BaseModel):
    signal_type: str                # funding | expansion | regulation | …(§8.4 taxonomy)
    entity: str
    headline: str
    source: str
    published_at: str
    confidence: float = Field(ge=0.0, le=1.0)


class KpiEntry(BaseModel):
    metric_id: str
    version: int
    value: float | None             # None = suppressed (§8.3 guards)
    unit: str = "raw"               # percent | ratio | minor


class DailyBriefing(BaseModel):
    as_of: str
    scope_id: str
    greeting: str
    kpis: list[KpiEntry]
    top_risks: list[OpportunityBrief]
    market_signals: list[SignalItem]
    overdue_actions: int = 0
    evidence: list[EvidenceItem]


def compose_daily_briefing(
    as_of: str,
    user_id: str,
    metric_rows: list,              # metrics.engine MetricResult rows
    deals: list[DealSnapshot],
    signals: list[SignalItem],
    today: date | None = None,
) -> DailyBriefing:
    briefs = [compose_deal_brief(d, as_of) for d in deals]
    # Authorization happened upstream (pipeline step 5): callers pass scope-filtered
    # deals only; ranking here is purely within that authorized set.
    top_risks = select_top_risks(briefs, {d.owner_id for d in deals})
    kpis = [
        KpiEntry(metric_id=r.metric_id, version=r.version, value=r.value,
                 unit="percent" if r.metric_id == "attainment_pct" else "ratio" if r.metric_id == "coverage" else "minor")
        for r in metric_rows
        if r.metric_id in ("attainment_pct", "coverage", "forecast_gap", "remaining_target")
    ]
    return DailyBriefing(
        as_of=as_of, scope_id=user_id,
        greeting="Here is your day at a glance." if (today or date(2026, 9, 27)).weekday() < 5
        else "Quiet weekend brief — pipeline does not sleep.",
        kpis=kpis, top_risks=top_risks, market_signals=signals[:2],
        overdue_actions=sum(1 for d in deals if not d.has_next_step),
        evidence=[
            EvidenceItem(type="metric_definition", ref=k.metric_id, label=f"{k.metric_id} v{k.version}")
            for k in kpis
        ] + [e for b in top_risks for e in b.evidence[:1]],
    )


__all__ = [
    "DailyBriefing",
    "DealSnapshot",
    "EvidenceItem",
    "HealthIndicator",
    "KpiEntry",
    "OpportunityBrief",
    "SignalItem",
    "compose_daily_briefing",
    "compose_deal_brief",
    "deal_indicators",
    "risk_score",
    "select_top_risks",
]
