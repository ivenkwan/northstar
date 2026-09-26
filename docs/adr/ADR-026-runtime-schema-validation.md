# ADR-026: Dynamic agent/dashboard/graph payloads require runtime schema validation

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §8.5, §17.1, §17.4–§17.5, §18, §28.2 criteria 8–10 |

## Context

Three classes of payload arrive shaped at runtime rather than at compile time: AI-generated conversation components and events, dashboard definitions authored by the Dashboard Composer from natural language, and knowledge-graph query results. Compile-time types cannot protect against malformed, adversarial, or forward-incompatible payloads crossing these boundaries — and PRD §17.3 explicitly prohibits rendering unvalidated JSON from agents, dashboards, or graph services.

## Decision

Every untrusted dynamic payload is validated at runtime with **Zod schemas** maintained in `packages/validation`, then narrowed to discriminated-union domain types before use:

- **Dashboard definitions** produced by the Dashboard Composer must pass their Zod schema **and server-side authorization** (metric compatibility, chart suitability, allowed dimensions, query cost — §8.5) before reaching a renderer; widgets are a discriminated union with exhaustive `never`-checked renderer switches (§17.5).
- **Conversation components/events** validate against the UI component schema (CONV-03) with exhaustive event handling for any diagnostic provider-native stream parsers (§17.6).
- **Graph payloads** validate against typed `GraphNode`/`GraphEdge` contracts; agent-generated graph queries are compiled from a typed intermediate representation — raw Cypher, Gremlin, or SQL from a model is never executed (§18).
- Unknown data follows the approved exception pattern: accept `unknown`, validate with a schema, narrow to a domain type (§17.3). Malformed and forward-compatible payload cases are tested (§23.4).

## Consequences

**Positive:**

- Malicious or malformed AI output fails loudly at the boundary instead of crashing renderers or leaking fields; prompt-injection payloads cannot smuggle structure past validation.
- Server-side dashboard validation enforces governed metrics and authorization even for conversational authoring (acceptance Scenario D, §28.1).
- Schemas double as living documentation of the component/widget/event contracts shared by web and mobile.

**Negative / accepted costs:**

- Two representations to keep aligned (Zod schema and discriminated type); mitigated by deriving types from schemas (`z.infer`) where tooling permits.
- Validation cost on every streamed event; bounded by keeping schemas structural and payloads bounded (§18 bounded subgraphs).
- Schema versioning must handle forward-compatible additions from newer backends to older mobile builds.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Trust compile-time types only | Types vanish at runtime; payloads are dynamic and partially untrusted — exactly the case types cannot cover. |
| Ad-hoc manual guards at each call site | Unenforceable, unauditable, and prohibited by §17.3. |
| JSON Schema with a generic validator | Loses the TypeScript-first inference pipeline and the shared authored-once consumption model of `packages/validation`. |

## Verification

- Engineering acceptance criteria 8–10 (PRD §28.2): runtime validation protects all untrusted dynamic payloads; discriminated/branded domain types at navigation, dashboards, graph views, conversation events; graph queries authorized and provenance-bearing with no raw model-generated database code executed.
- Mobile quality gates (§23.4): Zod tests cover malformed and forward-compatible payloads; exhaustiveness tests cover every widget and conversation event.
- Golden tests: malicious news/agent content cannot alter structure or behavior (Scenario C, §23.2).
