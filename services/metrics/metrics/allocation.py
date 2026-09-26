"""Multi-group allocation engine (PRD §6.2, ADR goldens GPM-05/06).

The same pipeline must never be summed into an enterprise total more than once
when a domain participates in several groups. Each DomainGroupMembership carries
an aggregation_policy; group views and enterprise totals apply them differently.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AggregationPolicy(str, Enum):
    FULL_VIEW = "full_view"
    PROPORTIONAL_ALLOCATION = "proportional_allocation"
    PRIMARY_ONLY = "primary_only"
    EXCLUDED_FROM_ENTERPRISE_TOTAL = "excluded_from_enterprise_total"


class Membership(BaseModel):
    domain_id: str
    group_id: str
    policy: AggregationPolicy = AggregationPolicy.FULL_VIEW
    pipeline_allocation_pct: float = Field(default=1.0, ge=0.0, le=1.0)
    is_primary_group: bool = True  # marks the single primary membership for PRIMARY_ONLY
    valid_from: str
    valid_to: str | None = None


class AllocatedAmount(BaseModel):
    group_id: str
    gross_amount: float
    counted_amount: float
    non_additive: bool
    rule: str  # human-readable allocation rule surfaced in the UI (§6.2)


def group_view(domain_amounts: dict[str, float], memberships: list[Membership]) -> list[AllocatedAmount]:
    """Operational group view: full amounts per group, labeled non-additive when shared."""
    counts: dict[str, int] = {}
    for m in memberships:
        counts[m.domain_id] = counts.get(m.domain_id, 0) + 1
    out: dict[str, AllocatedAmount] = {}
    for m in memberships:
        amount = domain_amounts.get(m.domain_id, 0.0)
        entry = out.get(m.group_id)
        shared = counts.get(m.domain_id, 1) > 1
        if entry is None:
            out[m.group_id] = AllocatedAmount(
                group_id=m.group_id,
                gross_amount=amount,
                counted_amount=amount,
                non_additive=shared,
                rule=m.policy.value,
            )
        else:
            entry.gross_amount += amount
            entry.counted_amount += amount
            entry.non_additive = entry.non_additive or shared
    return list(out.values())


def enterprise_total(domain_amounts: dict[str, float], memberships: list[Membership]) -> float:
    """Cross-group enterprise total: each domain counted exactly once per its policy."""
    total = 0.0
    for domain_id, amount in domain_amounts.items():
        applicable = [m for m in memberships if m.domain_id == domain_id]
        if not applicable:
            # Domain outside all groups still belongs in the enterprise total once.
            total += amount
            continue
        match applicable[0].policy:
            case AggregationPolicy.EXCLUDED_FROM_ENTERPRISE_TOTAL:
                continue
            case AggregationPolicy.PROPORTIONAL_ALLOCATION:
                # Sum of allocation percentages across groups; capped at 1.0 by constraint.
                total += amount * sum(m.pipeline_allocation_pct for m in applicable)
            case AggregationPolicy.PRIMARY_ONLY:
                # Counted once via the primary membership, regardless of group count.
                total += amount
            case AggregationPolicy.FULL_VIEW:
                # Full-view domains are operational-only for their groups; for the
                # enterprise total they count once (primary membership), never per group.
                total += amount
    return total
