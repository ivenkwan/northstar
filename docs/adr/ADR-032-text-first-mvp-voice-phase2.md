# ADR-032: Text-first MVP; voice input deferred to Phase 2

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Product owner, solution architect, security |
| **PRD references** | §8.1 (CONV-01), §10.2 |
| **Resolves** | PRD review finding F-03 |

## Context

CONV-01 made "text and voice input" a Must for MVP, but Part II specifies no speech-to-text pipeline: no provider, no consent flow, no latency budget, no data-residency treatment for audio (F-03). Voice also multiplies privacy surface (employee and customer voices, possible third-party STT processing) inside a PDPO-aligned deployment (§11.3). Building it without an architecture would violate the PRD's own governance rules.

## Decision

**Voice input is reclassified from Must to Should and deferred to Phase 2.** The MVP conversational assistant accepts text only (multi-turn context remains a Must). PRD v3.2 amends CONV-01 accordingly. When voice ships in Phase 2, it follows this architecture (to be finalized in its own ADR):

- STT runs as a provider behind APISIX — either the enterprise's approved STT service or a cloud provider reached through the same BYOK/budget/header-sanitization controls as LLM providers (§15).
- The transcript is displayed for user correction before submission (§10.2); nothing is sent to the orchestrator until the user confirms.
- Audio is processed transiently (streamed, not persisted) unless governance approves retention; transcripts inherit the conversation's audit and retention policy.
- NFR: transcript visible within 2 seconds for a 15-second utterance (target, to be validated).

## Consequences

**Positive:** MVP loses no analytic capability (all components are text-driven); the STT decision gets a proper architecture with privacy review instead of an accidental one; schedule risk reduced (F-10).

**Negative / accepted costs:** CONV-01's voice acceptance condition moves to Phase 2; users who would prefer voice wait; Phase 2 scope grows by one ADR plus provider onboarding.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| On-device STT (e.g. OS-level dictation) | Requires no platform work, but quality and language coverage vary by device and cannot meet a governed NFR; acceptable as an accessibility fallback, not as the product feature. |
| Ship voice with a cloud STT in MVP | Adds an unreviewed provider, consent, and residency path inside the MVP window; exactly the gap F-03 flags. |

## Verification

- PRD v3.2 CONV-01 text says "text (Must); voice (Should, Phase 2)".
- Phase 2 entry checklist includes the STT ADR, DPIA update for audio processing, and consent copy.
