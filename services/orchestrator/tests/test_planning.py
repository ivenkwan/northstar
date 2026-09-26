import pytest
from orchestrator.planning import (
    AccountPlan,
    PartnerInvolvement,
    PlanObjective,
    merge_plan_versions,
    objective_progress,
    partner_compliance,
)


def plan(**kw) -> AccountPlan:
    defaults = dict(plan_id="p1", account_id="acct_9", owner_id="s1", period="FY28-Q1")
    defaults.update(kw)
    return AccountPlan(**defaults)


def test_objective_progress_with_target_guard():
    p = plan(objectives=[
        PlanObjective(objective_id="o1", description="expand", target_minor=1_000_000, booked_minor=400_000),
        PlanObjective(objective_id="o2", description="renew", target_minor=0, booked_minor=50_000),
    ])
    rows = {r["objective_id"]: r for r in objective_progress(p)}
    assert rows["o1"]["attainment_pct"] == 40.0
    assert rows["o1"]["gap_minor"] == 600_000
    assert rows["o2"]["attainment_pct"] is None  # no target → suppressed, not zero


def test_cosell_without_registration_flagged_not_silent():
    p = plan(partners=[
        PartnerInvolvement(partner_id="prt_a", role="co-sell", registration_id=None,
                           attached_opportunities=["opp1", "opp2"]),
        PartnerInvolvement(partner_id="prt_b", role="referral", registration_id=None,
                           attached_opportunities=["opp3"]),
    ])
    reports = {r.partner_id: r for r in partner_compliance(p)}
    assert reports["prt_a"].unregistered_deals == ["opp1", "opp2"]  # co-sell needs registration
    assert reports["prt_b"].unregistered_deals == []                 # referral does not


def test_merge_bumps_version_and_preserves_account_binding():
    current = plan()
    edited = plan(plan_id="p1", version=1,
                  objectives=[PlanObjective(objective_id="o1", description="new", target_minor=5)])
    merged = merge_plan_versions(current, edited)
    assert merged.version == 2 and merged.account_id == "acct_9"


def test_cannot_merge_across_accounts():
    with pytest.raises(ValueError):
        merge_plan_versions(plan(), plan(account_id="acct_other"))
