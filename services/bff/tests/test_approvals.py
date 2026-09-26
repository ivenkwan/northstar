from bff.approvals import ApprovalWorkflow, evaluate_approval


def test_low_impact_needs_confirmation_only():
    d = evaluate_approval.__wrapped__ if False else None  # noqa: F841 — keep import surface simple
    from bff.approvals import ApprovalRequest

    req = ApprovalRequest(action_id="a", action_type="create_task", actor="u1")
    decision = evaluate_approval(req)
    assert decision.approved and decision.required == ["explicit_confirmation"]


def test_medium_impact_requires_step_up():
    from bff.approvals import ApprovalRequest

    no_step_up = ApprovalRequest(action_id="a", action_type="add_note", actor="u1")
    assert not evaluate_approval(no_step_up).approved
    with_step_up = ApprovalRequest(action_id="a", action_type="add_note", actor="u1", step_up_auth=True)
    d = evaluate_approval(with_step_up)
    assert d.approved and "step_up_auth" in d.required


def test_high_impact_requires_step_up_and_manager():
    from bff.approvals import ApprovalRequest

    req = ApprovalRequest(action_id="a", action_type="update_close_date", actor="u1",
                          step_up_auth=True, manager_approved=True)
    d = evaluate_approval(req)
    assert d.approved and {"step_up_auth", "manager_approval"} <= set(d.required)


def test_workflow_state_machine_blocks_until_gates_met():
    wf = ApprovalWorkflow()
    action_id = wf.open("update_forecast_category", "u_seller", manager="u_manager")
    assert not wf.try_execute(action_id).approved           # no gates yet
    wf.step_up(action_id)
    assert not wf.try_execute(action_id).approved           # still missing manager
    wf.manager_approve(action_id, "u_manager")
    assert wf.try_execute(action_id).approved
    assert wf.try_execute(action_id).reason == "unknown_action"  # consumed; no double execution
    events = [e["event"] for e in wf.audit]
    assert events == ["opened", "step_up_auth", "manager_approved", "executed"]  # full audit trail
