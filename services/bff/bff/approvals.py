"""Expanded controlled actions (Phase 2, §8.7): step-up authentication and
manager approval for high-impact actions, with audit trail and idempotent
execution receipts (Scenario E).
"""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel


class Impact(str, Enum):
    LOW = "low"            # task creation, topic subscription
    MEDIUM = "medium"      # note, next step
    HIGH = "high"          # close date, probability, forecast category


ACTION_IMPACT: dict[str, Impact] = {
    "create_task": Impact.LOW,
    "add_note": Impact.MEDIUM,
    "update_next_step": Impact.MEDIUM,
    "update_close_date": Impact.HIGH,
    "update_probability": Impact.HIGH,
    "update_forecast_category": Impact.HIGH,
}


class ApprovalRequest(BaseModel):
    action_id: str
    action_type: str
    actor: str
    manager: str | None = None
    step_up_auth: bool = False       # fresh strong auth performed in this session
    manager_approved: bool = False


class ApprovalDecision(BaseModel):
    approved: bool
    required: list[str]  # which gates applied
    reason: str


def evaluate_approval(req: ApprovalRequest) -> ApprovalDecision:
    """LOW: confirm only. MEDIUM: step-up. HIGH: step-up + manager approval (§8.7)."""
    impact = ACTION_IMPACT.get(req.action_type)
    if impact is None:
        return ApprovalDecision(approved=False, required=[], reason="unknown_action_type")
    required: list[str] = ["explicit_confirmation"]
    if impact is not Impact.LOW:
        required.append("step_up_auth")
    if impact is Impact.HIGH:
        required.append("manager_approval")
    ok = True
    if impact is not Impact.LOW and not req.step_up_auth:
        ok = False
    if impact is Impact.HIGH and not req.manager_approved:
        ok = False
    return ApprovalDecision(approved=ok, required=required,
                            reason="ok" if ok else "missing_required_gates")


class ApprovalWorkflow:
    """State machine for in-flight approvals: requested → step_up → manager → executed."""

    def __init__(self) -> None:
        self.pending: dict[str, ApprovalRequest] = {}
        self.audit: list[dict] = []

    def open(self, action_type: str, actor: str, manager: str | None = None) -> str:
        action_id = f"act_{uuid.uuid4().hex[:10]}"
        self.pending[action_id] = ApprovalRequest(action_id=action_id, action_type=action_type,
                                                  actor=actor, manager=manager)
        self.audit.append({"action_id": action_id, "event": "opened", "actor": actor})
        return action_id

    def step_up(self, action_id: str) -> None:
        req = self.pending.get(action_id)
        if req is not None:
            req.step_up_auth = True
            self.audit.append({"action_id": action_id, "event": "step_up_auth"})

    def manager_approve(self, action_id: str, manager: str) -> None:
        req = self.pending.get(action_id)
        if req is not None:
            req.manager_approved = True
            req.manager = manager
            self.audit.append({"action_id": action_id, "event": "manager_approved", "manager": manager})

    def try_execute(self, action_id: str) -> ApprovalDecision:
        req = self.pending.get(action_id)
        if req is None:
            return ApprovalDecision(approved=False, required=[], reason="unknown_action")
        decision = evaluate_approval(req)
        if decision.approved:
            self.audit.append({"action_id": action_id, "event": "executed"})
            del self.pending[action_id]
        return decision
