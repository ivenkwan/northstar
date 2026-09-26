import math

import pytest
from metrics.allocation import AggregationPolicy, Membership, enterprise_total, group_view
from metrics.engine import (
    Catalog,
    Opportunity,
    PlanRow,
    attainment_pct,
    compute_attainment_report,
    coverage,
    forecast_gap,
    remaining_target,
    target,
    weighted_pipeline,
)

# ---------------------------------------------------------------- formulas (§8.3)


def test_attainment_formula_and_guards():
    assert attainment_pct(60, 100) == pytest.approx(60.0)
    assert attainment_pct(60, 0) is None  # target 0 → suppressed
    assert attainment_pct(60, None) is None  # no approved plan → undefined, not 0%


def test_remaining_target_clamps_at_zero():
    assert remaining_target(60, 100) == 40
    assert remaining_target(120, 100) == 0


def test_weighted_pipeline_uses_approved_probability_and_default():
    opps = [
        Opportunity(opportunity_id="1", owner_id="s1", account_id="a1", amount_minor=100, probability=0.6),
        Opportunity(opportunity_id="2", owner_id="s1", account_id="a1", amount_minor=100),  # default 0.2
        Opportunity(opportunity_id="3", owner_id="s1", account_id="a1", amount_minor=999, is_open=False),
    ]
    assert weighted_pipeline(opps) == 80


def test_coverage_guard_when_target_met():
    assert coverage(300, 0) is None  # nothing remaining → coverage undefined
    assert coverage(300, 150) == pytest.approx(2.0)


def test_forecast_gap():
    assert forecast_gap(100, 40, 30) == 30
    assert forecast_gap(None, 40, 30) is None


def test_no_approved_plan_suppresses_not_zero():
    assert target([PlanRow(assignee_id="s1", period="Q3", target_minor=99, approval_status="draft")], "s1", "Q3") is None


# ------------------------------------------------- catalog is loadable and governed


def test_catalog_loads_governed_definitions():
    cat = Catalog()
    assert "attainment_pct" in cat.ids()
    assert "invented_metric" not in cat.ids()
    with pytest.raises(KeyError):
        cat.metric("invented_metric")  # LLMs cannot invent metrics (§14.2)


def test_scenario_a_report_carries_metric_versions_and_guards():
    opps = [
        Opportunity(opportunity_id="w", owner_id="s1", account_id="a1", amount_minor=600_000,
                    forecast_category="closed", is_open=False),
        Opportunity(opportunity_id="c", owner_id="s1", account_id="a1", amount_minor=400_000,
                    probability=0.9, forecast_category="commit"),
    ]
    plans = [PlanRow(assignee_id="s1", period="FY27-Q1", target_minor=1_000_000)]
    report = compute_attainment_report(opps, plans, "s1", "FY27-Q1", as_of="2026-09-26T09:00:00Z")
    by_id = {r.metric_id: r for r in report}
    assert by_id["actual"].value == 600_000
    assert by_id["attainment_pct"].value == pytest.approx(60.0)
    assert by_id["attainment_pct"].version >= 3
    assert by_id["coverage"].value is not None
    assert all(r.reconciliation_status == "reconciled" for r in report)


# ------------------------------------------------ multi-group allocation (§6.2 / GPM-06)


def _ms(domain: str, groups: list[tuple[str, AggregationPolicy, float, bool]]) -> list[Membership]:
    return [
        Membership(domain_id=domain, group_id=g, policy=p, pipeline_allocation_pct=pct,
                   is_primary_group=prim, valid_from="2026-01-01")
        for g, p, pct, prim in groups
    ]


def test_domain_in_two_groups_counted_once_in_enterprise_total():
    """GPM-06 / Scenario B: Domain A in Groups X and Y must not double count."""
    ms = _ms(
        "dom_a",
        [
            ("grp_x", AggregationPolicy.FULL_VIEW, 1.0, True),
            ("grp_y", AggregationPolicy.FULL_VIEW, 1.0, False),
        ],
    )
    assert enterprise_total({"dom_a": 1_000_000}, ms) == 1_000_000


def test_proportional_allocation_sums_percentages():
    ms = _ms(
        "dom_b",
        [
            ("grp_x", AggregationPolicy.PROPORTIONAL_ALLOCATION, 0.6, True),
            ("grp_y", AggregationPolicy.PROPORTIONAL_ALLOCATION, 0.4, False),
        ],
    )
    assert math.isclose(enterprise_total({"dom_b": 1_000_000}, ms), 1_000_000)


def test_excluded_policy_drops_from_enterprise_total():
    ms = _ms("dom_c", [("grp_x", AggregationPolicy.EXCLUDED_FROM_ENTERPRISE_TOTAL, 1.0, True)])
    assert enterprise_total({"dom_c": 500_000}, ms) == 0


def test_group_view_labels_shared_domain_non_additive():
    ms = _ms(
        "dom_a",
        [
            ("grp_x", AggregationPolicy.FULL_VIEW, 1.0, True),
            ("grp_y", AggregationPolicy.FULL_VIEW, 1.0, False),
        ],
    )
    views = {v.group_id: v for v in group_view({"dom_a": 700_000}, ms)}
    assert views["grp_x"].gross_amount == 700_000  # operational visibility kept
    assert views["grp_x"].non_additive is True  # labeled (§6.2)
    assert views["grp_x"].rule == "full_view"
