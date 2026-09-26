"""Forecast model calibration gate (PRD §23.1 forecast layer, Phase 2).

Approved forecast models are allowed only after back-testing meets the
calibration threshold; until then every model-assisted number carries an
informational label. Gate metrics: Brier score (calibration), bias ratio
(systematic over/under-forecasting), and stability across periods.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

BRIER_THRESHOLD = 0.20     # target: Brier ≤ 0.20 on win-probability back-tests
BIAS_RATIO_MAX = 1.25      # |forecast/actual| within [0.8, 1.25]
BIAS_RATIO_MIN = 0.80
STABILITY_MAX_CV = 0.30    # coefficient of variation of period bias
MIN_BACKTEST_PERIODS = 4


class BacktestRow(BaseModel):
    period: str
    forecast_minor: int = Field(ge=0)
    actual_minor: int = Field(ge=0)
    win_probabilities: list[float] = Field(default_factory=list)  # predicted win probs for closed deals
    win_outcomes: list[int] = Field(default_factory=list)         # 1 = won, 0 = lost


class CalibrationReport(BaseModel):
    model_id: str
    brier: float | None
    bias_ratio: float | None
    stability_cv: float | None
    periods: int
    approved: bool
    label: str  # "certified" | "informational"
    failures: list[str] = Field(default_factory=list)


def brier_score(probs: list[float], outcomes: list[int]) -> float | None:
    if not probs or len(probs) != len(outcomes):
        return None
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes, strict=True)) / len(probs)


def bias_ratio(rows: list[BacktestRow]) -> float | None:
    total_f = sum(r.forecast_minor for r in rows)
    total_a = sum(r.actual_minor for r in rows)
    if total_a == 0:
        return None
    return total_f / total_a


def stability_cv(rows: list[BacktestRow]) -> float | None:
    per_period = [r.forecast_minor / r.actual_minor for r in rows if r.actual_minor > 0]
    if len(per_period) < 2:
        return None
    mean = sum(per_period) / len(per_period)
    var = sum((x - mean) ** 2 for x in per_period) / len(per_period)
    return (var ** 0.5) / mean if mean > 0 else None


def evaluate(model_id: str, rows: list[BacktestRow]) -> CalibrationReport:
    """The §23.1 gate: all thresholds met AND enough periods → certified; else informational."""
    failures: list[str] = []
    if len(rows) < MIN_BACKTEST_PERIODS:
        failures.append(f"insufficient_backtest_periods:{len(rows)}")

    probs = [p for r in rows for p in r.win_probabilities]
    outs = [o for r in rows for o in r.win_outcomes]
    brier = brier_score(probs, outs) if probs else None
    if brier is None or brier > BRIER_THRESHOLD:
        failures.append(f"calibration_brier:{brier}")

    ratio = bias_ratio(rows)
    if ratio is None or not (BIAS_RATIO_MIN <= ratio <= BIAS_RATIO_MAX):
        failures.append(f"bias_ratio:{ratio}")

    cv = stability_cv(rows)
    if cv is None or cv > STABILITY_MAX_CV:
        failures.append(f"stability_cv:{cv}")

    approved = not failures
    return CalibrationReport(
        model_id=model_id, brier=brier, bias_ratio=ratio, stability_cv=cv,
        periods=len(rows), approved=approved,
        label="certified" if approved else "informational",  # §23.1 informational label rule
        failures=failures,
    )
