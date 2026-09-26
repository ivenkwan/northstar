"""Account planning and partner selling (Phase 3, §24.4).

Structured account plans: objectives, whitespace references, partner attach,
and plan-versus-actual tracking. Plans are versioned operational records —
the CRM stays the system of record (§4.1); Northstar holds the analytical
projection.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlanObjective(BaseModel):
    objective_id: str
    description: str
    target_minor: int = Field(default=0, ge=0)
    booked_minor: int = Field(default=0, ge=0)


class PartnerInvolvement(BaseModel):
    partner_id: str
    role: str                    # co-sell | referral | implementation
    registration_id: str | None = None  # deal-registration guard
    attached_opportunities: list[str] = Field(default_factory=list)


class AccountPlan(BaseModel):
    plan_id: str
    account_id: str
    owner_id: str
    period: str
    version: int = 1
    objectives: list[PlanObjective] = Field(default_factory=list)
    partners: list[PartnerInvolvement] = Field(default_factory=list)


class PartnerComplianceReport(BaseModel):
    partner_id: str
    attached_deals: int
    unregistered_deals: list[str]  # co-sell without registration → policy flag, not silent


def objective_progress(plan: AccountPlan) -> list[dict]:
    out = []
    for o in plan.objectives:
        pct = (o.booked_minor / o.target_minor * 100) if o.target_minor > 0 else None
        out.append({"objective_id": o.objective_id,
                    "attainment_pct": pct,  # None = no target set (suppressed, §8.3 discipline)
                    "gap_minor": max(o.target_minor - o.booked_minor, 0)})
    return out


def partner_compliance(plan: AccountPlan) -> list[PartnerComplianceReport]:
    reports = []
    for p in plan.partners:
        needs_reg = p.role == "co-sell"
        unregistered = [opp for opp in p.attached_opportunities
                        if needs_reg and p.registration_id is None]
        reports.append(PartnerComplianceReport(
            partner_id=p.partner_id, attached_deals=len(p.attached_opportunities),
            unregistered_deals=unregistered))
    return reports


def merge_plan_versions(current: AccountPlan, incoming: AccountPlan) -> AccountPlan:
    """Versioned update: monotonic versioning, never destructive — history preserved (§9.3)."""
    if incoming.account_id != current.account_id:
        raise ValueError("cannot merge plans across accounts")
    return incoming.model_copy(update={"version": current.version + 1})
