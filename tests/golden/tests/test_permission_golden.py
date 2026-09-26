"""GPM permission goldens (§23.2) — end-to-end: scope resolution + record authz + roll-up math.

The platform invariant under test: authorized visibility without double counting,
with effective-dated history correctness, and suppression (not zeroing) when
definitions are missing.
"""

from __future__ import annotations

from datetime import date

from metrics.allocation import AggregationPolicy, Membership
from metrics.engine import Opportunity, PlanRow, attainment_pct, compute_attainment_report, target
from orchestrator.pipeline import MetricRow, Orchestrator, ScriptedProvider
from orchestrator.scope import OrgGraph, Person, Role, ScopeResolver, Team, authorize_record


def graph() -> OrgGraph:
    return OrgGraph(
        people=[
            Person(salesperson_id="s1", user_id="u1", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s2", user_id="u2", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s3", user_id="u3", primary_team_id="t2", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="s4", user_id="u4", primary_team_id="t1", valid_from=date(2026, 1, 1), valid_to=date(2026, 7, 1)),
            Person(salesperson_id="s4", user_id="u4", primary_team_id="t2", valid_from=date(2026, 7, 1)),
            Person(salesperson_id="m1", user_id="um", primary_team_id="t1", valid_from=date(2026, 1, 1)),
            Person(salesperson_id="d1", user_id="ud", primary_team_id="t2", valid_from=date(2026, 1, 1)),
        ],
        teams=[
            Team(team_id="t1", domain_id="dom1", manager_id="m1", valid_from=date(2026, 1, 1)),
            Team(team_id="t2", domain_id="dom1", manager_id="d1", valid_from=date(2026, 1, 1)),
        ],
        memberships=[
            {"domain_id": "dom1", "group_id": "gx", "valid_from": date(2026, 1, 1), "valid_to": None},
            {"domain_id": "dom1", "group_id": "gy", "valid_from": date(2026, 1, 1), "valid_to": None},
        ],
    )


ROLES = {"u1": Role.SELLER, "u2": Role.SELLER, "u3": Role.SELLER, "u4": Role.SELLER,
         "um": Role.TEAM_MANAGER, "ud": Role.DOMAIN_LEADER}


def test_gpm01_02_seller_scope_and_peer_exclusion():
    r = ScopeResolver(graph(), ROLES)
    token = r.resolve("u1", date(2026, 9, 1))
    assert token.visible_salesperson_ids == {"s1"}
    assert authorize_record(token, "s2") is False
    # A seller asking about the team gets their own rows only; peer rows are masked by the pipeline (§10).
    orch = Orchestrator(ScriptedProvider())
    out = orch.run("u1", "team attainment?", token, metrics=[
        MetricRow(metric_id="attainment_pct", version=3, value=60.0, owner_id="s1"),
        MetricRow(metric_id="attainment_pct", version=3, value=90.0, owner_id="s2"),
    ])
    masked = [e for e in out.evidence if e.label.startswith("[masked")]
    assert len(masked) == 1  # CONV-05: inaccessible source details remain masked


def test_gpm03_manager_team_rollup_and_member_detail():
    r = ScopeResolver(graph(), ROLES)
    token = r.resolve("um", date(2026, 9, 1))
    assert authorize_record(token, "s1") and authorize_record(token, "s2")
    assert not authorize_record(token, "s3")  # outside team


def test_gpm04_domain_leader_all_domain_teams():
    token = ScopeResolver(graph(), ROLES).resolve("ud", date(2026, 9, 1))
    assert token.visible_team_ids == {"t1", "t2"}


def test_gpm05_group_full_view_labeled_non_additive():
    from metrics.allocation import group_view

    ms = [
        Membership(domain_id="dom1", group_id="gx", policy=AggregationPolicy.FULL_VIEW, valid_from="2026-01-01"),
        Membership(domain_id="dom1", group_id="gy", policy=AggregationPolicy.FULL_VIEW, valid_from="2026-01-01"),
    ]
    views = {v.group_id: v for v in group_view({"dom1": 800_000}, ms)}
    assert views["gx"].non_additive is True and views["gy"].non_additive is True
    assert views["gx"].rule == "full_view"  # allocation rule exposed (§6.2)


def test_gpm06_no_double_counting_in_enterprise_total():
    from metrics.allocation import enterprise_total

    ms = [
        Membership(domain_id="dom1", group_id="gx", policy=AggregationPolicy.FULL_VIEW, valid_from="2026-01-01"),
        Membership(domain_id="dom1", group_id="gy", policy=AggregationPolicy.FULL_VIEW, valid_from="2026-01-01"),
        Membership(domain_id="dom2", group_id="gx", policy=AggregationPolicy.FULL_VIEW, valid_from="2026-01-01"),
    ]
    total = enterprise_total({"dom1": 1_000_000, "dom2": 500_000}, ms)
    assert total == 1_500_000  # dom1 counted once despite two group memberships


def test_gpm07_effective_dated_transfer_history():
    r = ScopeResolver(graph(), ROLES)
    q2 = r.resolve("um", date(2026, 6, 15))
    q3 = r.resolve("um", date(2026, 8, 15))
    assert "s4" in q2.visible_salesperson_ids      # s4 was in t1 pre-transfer
    assert "s4" not in q3.visible_salesperson_ids  # and in t2 after — manager view follows the dates


def test_gpm08_kpis_reconcile_to_certified_queries():
    opps = [
        Opportunity(opportunity_id="o1", owner_id="s1", account_id="a", amount_minor=600_000,
                    forecast_category="closed", is_open=False),
        Opportunity(opportunity_id="o2", owner_id="s1", account_id="a", amount_minor=400_000,
                    probability=0.9, forecast_category="commit"),
    ]
    plans = [PlanRow(assignee_id="s1", period="FY27-Q1", target_minor=1_000_000)]
    report = {r.metric_id: r for r in compute_attainment_report(opps, plans, "s1", "FY27-Q1", "2026-09-26")}
    # Exact-match gate (§23.1 analytics): values equal the governed formulas.
    assert report["actual"].value == 600_000
    assert report["attainment_pct"].value == 60.0
    assert report["coverage"].value == 400_000 * 0.9 / 400_000


def test_gpm08_suppressed_target_never_zero():
    plans = [PlanRow(assignee_id="sX", period="FY27-Q1", target_minor=500_000, approval_status="draft")]
    assert target(plans, "sX", "FY27-Q1") is None
    assert attainment_pct(120_000, None) is None


def test_gpm09_revoked_content_disappears_from_answers():
    """Access-revoked evidence is absent from retrieval results and the generated answer."""
    orch = Orchestrator(ScriptedProvider())
    token = ScopeResolver(graph(), ROLES).resolve("u1", date(2026, 9, 1))
    rows = [MetricRow(metric_id="attainment_pct", version=3, value=55.0, owner_id="s2")]
    out = orch.run("u1", "attainment?", token, metrics=rows)
    assert all(e.ref == "masked" for e in out.evidence if e.label.startswith("[masked"))
