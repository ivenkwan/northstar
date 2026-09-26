# data/semantic-layer — Governed metric catalog

Versioned definitions for every certified measure, dimension, fiscal calendar, currency treatment, and inclusion rule (PRD §8.3, §14.2). `services/metrics` executes these definitions; the UI exposes formula/version/lineage from them (PRD §27 "Semantic metrics" exit criterion).

## Governed measures (PRD §8.3)

`Actual`, `Target`, `Attainment %`, `Remaining Target`, `Weighted Pipeline`, `Coverage`, `Forecast Gap`, `Run Rate`, `Required Run Rate` — plus pipeline analytics: stage conversion, velocity, aging, staleness, movements, and deal-health indicators (PRD §8.2).

## Each definition records

Formula, grain, dimensions, fiscal calendar, currency treatment, stage mapping, probability source, inclusion rules, null/late-arriving-data behavior, owner, version, certification status.

## Open item

FX rate reference dataset and as-of policy (review finding F-08).

## Build track

Phase 0 (certified metric validation) → Phase 1, Track C — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
