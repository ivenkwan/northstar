# ADR-027: ZCode is the standard AI engineering workbench

**Status:** Proposed
**Date:** 26 September 2026
**Decision owners:** Engineering, security, enterprise architecture
**PRD references:** §17.9, §20, §23.5, §28.2

## Context

Sales Northstar spans strict React Native, FastAPI, agent orchestration, data semantics, knowledge graphs, APISIX, Vault, Kubernetes, and AI evaluation. AI-assisted changes can accelerate this work but can also expose secrets, broaden scope, bypass architecture decisions, or create false confidence in unexecuted tests.

The previous external recommendation named OpenCode. The repository did not yet contain an enforceable OpenCode configuration, and the engineering team has selected ZCode as the AI coding environment. ZCode supports a workspace `AGENTS.md`, controlled execution modes, model-provider connections over OpenAI-compatible and Anthropic-compatible protocols, commands, skills, plugins, remote development, browser verification, and isolated read-only exploration.

## Decision

1. ZCode becomes the primary AI coding Agent Development Environment for this repository; OpenCode is removed from the current toolchain.
2. Root `AGENTS.md` is the single version-controlled workspace instruction source because ZCode does not merge nested project instruction files.
3. Stable team workflows are distributed through the reviewed `northstar` ZCode plugin in `tools/zcode`; user-specific settings remain outside Git.
4. ZCode model access uses an approved enterprise channel, preferably the APISIX development gateway with separate OpenAI-compatible and Anthropic-compatible profiles. Credentials never enter repository files.
5. Plan mode is required for broad, security, schema, dependency, and cross-service changes. Ask-before-changes is required for APISIX, Vault, BYOK, IAM, Kubernetes, CI, release, destructive, or credential-related work.
6. Full-access mode is not the default and may be used only in isolated, disposable, non-sensitive environments.
7. Workspace MCP servers and executable plugin hooks are disabled by default. Enabling either requires source review, least privilege, ownership, and security approval.
8. Project Memory remains disabled for confidential work unless governance approves it. Durable knowledge belongs in version-controlled documentation and tests.
9. ZCode-generated code and summaries are untrusted until human review and independent CI verification complete.
10. GitHub Actions and GitOps remain the authoritative build and release controls; no release gate depends on a ZCode session.

## Consequences

### Positive

- A single workspace-aware tool and instruction file reduce inconsistent agent behavior.
- Native OpenAI/Anthropic provider support aligns with the APISIX/BYOK architecture.
- Execution modes allow risk-proportionate human control.
- Versioned commands and skills make repeatable workflows reviewable.
- Existing deterministic build and CI tooling remains unchanged.

### Trade-offs

- ZCode is a desktop-first dependency and requires developer onboarding and governance.
- Some settings, memories, and custom subagents are user-local rather than fully repository-distributed.
- Plugin and MCP extensibility expands the local attack surface and requires supply-chain review.
- Interactive agent execution cannot serve as reproducible CI evidence.

## Alternatives considered

- **OpenCode:** Rejected as the primary tool following the engineering decision to standardize on ZCode.
- **IDE copilot only:** Rejected because it does not provide the same repository planning and long-running workflow standard.
- **Unrestricted mixed tools:** Rejected because project rules, permissions, and evidence would be inconsistent.
- **No AI coding tools:** Rejected because it forgoes useful acceleration; risks are better handled through bounded permissions and independent verification.

## Verification

- Documentation contains no active recommendation to use OpenCode.
- Root `AGENTS.md` exists and references release-governing architecture constraints.
- The repository plugin installs and its commands/skill are visible in ZCode.
- `.zcode/` local state and credentials are excluded from Git.
- Representative changes pass local verification and the same independent GitHub Actions gates.
- Security signs off any enterprise provider channel, MCP server, executable hook, or Full Access exception.
