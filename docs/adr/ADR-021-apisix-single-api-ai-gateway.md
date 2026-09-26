# ADR-021: Apache APISIX is the sole enterprise API and AI gateway

| | |
|---|---|
| **Status** | Proposed (release-governing) |
| **Date** | 2026-09-26 |
| **Deciders** | Solution architect, security, product owner |
| **PRD references** | §12, §15, §13, §28.2 criterion 1 |

## Context

Sales Northstar needs north–south traffic control for both product APIs and LLM provider calls: multi-provider proxying with native protocol preservation, token-aware rate limiting and budgets, load balancing, bounded retries and fallback, and AI request observability — without adding another model-proxy hop beside the API gateway. Provider credentials must never reach the mobile client, and prompt/payload logging must stay off by default.

## Decision

Apache APISIX is the **only** north–south API and AI gateway in the runtime, deployment manifests, operations model, and dependency inventory. It terminates all product API traffic (`/api/*` to the BFF and services) and all provider AI traffic via the `ai-proxy` and `ai-proxy-multi` plugins, publishing the two first-class native LLM routes defined in ADR-022 plus the internal capability pool. Provider keys are injected server-side from Vault references (ADR-023). Topology, plugin chain order, and provider-routing policies follow PRD §15.1–§15.4.

## Consequences

**Positive:**

- Authentication, rate limiting, load balancing, and AI proxying in one open-source gateway; no extra hop and one operational surface to harden and observe.
- Native support for both OpenAI and Anthropic protocols, including SSE streaming semantics.
- AI observability (model, duration, token usage, time-to-first-response) available from access logs with payload logging disabled by default.

**Negative / accepted costs:**

- Gateway configuration becomes release-critical; a CI conformance test must verify the exact APISIX release schema on every upgrade because plugin attributes and secret-manager capabilities differ across releases.
- etcd, control-plane isolation, and Gateway-API/GitOps configuration discipline are mandatory operational overhead.
- Header sanitization must be configured explicitly (see ADR-023 and PRD §15.3) because `ai-proxy` forwards most client headers by default.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Dedicated AI gateway beside a traditional API gateway (e.g. an LLM proxy + NGINX/Kong) | Two gateways to secure, observe, and operate; the PRD explicitly avoids the additional model-proxy hop (§12). |
| Provider SDKs called directly from services | No central credential custody, quota enforcement, model authorization, or protocol observability; violates the mobile and BYOK trust boundaries (§13.1). |
| Cloud-provider API management with AI features | Deployment target is single-enterprise private cloud/VPC (§4.1); portability requirement (§22) disallows cloud-locked gateway control planes. |

## Verification

- Engineering acceptance criterion 1 (PRD §28.2): APISIX is the only AI gateway in the runtime, manifests, operations model, and dependency inventory, and it passes the golden OpenAI and Anthropic contract suites (§23.3).
- Gateway conformance goldens in `tests/golden` cover plugin chain order, header stripping, quota/retry behavior, and tenant isolation.
