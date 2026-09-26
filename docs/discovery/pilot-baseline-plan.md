# Pilot baseline plan — Phase 0

Selects the two pilot teams and defines the baseline measurements required by PRD §24.1 and §32 (controlled pilot, no speculative ROI).

## Pilot selection criteria

Two teams are selected to exercise the platform's hardest invariants (§23.2) rather than its happiest path:

| Criterion | Pilot 1 (target profile) | Pilot 2 (target profile) |
|---|---|---|
| Size | 8–12 sellers, 1–2 teams | 8–12 sellers, 1–2 teams |
| Org shape | Team inside a domain that belongs to **two groups** | Team in a single-group domain (control contrast for allocation) |
| CRM hygiene | Typical (some stale data) — real conditions | Similar; avoid the cleanest team |
| Manager engagement | Manager commits to weekly review rhythm | Same |
| Forecast practice | Submits commit/best-case categories | Different forecast maturity than Pilot 1 if possible |
| Data completeness | ≥80% opportunities with stage + close date + amount | Similar |

**[INPUT REQUIRED]:** sales-operations nominates the actual teams against these criteria; names and IDs recorded here once confirmed.

## Matched control teams

For each pilot, nominate one matched control team (same domain, comparable book of business, no product access). Matching variables: team size, average deal size, historical attainment variance, territory mix. Comparison is baseline-adjusted (difference-in-differences), never raw post-period comparison.

## Baseline measurements (captured before Phase 1 UAT starts)

Measured over the 4 weeks preceding pilot onboarding, per §25:

| Metric | Definition | Source | Collection |
|---|---|---|---|
| Pipeline-review prep time | Manager-reported hours/week preparing weekly review | Interview + calendar audit | Manual, once |
| Forecast variance | \|submitted commit − actual bookings\| / target, per period | CRM history | Query |
| Data completeness | % opportunities with amount, stage, close date, next step | CRM | Automated snapshot |
| Stale-deal rate | % open opportunities with no activity in 21 days | CRM + activity | Automated snapshot |
| Meeting prep time (sellers) | Self-reported minutes preparing for account meetings | Survey | Manual, once |
| Market-intel usage | Self-reported use of external news in account plans | Survey | Manual, once |

Automated snapshots repeat monthly during the pilot so trend, not just endpoints, is available. No employee-level performance metrics are derived from these — team-level only, per §11.3 (no hidden behavioral profiling).

## Pilot success thresholds (exit from Phase 2 decision point)

- ≥60% weekly active sellers in both pilots by week 6.
- Successful-answer rate ≥80% on the pilot question set (§23.2 retrieval/generation gate).
- No unresolved critical authorization or reconciliation error in the pilot window.
- Manager prep-time reduction directionally positive (informational; causality only claimed with control-team contrast).

## Ethics and transparency

Pilots receive the §11.3 notice: what data is processed, what AI does, what is logged, and the correction/appeal channel. Participation analytics are team-level; individual surveillance features are out of scope by policy.
