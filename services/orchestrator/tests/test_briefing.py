from datetime import date

from metrics.engine import Opportunity, PlanRow, compute_attainment_report
from orchestrator.briefing import (
    DailyBriefing,
    DealSnapshot,
    SignalItem,
    compose_daily_briefing,
    compose_deal_brief,
    deal_indicators,
    risk_score,
    select_top_risks,
)

AS_OF = "2026-09-27T08:00:00Z"


def deal(**kw) -> DealSnapshot:
    defaults = dict(opportunity_id="opp_1", account_id="acct_9", name="ACME renewal",
                    owner_id="s1", amount_minor=400_000, stage="middle", probability=0.6,
                    close_date="2026-12-15", stage_age_days=20, days_since_activity=5,
                    close_date_push_count=0, has_next_step=True)
    defaults.update(kw)
    return DealSnapshot(**defaults)


# ------------------------------------------------------------------ deal brief (§9.1)


def test_healthy_deal_has_clean_brief():
    brief = compose_deal_brief(deal(), AS_OF)
    assert brief.indicators == []
    assert "healthy" in brief.headline
    assert brief.next_steps == []
    assert any(e.type == "crm_record" and e.ref == "opp_1" for e in brief.evidence)


def test_indicators_fire_with_severity():
    messy = deal(days_since_activity=30, close_date_push_count=2, has_next_step=False,
                 stage_age_days=70, stage="late", probability=0.3)
    kinds = [i.kind for i in deal_indicators(messy)]
    assert kinds == ["stale", "close_date_push", "missing_next_step", "stage_age", "late_stage_low_prob"]
    severities = {i.kind: i.severity for i in deal_indicators(messy)}
    assert severities["stale"] == "critical" and severities["close_date_push"] == "warning"


def test_next_steps_prioritize_critical_and_carry_evidence():
    brief = compose_deal_brief(deal(days_since_activity=30, has_next_step=False), AS_OF)
    first_step = brief.next_steps[0]
    assert "Re-engage" in first_step  # critical (stale) sorted before warning
    assert all(e.label for e in brief.evidence)  # every claim traceable (CONV-05/06)


def test_top_risks_ranked_by_score_and_owner_filtered():
    briefs = [
        compose_deal_brief(deal(opportunity_id="a", days_since_activity=30), AS_OF),           # critical stale
        compose_deal_brief(deal(opportunity_id="b", close_date_push_count=3), AS_OF),          # warning push
        compose_deal_brief(deal(opportunity_id="c"), AS_OF),                                    # healthy
        compose_deal_brief(deal(opportunity_id="peer", owner_id="s2", days_since_activity=40), AS_OF),
    ]
    top = select_top_risks(briefs, {"s1"}, limit=2)
    assert [b.opportunity_id for b in top] == ["a", "b"]       # score order, peer excluded
    assert risk_score(briefs[0]) == 3 and risk_score(briefs[1]) == 1


# ------------------------------------------------------------------ daily briefing (§7.1)


def metric_rows():
    opps = [
        Opportunity(opportunity_id="o1", owner_id="s1", account_id="a", amount_minor=600_000,
                    forecast_category="closed", is_open=False),
        Opportunity(opportunity_id="o2", owner_id="s1", account_id="a", amount_minor=400_000,
                    probability=0.9, forecast_category="commit"),
    ]
    plans = [PlanRow(assignee_id="s1", period="FY27-Q1", target_minor=1_000_000)]
    return compute_attainment_report(opps, plans, "s1", "FY27-Q1", AS_OF)


def signals():
    return [
        SignalItem(signal_type="expansion", entity="Acme Corp",
                   headline="Acme expands APAC data-centre footprint",
                   source="licensed_wire", published_at="2026-09-26T08:00:00Z", confidence=0.9),
        SignalItem(signal_type="regulation", entity="BetaSoft",
                   headline="Regulator fines BetaSoft over disclosures",
                   source="licensed_wire", published_at="2026-09-25T10:00:00Z", confidence=0.8),
    ]


def test_daily_briefing_assembles_scenario_a_content():
    briefing = compose_daily_briefing(
        AS_OF, "u_dev", metric_rows(),
        [deal(days_since_activity=30), deal(opportunity_id="opp_2")],
        signals(), today=date(2026, 9, 25))
    assert isinstance(briefing, DailyBriefing)
    kpis = {k.metric_id: k for k in briefing.kpis}
    assert kpis["attainment_pct"].value == 60.0 and kpis["attainment_pct"].unit == "percent"
    assert briefing.top_risks[0].opportunity_id == "opp_1"           # risk first
    assert len(briefing.market_signals) == 2                          # two sourced signals (§7.1)
    assert briefing.market_signals[0].source == "licensed_wire"       # evidence-bearing (§8.4)
    assert any(e.type == "metric_definition" for e in briefing.evidence)
    assert briefing.overdue_actions == 0                              # both deals have next steps


def test_briefing_greeting_differs_on_weekend():
    weekday = compose_daily_briefing(AS_OF, "u", metric_rows(), [], [], today=date(2026, 9, 25))
    weekend = compose_daily_briefing(AS_OF, "u", metric_rows(), [], [], today=date(2026, 9, 27))
    assert weekday.greeting != weekend.greeting


def test_no_deals_no_signals_still_valid_briefing():
    briefing = compose_daily_briefing(AS_OF, "u", metric_rows(), [], [], today=date(2026, 9, 25))
    assert briefing.top_risks == [] and briefing.market_signals == []
