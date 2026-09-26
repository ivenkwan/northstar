# ADR-028: Product APIs are versioned under `/api/v1`

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §15.2, §16.5, §19.1–§19.2 |
| **Resolves** | PRD review finding F-01 |

## Context

The PRD used two incompatible conventions for product APIs: the gateway route table (§15.2) declared `/api/v2/*` while the core endpoint list (§19.2) used `/v1/...`, and BYOK admin APIs (§16.5) used `/api/v2/admin/...`. No v1 product API has ever shipped, so starting at v2 has no compatibility basis. The first OpenAPI document cannot be authored until one convention is fixed (F-01, blocking).

## Decision

All product APIs are served under a single versioned prefix through APISIX:

- **`/api/v1/...`** — product APIs for mobile and admin clients (e.g. `/api/v1/conversations`, `/api/v1/admin/byok/credentials`).
- **`/ai/openai/v1/chat/completions`** and **`/ai/anthropic/v1/messages`** — unchanged native LLM routes (ADR-022).
- **`/internal/ai/capabilities/{capability}`** — unchanged server-side-only route.

Versioning is in the path prefix (`/api/v1`), raised only for breaking changes per §19.1 backward-compatibility rules. The PRD (v3.2) is amended accordingly; §15.2, §16.5, and §19.2 now consistently use `/api/v1`.

## Consequences

**Positive:** one convention across gateway routes, OpenAPI documents, generated TypeScript clients, and contract tests; version bump semantics are explicit.

**Negative / accepted costs:** `/api/v1` must not be confused with provider-native `/v1/...` paths inside `/ai/*` routes — docs and lint rules must treat the prefixes as distinct roots.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Keep `/api/v2` | Implies a v1 that never existed; confuses contract history. |
| Bare `/v1/...` (no `/api` root) | Collides visually with provider-native `/v1` route fragments; weaker gateway routing partitioning. |

## Verification

Spectral lint rule: every product operation path starts with `/api/v1/`; gateway route table conformance test asserts no other public product prefix.
