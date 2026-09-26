# ADR-036: Mobile charts use Victory Native XL with mandatory accessible data tables

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Mobile lead, product designer, accessibility |
| **PRD references** | §8.5, §10.2, §22, §17.5 |
| **Resolves** | PRD review open decision: mobile chart library |

## Context

Dashboard cards include bar, stacked bar, line, area, donut, waterfall, funnel, scatter, bubble, heat map, gauge, and bullet charts (§8.5), rendered on React Native under the strict-TypeScript standard (ADR-025), with WCAG 2.2 AA required for core flows — including "charts open in a focus view with accessible data table equivalent" (§10.2, §22). The chart library is a foundational Track B dependency that must be chosen before widget renderers are built (Sprint 3).

## Decision

**Victory Native XL** (built on React Native Skia and TypeScript) is the mobile chart runtime:

- First-class TypeScript types fit the ADR-025 toolchain; Skia rendering performs on low-end Android devices within §22 low-bandwidth/device-size scenarios.
- Covers the §8.5 card set; waterfall/funnel/gauge composites are built from its primitives inside the widget-union renderers (§17.5) rather than via a second library.
- Charts are always constructed from validated datasets (`packages/validation` schemas) — never from raw agent JSON (ADR-026).

**Mandatory accessibility rule:** every chart widget ships with a data-table alternative (the §17.5 `table` widget), reachable from the chart's focus view and via screen-reader labels on the chart card. A widget renderer without a table equivalent fails the accessibility quality gate (§23.4) — this is enforced by a render-checklist test, not convention.

## Consequences

**Positive:** one rendering stack for all cards; GPU-accelerated performance; strong types end-to-end; accessibility is structural, not optional.

**Negative / accepted costs:** Skia adds native build size; composite charts (waterfall, gauge) are our code to maintain; library upgrades ride the pinned-dependency policy (§17.2).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| react-native-svg + hand-rolled charts | Full control but we would own hit-testing, animation, and performance across the whole card set. |
| react-native-gifted-charts | Faster start, weaker typing and performance story at the strictness bar of ADR-025. |
| WebView charting (ECharts/Chart.js) | Escapes the typed boundary, adds webview accessibility and performance problems on mobile. |

## Verification

- §23.4 gate: accessibility/device-size scenarios pass, including screen-reader table alternatives for every chart widget kind.
- Widget-union exhaustiveness test includes renderer + table-alternative registration for every kind (§17.5 `never` check).
