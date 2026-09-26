import pytest
from orchestrator.experiments import ExperimentSpec, VariantOutcome, analyze, assign


def spec() -> ExperimentSpec:
    return ExperimentSpec(experiment_id="nba_v1", variants=["control", "treatment"], min_samples_per_variant=100)


def test_assignment_is_deterministic_and_distributed():
    s = spec()
    assert assign(s, "u1") == assign(s, "u1")  # stable forever
    variants = {assign(s, f"u{i}") for i in range(200)}
    assert variants == {"control", "treatment"}  # both arms populated
    assert assign(s, "u1") != assign(ExperimentSpec(experiment_id="nba_v2", variants=["a", "b"]), "u1")  # salted


def outcomes(control_n, control_s, treat_n, treat_s):
    return [VariantOutcome(variant="control", exposures=control_n, successes=control_s),
            VariantOutcome(variant="treatment", exposures=treat_n, successes=treat_s)]


def test_underpowered_results_never_reported_as_uplift():
    report = analyze(spec(), outcomes(50, 10, 50, 15), "control")
    assert not report.powered
    assert report.abs_uplift is None
    assert "underpowered" in report.note  # §32: no causality claims without a powered experiment


def test_powered_uplift_reported_with_stats():
    report = analyze(spec(), outcomes(1000, 200, 1000, 260), "control")
    assert report.powered and report.treatment == "treatment"
    assert report.abs_uplift == pytest.approx(0.06)
    assert report.rel_uplift == pytest.approx(0.30)
    assert report.z_score is not None and report.z_score > 2.5  # ~2.8σ here


def test_negative_uplift_reported_honestly():
    report = analyze(spec(), outcomes(1000, 300, 1000, 270), "control")
    assert report.powered
    assert report.abs_uplift < 0  # losers are reported as losers


def test_missing_baseline_is_not_an_error_report():
    report = analyze(spec(), [VariantOutcome(variant="treatment", exposures=100, successes=10)], "control")
    assert not report.powered and "no exposures" in report.note
