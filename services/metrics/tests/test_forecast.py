import pytest
from metrics.forecast import BacktestRow, brier_score, evaluate


def row(period, forecast, actual, probs=None, outs=None):
    return BacktestRow(period=period, forecast_minor=forecast, actual_minor=actual,
                       win_probabilities=probs or [], win_outcomes=outs or [])


WELL_CALIBRATED = [0.8] * 10 + [0.3] * 10
MATCHING_OUTCOMES = [1] * 8 + [0] * 2 + [1] * 3 + [0] * 7  # ~80% and ~30% realized


def test_brier_score_perfect_and_chance():
    assert brier_score([1.0, 0.0], [1, 0]) == 0.0
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)
    assert brier_score([], []) is None


def test_well_calibrated_model_passes_gate():
    rows = [row(f"Q{i}", 1_000_000, 1_000_000, WELL_CALIBRATED, MATCHING_OUTCOMES) for i in range(6)]
    report = evaluate("forecast_v1", rows)
    assert report.approved
    assert report.label == "certified"
    assert report.brier < 0.20 and 0.8 <= report.bias_ratio <= 1.25


def test_biased_model_stays_informational():
    rows = [row(f"Q{i}", 2_000_000, 1_000_000, WELL_CALIBRATED, MATCHING_OUTCOMES) for i in range(6)]
    report = evaluate("forecast_v2", rows)
    assert not report.approved
    assert report.label == "informational"  # §23.1: no certification without passing back-test
    assert any(f.startswith("bias_ratio") for f in report.failures)


def test_poorly_calibrated_probabilities_fail():
    overconfident = [0.95] * 20
    outcomes = [1] * 10 + [0] * 10  # realized 50%, predicted 95% → terrible Brier
    rows = [row(f"Q{i}", 1_000_000, 1_000_000, overconfident, outcomes) for i in range(6)]
    report = evaluate("forecast_v3", rows)
    assert not report.approved and any(f.startswith("calibration_brier") for f in report.failures)


def test_too_few_periods_fails_even_with_good_numbers():
    rows = [row("Q1", 1_000_000, 1_000_000, [0.5, 0.5], [1, 0])]
    report = evaluate("forecast_v4", rows)
    assert not report.approved
    assert report.failures[0].startswith("insufficient_backtest_periods")
