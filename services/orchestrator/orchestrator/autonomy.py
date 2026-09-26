"""Progressive autonomy governor (Phase 3, §33: "controlled multi-agent workflow
automation with progressive autonomy based on measured safety and value").

Autonomy levels per workflow type:
  L0 CONFIRM_EACH   — human confirms every step (default)
  L1 CONFIRM_BATCH  — human confirms the plan; steps run, results reviewed
  L2 SUPERVISED     — runs autonomously within rate limits; sampled human review
  L3 EXCEPTION_ONLY — autonomous; escalates only on anomaly

Promotion requires BOTH safety and value metrics over a rolling window to clear
thresholds; any hard breach (unauthorized action, injection success, write
rollback) triggers immediate demotion to L0 and, on kill-switch, suspension.
High-impact action types can never exceed L0 (§8.7).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class AutonomyLevel(int, Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3


PROMOTION_THRESHOLDS = {
    # measured over the rolling window before promotion is even considered (§33)
    "min_evaluations": 100,
    "min_safety_score": 0.995,     # zero critical safety failures over the window
    "min_success_rate": 0.95,
    "min_value_lift": 0.0,         # no negative value; positive value required for L2+
    "min_value_lift_for_l2": 0.05, # measured, experiment-backed uplift (experiments.py)
}

NEVER_AUTONOMOUS_ACTION_TYPES = frozenset({"update_close_date", "update_probability",
                                           "update_forecast_category", "bulk_update", "external_message"})


class WorkflowMetrics(BaseModel):
    evaluations: int = 0
    safety_failures: int = 0
    successes: int = 0
    measured_value_lift: float | None = None  # from a POWERED experiment only


class AutonomyState(BaseModel):
    workflow_type: str
    level: AutonomyLevel = AutonomyLevel.L0
    suspended: bool = False
    demotion_reason: str | None = None


class GovernorDecision(BaseModel):
    allowed_level: AutonomyLevel
    reason: str
    requires_human: bool


def promotion_eligible(metrics: WorkflowMetrics, target: AutonomyLevel) -> tuple[bool, str]:
    if metrics.evaluations < PROMOTION_THRESHOLDS["min_evaluations"]:
        return False, f"insufficient_evaluations:{metrics.evaluations}"
    safety = 1 - (metrics.safety_failures / max(metrics.evaluations, 1))
    if safety < PROMOTION_THRESHOLDS["min_safety_score"]:
        return False, f"safety_score_too_low:{safety:.4f}"
    if metrics.successes / max(metrics.evaluations, 1) < PROMOTION_THRESHOLDS["min_success_rate"]:
        return False, "success_rate_too_low"
    if metrics.measured_value_lift is None:
        return False, "no_powered_uplift_measurement"  # §32: no autonomy without measured value
    if target >= AutonomyLevel.L2 and metrics.measured_value_lift < PROMOTION_THRESHOLDS["min_value_lift_for_l2"]:
        return False, "value_lift_below_l2_gate"
    return True, "ok"


def govern(state: AutonomyState, action_type: str, metrics: WorkflowMetrics) -> GovernorDecision:
    if state.suspended:
        return GovernorDecision(allowed_level=AutonomyLevel.L0, reason="kill_switch_suspended",
                                requires_human=True)
    if action_type in NEVER_AUTONOMOUS_ACTION_TYPES:
        return GovernorDecision(allowed_level=AutonomyLevel.L0, reason="action_type_never_autonomous",
                                requires_human=True)  # §8.7: high-impact stays human-confirmed
    return GovernorDecision(allowed_level=state.level, reason="ok",
                            requires_human=state.level is AutonomyLevel.L0)


def record_breach(state: AutonomyState, kind: str) -> AutonomyState:
    """Any hard breach → immediate L0; safety-critical kinds → suspension (kill switch)."""
    state.level = AutonomyLevel.L0
    state.demotion_reason = kind
    if kind in ("unauthorized_action", "injection_success", "data_leak"):
        state.suspended = True
    return state


def consider_promotion(state: AutonomyState, metrics: WorkflowMetrics) -> AutonomyState:
    target = AutonomyLevel(state.level + 1) if state.level < AutonomyLevel.L3 else AutonomyLevel.L3
    eligible, _ = promotion_eligible(metrics, target)
    if eligible and not state.suspended:
        state.level = target
    return state
