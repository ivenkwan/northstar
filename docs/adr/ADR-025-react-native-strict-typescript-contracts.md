# ADR-025: React Native uses the Strict TypeScript API and generated end-to-end contracts

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §12, §17.1–§17.4, §17.7, §28.2 criteria 7–9 |

## Context

The mobile app renders AI-generated, dynamically-shaped content (conversation components, dashboard definitions, graph subgraphs) and talks to versioned product APIs. Type confusion at these boundaries — unvalidated JSON reaching renderers, hand-copied DTOs drifting from the backend, stringly typed navigation — is a recurring source of crashes, data leakage, and contract breakage in React Native codebases. The PRD mandates a "no-untyped-boundary" engineering policy (§12).

## Decision

The mobile application is built on **React Native 0.87+ with the Strict TypeScript API enabled**, TypeScript 5.x only (no JavaScript source except reviewed build configuration), under the full strict compiler policy of PRD §17.2 (`strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax`, …). End-to-end contracts are **generated, never hand-authored**: the backend OpenAPI 3.1 documents are the source of truth; `tools/codegen` generates the TypeScript types and transport functions into `packages/contracts`; CI fails if generated output drifts or an unapproved breaking change ships (§17.4). Navigation uses statically typed parameter lists with branded IDs, and deep links are runtime-validated before navigation (§17.7). The prohibited patterns of §17.3 (explicit/implicit `any`, `@ts-ignore`, double assertions, non-null assertions at boundaries, raw `fetch` outside transport, unvalidated agent/dashboard JSON, …) fail CI unless a time-bounded waiver is recorded.

## Consequences

**Positive:**

- Type errors surface at compile time at exactly the boundaries where runtime data is dynamic; widget renderers and conversation event handlers are exhaustively checked.
- Contract drift between backend and mobile becomes a CI failure, not a production incident; forced minimum-version policy (§29) has a deterministic trigger.
- The codebase stays refactorable as the PRD's widget/domain model evolves.

**Negative / accepted costs:**

- Stricter-than-default flags (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`) demand more explicit code and disciplined schema narrowing; velocity cost accepted.
- TypeScript and dependency versions must be pinned and upgraded through controlled PRs because `strict` can surface new errors as the compiler strengthens (§17.2).
- Codegen pipeline must exist before feature work (Sprint 2 sequencing in `todo.md`).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Default (non-strict) TypeScript | Untyped boundaries are precisely where this product's risk concentrates (AI-generated payloads, contracts, navigation). |
| Hand-written client types | Explicitly prohibited (§17.3); drifts from backend within one sprint. |
| JavaScript with JSDoc checking | Weaker and less future-proof type accuracy than the Strict TypeScript API (§12); no exhaustiveness or discriminated-union guarantees. |
| Flutter / native clients | PRD §4.1 planning default is React Native; revisiting is a product decision outside this ADR's scope. |

## Verification

- Engineering acceptance criteria 7–9 (PRD §28.2): TypeScript-only source with strict compilation and no waivers; API clients generated from OpenAPI; navigation, dashboards, graph views, and conversation events use discriminated or branded types.
- Mobile quality gates (§23.4): `tsc --noEmit` zero errors; ESLint zero explicit `any`/unsafe access/floating promises; generated package current and reproducible; exhaustiveness and deep-link tests.
