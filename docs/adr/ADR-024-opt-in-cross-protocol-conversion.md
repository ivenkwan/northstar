# ADR-024: Cross-protocol conversion is opt-in and feature-matrix governed

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §12, §15.4, §15.5, §28.2 criterion 6 |

## Context

APISIX can accept Anthropic Messages on `/v1/messages` and translate to an OpenAI-compatible backend (and translate the response back), including streaming, system prompts, and tool use. This is useful for provider continuity during outages. But providers expose non-equivalent feature sets: naive conversion can silently discard provider-specific fields, altering tool behavior, stop reasons, or usage accounting without any client-visible signal.

## Decision

Cross-protocol conversion is **disabled by default** and may run only under a **named, explicitly activated model policy** (the `anthropic-emergency-conversion` policy of PRD §15.4, disabled unless incident policy activates it). Any conversion policy must:

- Authorize the source schema, destination provider, model, and supported feature subset.
- Pass contract tests covering text, system instructions, tool calls, tool results, stop reasons, usage accounting, and SSE.
- Fail requests using unsupported provider-specific fields with `422 AI_PROTOCOL_FEATURE_UNSUPPORTED` — fields are **never silently discarded**.
- Set `x-northstar-protocol-converted: true` on responses for trusted internal clients and audit records.

Activation and rollback of a conversion policy is a runbook operation (PRD §29).

## Consequences

**Positive:**

- Continuity option exists for provider outages without making lossy translation the default path.
- Every converted response is observable and auditable; unsupported semantics fail loudly instead of silently.
- Preserves ADR-022's guarantee for all default traffic.

**Negative / accepted costs:**

- A feature-compatibility matrix per provider pair must be maintained and tested; adding provider-specific features can invalidate a conversion policy.
- Incident-time activation adds operational procedure overhead and a distinct failure mode to rehearse.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Always-on conversion to a single backend | Silent semantic loss; violates the never-silently-discarded rule and ADR-022. |
| No conversion capability at all | Removes the provider-outage continuity option the PRD's resilience policies (§15.4) are designed to provide. |
| Client-side dual-protocol fallback | Pushes protocol competence and credential concerns into clients; violates trust boundaries. |

## Verification

- Gateway conformance goldens: conversion feature matrix, `422` rejection of unsupported fields, converted-response marker.
- Engineering acceptance criterion 6 (PRD §28.2): retry and fallback behavior bounded and tested, with no silent platform-key fallback.
- Runbook exercise for activation/rollback recorded in incident rehearsal.
