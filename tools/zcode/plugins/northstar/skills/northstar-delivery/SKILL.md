---
name: northstar-delivery
description: Use for planning, implementing, verifying, or reviewing any Sales Northstar change that must comply with its PRD, ADRs, security boundaries, strict TypeScript contracts, native LLM protocols, and CI gates.
metadata:
  author: Sales Northstar Engineering
  version: 1.0.0
---

# Northstar Delivery

1. Read root `AGENTS.md`, relevant `prd-v1.md` sections, ADRs, and component READMEs.
2. Define a bounded outcome and identify authorization, data, API, metric, graph, AI, infrastructure, and rollback impact.
3. Use Plan mode before broad or high-risk edits.
4. Preserve APISIX-only ingress, native OpenAI/Anthropic contracts, Vault-only BYOK, strict TypeScript, generated contracts, typed graph IR, certified metrics, and explicit confirmation for writes.
5. Implement the smallest coherent change and tests; do not hand-edit generated output.
6. Run deterministic checks and report exact outcomes. Never invent test success.
7. Review the complete diff for secrets, unsafe logs, permission leakage, unsupported claims, dependency risk, and unrelated changes.
8. Finish with files changed, commands/results, tests not run, assumptions, risks, and rollback notes.
