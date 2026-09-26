"""Next-best-action experimentation (Phase 3, §24.4; §32 no-causality-without-experiments).

Deterministic assignment (salted hash — stable per user, no drift mid-experiment),
exposure/outcome capture, and uplift analysis with a power gate: results below
the minimum sample size are reported as `underpowered`, never as uplift.
"""

from __future__ import annotations

import hashlib
import math

from pydantic import BaseModel, Field


class ExperimentSpec(BaseModel):
    experiment_id: str
    variants: list[str] = Field(min_length=2)
    min_samples_per_variant: int = Field(default=200, ge=1)
    owner: str = "product"


def assign(spec: ExperimentSpec, user_id: str) -> str:
    """Stable assignment: same experiment+user → same variant, forever."""
    digest = hashlib.sha256(f"{spec.experiment_id}:{user_id}".encode()).digest()
    bucket = int.from_bytes(digest[:8], "big") % len(spec.variants)
    return spec.variants[bucket]


class VariantOutcome(BaseModel):
    variant: str
    exposures: int = 0
    successes: int = 0


class UpliftReport(BaseModel):
    experiment_id: str
    powered: bool
    baseline: str
    treatment: str | None = None
    abs_uplift: float | None = None
    rel_uplift: float | None = None
    z_score: float | None = None
    note: str


def _two_proportion_z(c_exposed: int, c_success: int, t_exposed: int, t_success: int) -> float | None:
    if c_exposed == 0 or t_exposed == 0:
        return None
    p_c = c_success / c_exposed
    p_t = t_success / t_exposed
    p_pool = (c_success + t_success) / (c_exposed + t_exposed)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / c_exposed + 1 / t_exposed))
    if se == 0:
        return None
    return (p_t - p_c) / se


def analyze(spec: ExperimentSpec, outcomes: list[VariantOutcome], baseline: str) -> UpliftReport:
    by_variant = {o.variant: o for o in outcomes}
    base = by_variant.get(baseline)
    if base is None or base.exposures == 0:
        return UpliftReport(experiment_id=spec.experiment_id, powered=False, baseline=baseline,
                            note="baseline variant has no exposures")
    treatments = [o for o in outcomes if o.variant != baseline]
    powered = (base.exposures >= spec.min_samples_per_variant
               and all(t.exposures >= spec.min_samples_per_variant for t in treatments))
    if not treatments:
        return UpliftReport(experiment_id=spec.experiment_id, powered=False, baseline=baseline,
                            note="no treatment variant")
    if not powered:
        # §32 discipline: underpowered numbers are never reported as uplift.
        return UpliftReport(experiment_id=spec.experiment_id, powered=False, baseline=baseline,
                            note=f"underpowered: min {spec.min_samples_per_variant} exposures/variant")
    t = max(treatments, key=lambda o: o.successes / max(o.exposures, 1))
    p_c = base.successes / base.exposures
    p_t = t.successes / t.exposures
    return UpliftReport(
        experiment_id=spec.experiment_id, powered=True, baseline=baseline, treatment=t.variant,
        abs_uplift=p_t - p_c,
        rel_uplift=(p_t - p_c) / p_c if p_c > 0 else None,
        z_score=_two_proportion_z(base.exposures, base.successes, t.exposures, t.successes),
        note="measured_uplift (experiment-backed; z is two-proportion normal approx)")
