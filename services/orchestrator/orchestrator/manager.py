"""Manager workflow expansions (Phase 2, §24.3): exception management, coaching
briefs, and reassignment. Data-driven and deterministic — the manager UI consumes
these outputs; the pipeline only ever presents them, never executes people
decisions (§4.3 exclusions).
"""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel

from .scope import OrgGraph, Role, ScopeResolver


class RepSnapshot(BaseModel):
    salesperson_id: str
    attainment_pct: float | None
    coverage: float | None
    forecast_gap_minor: int | None
    open_count: int
    stalled_count: int          # open opps with no activity ≥ staleness days
    late_stage_without_date: int


class ExceptionKind(str, enum.Enum):
    STALLED_PIPELINE = "stalled_pipeline"
    COVERAGE_SHORTFALL = "coverage_shortfall"
    FORECAST_RISK = "forecast_risk"
    MISSING_NEXT_STEP = "missing_next_step"


class ManagerException(BaseModel):
    kind: ExceptionKind
    salesperson_id: str
    detail: str
    severity: str = "warning"   # warning | critical
    threshold: str


class CoachingBrief(BaseModel):
    """Monday-review brief for one rep: grounded numbers + suggested talking points."""

    salesperson_id: str
    generated_for: str
    highlights: list[str]
    talking_points: list[str]
    exceptions: list[ManagerException]


class ReassignmentProposal(BaseModel):
    """Ownership change proposal — preview + approval, never executed inline (§8.7)."""

    proposal_id: str
    opportunity_ids: list[str]
    from_salesperson: str
    to_salesperson: str
    requires_approval: bool = True
    impact: str


COVERAGE_FLOOR = 3.0
STALL_DAYS = 21


def detect_exceptions(reps: list[RepSnapshot]) -> list[ManagerException]:
    out: list[ManagerException] = []
    for r in reps:
        if r.coverage is not None and r.coverage < COVERAGE_FLOOR and (r.forecast_gap_minor or 0) > 0:
            out.append(ManagerException(
                kind=ExceptionKind.COVERAGE_SHORTFALL, salesperson_id=r.salesperson_id,
                detail=f"coverage {r.coverage:.1f}x with gap remaining",
                threshold=f"coverage<{COVERAGE_FLOOR}x"))
        if r.stalled_count > 0 and r.stalled_count / max(r.open_count, 1) >= 0.3:
            out.append(ManagerException(
                kind=ExceptionKind.STALLED_PIPELINE, salesperson_id=r.salesperson_id,
                detail=f"{r.stalled_count}/{r.open_count} open opps stalled ≥{STALL_DAYS}d",
                severity="critical" if r.stalled_count / max(r.open_count, 1) >= 0.5 else "warning",
                threshold="stalled_ratio>=0.3"))
        if r.late_stage_without_date > 0:
            out.append(ManagerException(
                kind=ExceptionKind.MISSING_NEXT_STEP, salesperson_id=r.salesperson_id,
                detail=f"{r.late_stage_without_date} late-stage opps without next step",
                threshold="any"))
    return out


def coaching_brief(rep: RepSnapshot, exceptions: list[ManagerException], manager_id: str) -> CoachingBrief:
    highlights: list[str] = []
    if rep.attainment_pct is not None:
        pace = "ahead of" if rep.attainment_pct >= 100 else "behind"
        highlights.append(f"attainment {rep.attainment_pct:.0f}% ({pace} plan)")
    if rep.coverage is not None:
        highlights.append(f"coverage {rep.coverage:.1f}x of remaining target")
    if rep.forecast_gap_minor is not None:
        highlights.append(f"forecast gap {rep.forecast_gap_minor} minor units")
    talking_points: list[str] = []
    for exc in exceptions:
        match exc.kind:
            case ExceptionKind.COVERAGE_SHORTFALL:
                talking_points.append("Where will new pipeline come from in the next 30 days?")
            case ExceptionKind.STALLED_PIPELINE:
                talking_points.append("Walk the stalled deals: revive, re-stage, or close out?")
            case ExceptionKind.MISSING_NEXT_STEP:
                talking_points.append("Add concrete next steps to late-stage deals before the review.")
    return CoachingBrief(salesperson_id=rep.salesperson_id, generated_for=manager_id,
                         highlights=highlights, talking_points=talking_points, exceptions=exceptions)


def propose_reassignment(opportunity_ids: list[str], from_id: str, to_id: str,
                         resolver: ScopeResolver, manager_user: str, as_of: date) -> ReassignmentProposal:
    """A manager may only reassign within their effective team scope (§11.1 ReBAC)."""
    token = resolver.resolve(manager_user, as_of)
    if from_id not in token.visible_salesperson_ids or to_id not in token.visible_salesperson_ids:
        raise PermissionError("reassignment outside manager scope")
    return ReassignmentProposal(
        proposal_id=f"reassign_{abs(hash((tuple(opportunity_ids), from_id, to_id))) % 10**10}",
        opportunity_ids=opportunity_ids, from_salesperson=from_id, to_salesperson=to_id,
        impact="ownership, team roll-ups, and target attribution recalculate on effective date")


def brief_team(graph: OrgGraph, roles: dict[str, Role], manager_user: str, as_of: date,
               reps: list[RepSnapshot]) -> list[CoachingBrief]:
    resolver = ScopeResolver(graph, roles)
    token = resolver.resolve(manager_user, as_of)
    visible = [r for r in reps if r.salesperson_id in token.visible_salesperson_ids]
    briefs = []
    for rep in visible:
        excs = [e for e in detect_exceptions([rep])]
        briefs.append(coaching_brief(rep, excs, manager_user))
    return briefs
