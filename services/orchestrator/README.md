# services/orchestrator — Agent orchestrator (LangGraph)

Deterministic workflow around probabilistic models (PRD §9). Hosts the agent roster and the 12-step orchestration pattern (PRD §9.2): authenticate → classify intent/risk → resolve scope → plan → authorize → retrieve via semantic/record APIs only → validate freshness → generate typed components → attach citations → recheck output → confirm writes → record immutable trace.

## Agent roster (PRD §9.1)

Orchestrator, Identity & Scope, Sales Analytics, Opportunity, Target & Forecast, Market Intelligence, Dashboard Composer, Action, Data Quality, Governance.

## Hard rules

- No direct LLM database access; queries go through the semantic layer or record APIs (PRD §9.2 step 6).
- Agents request logical capabilities (e.g. `reasoning.standard`), never endpoints or credentials (PRD §13.1 agent boundary).
- Retrieved content (CRM notes, news, documents) is data, never instructions (PRD §8.4, §11.2).
- State: session memory (short-lived, encrypted), user preference memory (explicit, editable), enterprise knowledge (governed); no hidden behavioral memory (PRD §9.3).

## Build track

Phase 1, Tracks D/E/G — see `todo.md`.
