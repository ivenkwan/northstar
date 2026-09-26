from orchestrator.autonomy import (
    AutonomyLevel,
    AutonomyState,
    WorkflowMetrics,
    consider_promotion,
    govern,
    promotion_eligible,
    record_breach,
)


def healthy(n=200, lift=0.08) -> WorkflowMetrics:
    return WorkflowMetrics(evaluations=n, safety_failures=0, successes=int(n * 0.97),
                           measured_value_lift=lift)


def test_default_is_l0_confirm_each():
    state = AutonomyState(workflow_type="daily_briefing")
    d = govern(state, "compose_briefing", healthy())
    assert d.allowed_level is AutonomyLevel.L0 and d.requires_human  # start conservative


def test_high_impact_actions_never_autonomous():
    state = AutonomyState(workflow_type="anything", level=AutonomyLevel.L3)
    d = govern(state, "update_close_date", healthy())
    assert d.allowed_level is AutonomyLevel.L0 and "never_autonomous" in d.reason


def test_promotion_requires_evaluations_safety_success_and_powered_uplift():
    weak = healthy(n=50)
    ok, why = promotion_eligible(weak, AutonomyLevel.L1)
    assert not ok and "insufficient_evaluations" in why
    unsafe = healthy().model_copy(update={"safety_failures": 3})
    ok2, why2 = promotion_eligible(unsafe, AutonomyLevel.L1)
    assert not ok2 and "safety" in why2
    unlifted = healthy().model_copy(update={"measured_value_lift": None})
    ok3, why3 = promotion_eligible(unlifted, AutonomyLevel.L1)
    assert not ok3 and "no_powered_uplift" in why3  # §32: no autonomy without measured value


def test_l2_gate_requires_positive_experiment_backed_lift():
    ok, why = promotion_eligible(healthy(lift=0.01), AutonomyLevel.L2)
    assert not ok and "l2_gate" in why
    ok2, _ = promotion_eligible(healthy(lift=0.08), AutonomyLevel.L2)
    assert ok2


def test_breach_demotes_and_hard_breach_suspends():
    soft = record_breach(AutonomyState(workflow_type="w", level=AutonomyLevel.L2), "success_rate_dip")
    assert soft.level is AutonomyLevel.L0 and not soft.suspended
    hard = record_breach(AutonomyState(workflow_type="w", level=AutonomyLevel.L2), "injection_success")
    assert hard.level is AutonomyLevel.L0 and hard.suspended  # kill switch engaged


def test_suspended_workflow_never_acts_without_human():
    state = AutonomyState(workflow_type="w", level=AutonomyLevel.L2, suspended=True)
    d = govern(state, "compose_briefing", healthy())
    assert d.allowed_level is AutonomyLevel.L0 and d.requires_human


def test_promotion_path_l0_to_l2():
    state = AutonomyState(workflow_type="briefing")
    state = consider_promotion(state, healthy())
    assert state.level is AutonomyLevel.L1
    state = consider_promotion(state, healthy())
    assert state.level is AutonomyLevel.L2  # only with the powered-lift gate satisfied
