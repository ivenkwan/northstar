# Quarterly architecture & ADR review (Phase 3, todo.md)

Cadence: quarterly, chaired by the solution architect with security and product-owner attendance (§30 governance). Automation (`tools/adr_review.py`, golden test `test_repo_hygiene.py`) verifies inventory consistency before every session; the board works through this checklist.

## Verification matrix (run before the session)

| Check | How | Owner |
|---|---|---|
| ADR inventory consistent (indexed, valid statuses, dense numbering from 021) | `python tools/adr_review.py` — must exit 0 | Architect |
| ADRs' verification criteria still covered by golden/conformance suites | map each ADR's Verification section to current test ids | QA lead |
| Revisit triggers reviewed (AGE scale, lakehouse thresholds, ADR-029/030) | telemetry evidence attached | Platform |
| Open decisions from PRD review still tracked | docs/reviews/prd-v1-review.md resolution table | Architect |

## Decision items (each session)

1. Any ADR to supersede or extend (numbering continues from the highest existing)?
2. Any exception requests against Accepted ADRs (tri-party approval per §30)?
3. New architecture decisions accumulated during the quarter → new ADRs (Proposed).
4. Autonomy-level policy check: promotions/demotions recorded by `orchestrator/autonomy.py` reviewed (§33).
5. Residual-risk register (docs/security/threat-model.md) re-confirmed or updated.

## Sign-off

| Quarter | Attendees | ADRs changed | Notes |
|---|---|---|---|
| _(fill per session)_ | | | |
