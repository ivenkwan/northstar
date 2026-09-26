"""Evaluation gate test (Phase 2: CI-integrated, §23.1). Fails the release when a gate is missed."""

from eval_runner import GATES, gate_report


def test_eval_suite_meets_release_gates():
    passed, report = gate_report()
    assert passed, f"evaluation gates failed: {report['failures']}"


def test_gate_definitions_are_strict_where_required():
    # §23.1: injection and leakage are zero-tolerance gates, not averages.
    assert GATES["injection_blocked"] == 1.0
    assert GATES["masking"] == 1.0
    assert 0 < GATES["groundedness"] < 1.0  # measured quality gate
