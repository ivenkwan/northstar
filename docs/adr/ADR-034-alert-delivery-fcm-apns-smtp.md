# ADR-034: MVP alert delivery is in-app push (FCM/APNs) and enterprise email; Teams in Phase 2

| | |
|---|---|
| **Status** | Proposed — pending architecture review board (Phase 0 gate) |
| **Date** | 2026-09-26 |
| **Deciders** | Product owner, solution architect, security |
| **PRD references** | §8.6, §24.3 |
| **Resolves** | PRD review finding F-06 |

## Context

§8.6 lists in-app push, email, Teams, and enterprise notification services as alert channels, while §24.3 defers Teams integration to Phase 2 (F-06). Mobile push necessarily traverses Apple/Google infrastructure (APNs/FCM); email traverses the enterprise SMTP estate. Both must satisfy §8.6's rule that notifications deep-link to permission-checked views and record delivery telemetry, and §11.2's data-minimization posture.

## Decision

MVP alert delivery is:

1. **In-app notification center** — always available, no external dependency, satisfies the §8.6 deep-link and acknowledgement requirements.
2. **Mobile push via FCM (Android) and APNs (iOS)** — device tokens registered by the mobile app; **notification payloads carry metadata only** (alert type, severity, correlation ID) — never amounts, customer names, or record data; the body is fetched from the API after authentication. Quiet hours, frequency caps, digest, and snooze (§8.6) are enforced server-side before dispatch.
3. **Email via the enterprise SMTP relay** — digests and briefings only (not per-event alerts), rendered server-side, respecting the same frequency caps; enterprise DLP/retention applies.

**Teams integration is Phase 2** (resolving F-06): Teams channel delivery requires Graph API consent, tenant app registration, and message-policy review — scheduled with the other §24.3 Teams work.

## Consequences

**Positive:** every MVP channel is either internal or metadata-only at the boundary; alert fatigue controls are centralized; no third-party SaaS notification vendor in the trust boundary.

**Negative / accepted costs:** push requires FCM/APNs projects and MDM distribution alignment (Phase 0 discovery item); metadata-only push means users must open the app to learn details — acceptable per §8.6's permission-checked deep-link model.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Teams in MVP | Scope mismatch (F-06) and consent/app-registration lead time. |
| Third-party notification SaaS (e.g. OneSignal) | Adds a vendor receiving employee/device data; unnecessary given FCM/APNs + SMTP. |
| Full payload in push bodies | Leaks sales data through device notification surfaces (lock screens), violating minimization. |

## Verification

- Golden test: push payloads validate against a metadata-only schema; opening a deep link re-checks authorization at open time (§10.2).
- Telemetry records delivery and engagement per notification (§8.6, §25.1).
- Quiet hours / frequency-cap unit tests on the dispatch service.
