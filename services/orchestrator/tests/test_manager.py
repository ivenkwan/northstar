from datetime import date

import pytest
from orchestrator.manager import (
    ExceptionKind,
    RepSnapshot,
    brief_team,
    coaching_brief,
    detect_exceptions,
    propose_reassignment,
)
from orchestrator.scope import OrgGraph, Person, Role, ScopeResolver, Team


def rep(**kw) -> RepSnapshot:
    defaults = dict(salesperson_id="s1", attainment_pct=55.0, coverage=4.0, forecast_gap_minor=100_000,
                    open_count=10, stalled_count=1, late_stage_without_date=0)
    defaults.update(kw)
    return RepSnapshot(**defaults)


def graph() -> OrgGraph:
    return OrgGraph(
        people=[
            Person(salesperson_id="m", user_id="u_m", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s1", user_id="u_s1", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s2", user_id="u_s2", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s_out", user_id="u_out", primary_team_id="t2", valid_from=date(2026, 1, 1)),
        ],
        teams=[
            Team(team_id="t1", domain_id="dom1", manager_id="m", valid_from=date(2026, 1, 1)),
            Team(team_id="t2", domain_id="dom1", manager_id="s_out", valid_from=date(2026, 1, 1)),
        ],
    )


ROLES = {"u_m": Role.TEAM_MANAGER, "u_s1": Role.SELLER, "u_s2": Role.SELLER, "u_out": Role.SELLER}


def test_healthy_rep_has_no_exceptions():
    assert detect_exceptions([rep()]) == []


def test_coverage_shortfall_detected_only_with_gap():
    flagged = detect_exceptions([rep(coverage=1.8, forecast_gap_minor=100_000)])
    assert flagged[0].kind is ExceptionKind.COVERAGE_SHORTFALL
    # coverage low but target already covered → no exception
    assert detect_exceptions([rep(coverage=1.8, forecast_gap_minor=0)]) == []


def test_stalled_majority_is_critical():
    excs = detect_exceptions([rep(stalled_count=6, open_count=10)])
    assert excs[0].kind is ExceptionKind.STALLED_PIPELINE
    assert excs[0].severity == "critical"
    mild = detect_exceptions([rep(stalled_count=3, open_count=10)])
    assert mild[0].severity == "warning"
    noise = detect_exceptions([rep(stalled_count=2, open_count=10)])  # 20% < 30% threshold
    assert noise == []


def test_missing_next_step_flagged():
    excs = detect_exceptions([rep(late_stage_without_date=2)])
    assert excs[0].kind is ExceptionKind.MISSING_NEXT_STEP


def test_coaching_brief_pairs_numbers_with_talking_points():
    brief = coaching_brief(rep(coverage=1.5, stalled_count=6, open_count=10),
                           detect_exceptions([rep(coverage=1.5, stalled_count=6, open_count=10)]), "u_m")
    assert any("attainment" in h for h in brief.highlights)
    assert any("stalled" in tp.lower() or "pipeline" in tp.lower() for tp in brief.talking_points)


def test_reassignment_blocked_outside_manager_scope():
    resolver = ScopeResolver(graph(), ROLES)
    with pytest.raises(PermissionError):
        propose_reassignment(["opp1"], "s1", "s_out", resolver, "u_m", date(2026, 9, 1))


def test_reassignment_within_scope_requires_approval():
    resolver = ScopeResolver(graph(), ROLES)
    prop = propose_reassignment(["opp1", "opp2"], "s1", "s2", resolver, "u_m", date(2026, 9, 1))
    assert prop.requires_approval is True  # preview + approval, never executed inline
    assert "roll-ups" in prop.impact


def test_team_brief_covers_only_visible_reps():
    briefs = brief_team(graph(), ROLES, "u_m", date(2026, 9, 1),
                        [rep(), rep(salesperson_id="s2"), rep(salesperson_id="s_out")])
    assert {b.salesperson_id for b in briefs} == {"s1", "s2"}  # out-of-team rep excluded
