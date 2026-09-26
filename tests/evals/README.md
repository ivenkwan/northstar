# tests/evals — AI evaluation datasets and harnesses

Evaluation layers with release gates (PRD §23.1): data, retrieval, analytics, generation, authorization, agent safety, forecast, UX.

## Planned contents

- Curated retrieval/generation test sets by persona and scope (groundedness, citation correctness, abstention).
- Prompt-injection, malicious-document, excessive-agency, and exfiltration adversarial cases mapped to OWASP LLM/agentic references (PRD §11.2).
- Forecast calibration/back-test harness (informational label until threshold met — PRD §23.1).
- Datasets anonymized or pseudonymized per PCPD guidance (PRD §11.3).
- Feedback-loop integration: thumbs-up/down and structured corrections linked to response, retrieval set, prompt/model version (PRD CONV-09).

## Build track

Phase 1, Track H — see `todo.md`.

## AI-assisted development

ZCode is the standard AI coding workbench for this component. Before editing, follow the repository root [`AGENTS.md`](../../AGENTS.md) and [`docs/development/zcode-toolchain.md`](../../docs/development/zcode-toolchain.md); use the nearest PRD sections and ADRs as authoritative constraints. ZCode-generated changes require human diff review and the same deterministic checks and CI gates as human-authored changes.
