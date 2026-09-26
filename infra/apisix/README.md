# infra/apisix — Apache APISIX API and AI gateway

APISIX is the sole north–south API and AI gateway (PRD §12, §15; ADR-021). Deployment: separate data-plane and restricted control-plane workloads, ≥3 data-plane replicas across failure zones, etcd private with mTLS, Admin API off public listeners, declarative config in Git (PRD §15.1).

## Route contracts (PRD §15.2)

| Route | Purpose |
|---|---|
| `/ai/openai/v1/chat/completions` | OpenAI-native, SSE ending `[DONE]` |
| `/ai/anthropic/v1/messages` | Anthropic-native pass-through, SSE ending `message_stop` |
| `/internal/ai/capabilities/{capability}` | Server-side only capability pool |
| `/api/v2/*` (naming pending — review F-01) | Product APIs to BFF/services |

## Plugin chain order (PRD §15.3)

Correlation ID → authn → consumer/tenant resolution → request-size/method → header allow-list + sensitive-header stripping → model/capability authorization → rate limit/budget → `ai-proxy`/`ai-proxy-multi` → response/stream limits → metrics + redacted audit.

**Mandatory:** header stripping before `ai-proxy` — only `Host`, `Content-Length`, `Accept-Encoding` are dropped automatically; credentials and cookies otherwise reach providers (PRD §15.3).

## Policies (PRD §15.4)

`openai-native-primary`, `anthropic-native-primary`, `openai-compatible-resilient`, `anthropic-emergency-conversion` (disabled by default), `internal-capability-pool`. Bounded retries; semantic balancing never used for resilience. Example pattern in PRD §15.6.

## Build track

Phase 1, Track A Sprints 1–3, 5 — see `todo.md`.
