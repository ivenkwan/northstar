# UX IA blueprint — Phase 0 wireframe baseline

Wireframe-level blueprint for the five-destination information architecture (PRD §10.1) and the four core journeys (§7). This is the Phase 0 "UX prototype" artifact: screen inventory, layout skeletons, and interaction rules precise enough to build against in Track B; high-fidelity visual design is the product designer's Phase 0/1 deliverable.

## Navigation shell

```
┌──────────────────────────────────────┐
│  header: role chip · as-of · alert   │
│ ┌──────────────────────────────────┐ │
│ │            screen                │ │
│ └──────────────────────────────────┘ │
│ [Today] [Ask] [Dash] [Pipe] [Intel]  │  ← thumb-reachable tab bar
└──────────────────────────────────────┘
```

All primary actions sit in the bottom 60% of the viewport (§10.2 one-handed rule). Every analytical card exposes an overflow: *Explain · Evidence · As-of · Feedback*.

## 1 — Today (morning briefing, §7.1)

```
Today                                    Tue 26 Sep · data as-of 09:00
┌───────────────┬───────────────┐
│ Attainment %  │ Forecast gap  │  ← KPI pair, tap → Ask pre-scoped
│ 62%  of Q3    │ −HK$1.2M      │
├───────────────┴───────────────┤
│ Top 3 risks                   │  ← risk cards: deal, why, next step
│ ▸ ACME renewal slipped …      │
├───────────────────────────────┤
│ Meetings today (2)            │  ← tap → meeting prep brief
├───────────────────────────────┤
│ Overdue actions (3)           │
├───────────────────────────────┤
│ Market signals (2) ▸ sourced  │  ← evidence chips only
└───────────────────────────────┘
```

Rules: every number carries as-of + metric chip (`attainment_pct v3`); risk cards deep-link to opportunity brief; nothing here requires typing.

## 2 — Ask (conversational assistant)

- Input bar with suggested prompts (role-aware), session history.
- Responses render as component stacks: narrative → chart/table → evidence chips → suggested actions (§19.3 schema).
- Scope bar above input shows active scope/filters/currency, always editable ("My pipeline · Q3 · HKD ▾").
- Long-press any component → *Explain this* (CONV-06): formula, inputs, assumptions.
- Actions with `requires_confirmation` open a bottom-sheet preview (old/new values, impact) with explicit Confirm/Cancel — never a chat-typed "yes".

## 3 — Dashboard (§7.4)

- Grid of saved dashboards; shared dashboards badged with owner + scope.
- Card layout per declarative JSON (§10.3): 2-column mobile grid; drag/reorder with haptic snap; card resize limited to 1×1 / 2×1 / 2×2.
- Dashboard edit mode = conversation ("add coverage by rep") + direct touch; composer previews filter/scope changes before save (Scenario D).
- Every chart card has a table-alternative toggle in focus view (ADR-036 accessibility rule).

## 4 — Pipeline

- Searchable list (deal name, account, owner) with saved filters; chip row: stage · period · category · owner.
- List rows: amount, stage, close date, health indicator dot (transparent composition — tap shows factors).
- Detail (opportunity brief, §8.2): summary → risks → movement history → activities → products/quotes → evidence; drill-through honors record permissions (CONV-05 masking).

## 5 — Intelligence

- Followed topics (industry, company, competitor, regulation); signal feed clustered by story (§8.4).
- Signal card: taxonomy badge, why-it-matters line, affected accounts/opportunities chips, source + publisher + time, confidence.
- Strict visual separation: **Sourced facts** (evidence-styled) vs **AI interpretation** (labeled), per §7.3 step 4.

## Journey wiring (acceptance anchors)

| Journey | Entry | Key screens | Golden anchor |
|---|---|---|---|
| Morning briefing | Today push/open | Today → Ask (why down?) → opportunity brief → confirm task | §28.1 Scenario A/E |
| Manager review | Ask: "coverage by rep Q4" | Ask → chart+matrix+table → save view → schedule alert | Scenario D |
| Domain intelligence | Intelligence feed | Signal → affected opportunities → brief | Scenario C |
| Dashboard by conversation | Ask: "build me…" | Composer preview → confirm → saved dashboard | Scenario D |

## Accessibility requirements (built into Track B gates)

WCAG 2.2 AA: 4.5:1 contrast, 44pt targets, dynamic type to 200%, screen-reader labels on all KPI/chart cards, table equivalents for charts (§22, ADR-036), no color-only encoding (risk dots always paired with labels).
