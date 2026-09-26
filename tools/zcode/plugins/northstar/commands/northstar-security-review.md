---
description: Review Northstar changes for security, privacy, tenant isolation, agent, BYOK, and supply-chain risks.
argument-hint: "[path, branch, or diff scope]"
skills: northstar-delivery
---

Perform a security-focused review of: $ARGUMENTS

Use root AGENTS.md, PRD §§11, 15–16, 18, 20, 23, 28, and relevant ADRs. Prioritize exploitable findings. Check authorization, tenant/domain/group scope, secrets, logging, prompt injection, tool permissions, native protocol handling, dependency and plugin changes, unsafe fallbacks, data provenance, and confirmation/idempotency for writes. Cite file and line evidence and recommend tests.
