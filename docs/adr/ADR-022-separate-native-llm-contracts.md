# ADR-022: OpenAI Chat Completions and Anthropic Messages remain separate native contracts

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §12, §15.2, §15.5, §17.6, §28.2 criterion 2 |

## Context

Two provider families must be served: OpenAI Chat Completions and Anthropic Messages, including streaming SSE with different event models and terminators, different tool-use representations, and provider-specific fields. A single "normalized" LLM interface is attractive for client simplicity but silently discards or misrepresents provider-specific semantics (content blocks, stop reasons, beta headers, usage accounting), and normalization at the client forces every consumer to track the union of both protocols.

## Decision

The gateway publishes **two first-class, versioned native interfaces** rather than one normalized schema:

- `POST /ai/openai/v1/chat/completions` — OpenAI Chat Completions request/response/SSE semantics, preserving field names, SSE framing, and the `[DONE]` terminator.
- `POST /ai/anthropic/v1/messages` — Anthropic Messages pass-through (route ends in `/v1/messages`), preserving content blocks, tool-use blocks, stop reasons, and native SSE events through `message_stop`.

No default conversion occurs in either direction; any translation is the explicit, opt-in policy of ADR-024. TypeScript maintains **separate** transport types for the two protocols (PRD §17.6); merging them into one broad optional-field interface is prohibited. These routes are for trusted platform workloads — the mobile app consumes the product's typed conversation API, never a provider-native route (PRD §13.1).

## Consequences

**Positive:**

- Provider semantics are preserved end-to-end; no silent field loss; streaming behaves exactly as each provider documents.
- Contract tests can assert byte-level protocol fidelity per provider instead of a lossy intersection.
- Protocol choice stays an operational (routing) concern, not a client-code concern.

**Negative / accepted costs:**

- Two contracts to test, document, and version; golden suites must cover both protocols' non-streaming, streaming, and tool-call matrices (§23.3).
- Server-side rules must reject provider-incompatible model identifiers before upstream dispatch and pin an approved `anthropic-version`.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| One normalized gateway schema (union interface) | Loses provider-specific fields and SSE event fidelity; PRD §15.5 explicitly requires field preservation and §17.6 prohibits the merged optional-field interface. |
| OpenAI-compatible facade for all providers | Would force Anthropic traffic through lossy conversion by default — exactly what PRD §12 makes opt-in only (ADR-024). |
| Client-side per-provider SDKs | Pushes credential and protocol concerns into clients; violates trust boundaries (§13.1). |

## Verification

- Engineering acceptance criterion 2 (PRD §28.2): native Anthropic traffic preserves content blocks and SSE events without conversion.
- Gateway conformance goldens: SSE event order through terminators, tool calls/results for both protocols, rejection of unsupported beta headers.
- Static check: no TypeScript type merges OpenAI and Anthropic wire contracts (PRD §17.6).
