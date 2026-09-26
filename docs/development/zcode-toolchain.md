# ZCode AI Engineering Toolchain

**Status:** Required development standard
**Applies to:** Sales Northstar repository
**Decision:** ADR-027
**Last updated:** 26 September 2026

## 1. Standard

ZCode is the primary AI coding Agent Development Environment for Sales Northstar. It replaces OpenCode in the engineering workflow. ZCode assists with repository exploration, planning, implementation, testing, browser verification, and change review; it does not replace Git, pull-request approval, CI, security review, or release controls.

The supporting build toolchain remains:

| Layer | Standard |
|---|---|
| AI coding workbench | ZCode Agent |
| Manual editor | ZCode editor; VS Code may be used as a non-agent fallback |
| Runtime/task versions | mise |
| TypeScript monorepo | pnpm workspaces + Turborepo |
| Python workspace | uv |
| Local dependencies | Docker Compose |
| Kubernetes integration | kind + Tilt |
| Source and review | GitHub pull requests + CODEOWNERS |
| CI | GitHub Actions |
| Deployment | Argo CD / approved GitOps controller |
| Security | secret scanning, SAST, SCA, SBOM, image and IaC scanning |

## 2. Why ZCode fits

ZCode provides a workspace-aware coding agent with file references, command execution, Git context, change review, long-running task goals, controlled execution modes, browser automation, remote development, reusable commands and skills, MCP integration, and custom model providers. ZCode accepts OpenAI-compatible and Anthropic-compatible custom providers, allowing an approved team model channel to terminate at the Northstar APISIX development gateway rather than embedding provider credentials in repository configuration.

## 3. Repository integration

### 3.1 Workspace instructions

The root `AGENTS.md` is the single project instruction file. ZCode loads the user-global `~/.zcode/AGENTS.md` first and the workspace root `AGENTS.md` second. It does not merge nested `AGENTS.md` files, scan child directories for rules, or process `@include` directives. Therefore:

- Keep mandatory architecture and security rules in root `AGENTS.md`.
- Keep component detail in the nearest `README.md` and explicitly reference it in tasks.
- Do not create conflicting nested `AGENTS.md` files.
- Review changes to `AGENTS.md` through CODEOWNERS as an engineering-policy change.

### 3.2 Team plugin

The repository includes a versioned `northstar` ZCode plugin under `tools/zcode/plugins/northstar` and a root `marketplace.json`. The plugin contains reusable commands and a delivery skill but no hooks, MCP servers, credentials, or executable binaries.

Install it by adding this repository as a personal marketplace in **Settings → Plugins → Create → Add marketplace**, then install `northstar`. Review the plugin source before enabling it. Reinstall or refresh after a plugin version update.

Available commands:

| Command | Purpose |
|---|---|
| `/northstar-plan` | Produce a bounded implementation plan mapped to PRD and ADR controls |
| `/northstar-verify` | Run and report the relevant verification matrix without inventing success |
| `/northstar-security-review` | Review a diff for authorization, secret, protocol, data, and agent risks |
| `/northstar-contract-review` | Check OpenAPI, TypeScript, Zod, streaming, and compatibility impacts |

The `$northstar-delivery` skill provides the standard plan → implement → verify → review workflow.

### 3.3 Local state

Do not commit ZCode local state, model credentials, account tokens, private MCP settings, task history, or memory. `.zcode/` is ignored. Team behavior belongs in root `AGENTS.md` and the reviewed plugin; developer-specific preferences belong under the user's home directory.

Project Memory remains disabled for confidential work unless security governance approves it. It is local and unversioned, but currently cannot be browsed or selectively cleared from the product. Durable team knowledge must be written into reviewed documentation, tests, ADRs, or `AGENTS.md`.

## 4. Model access

### 4.1 Approved connection pattern

Use one of these approved options, in order:

1. **Enterprise APISIX channel:** configure a ZCode custom provider to the team-managed Northstar development gateway using either the OpenAI-compatible or Anthropic-compatible route family.
2. **Approved team plan:** use an enterprise-managed Z.ai/BigModel team plan when permitted by data-classification policy.
3. **Direct provider key:** permitted only for non-sensitive work under an approved exception; store the key in ZCode's local provider settings, never in Git or shell history.

The APISIX development gateway must apply authenticated developer identity, provider/model allowlists, quotas, payload-logging restrictions, DLP, and audit correlation. OpenAI and Anthropic remain separate native provider profiles. Do not rely on silent protocol conversion.

### 4.2 Data boundaries

Before sending context to a coding model:

- Use synthetic or redacted fixtures; never include live CRM, customer, pipeline, employee, access-token, Vault, or licensed-news data.
- Exclude `.env`, key files, production exports, crash dumps, packet captures, and secret-bearing logs.
- Do not paste model-provider responses that contain sensitive prompts or tenant data.
- Treat generated dependency changes, migration scripts, policies, and infrastructure as high risk.

## 5. Execution policy

| Change class | ZCode mode | Human gate |
|---|---|---|
| Read-only exploration | Plan or Ask before changes | Confirm scope before implementation |
| Small test/docs/refactor | Edit automatically | Diff review and relevant tests |
| Cross-service or schema change | Plan mode | Approve plan before edits |
| APISIX, Vault, BYOK, IAM, K8s, CI, release | Ask before changes | Security/platform owner review |
| Destructive command, migration, credential action | Ask before changes | Explicit per-command approval; production execution prohibited from ZCode |
| Full access | Not the default | Only isolated, disposable, non-sensitive environments |

Use ZCode's built-in **Explore** subagent for broad read-only codebase mapping. Custom subagents are not treated as repository policy because current project-level custom-subagent management is not a stable team-distribution mechanism. Any subagent output receives the same review as primary-agent output.

## 6. Development workflow

1. Open the repository root as the ZCode workspace.
2. Create a dedicated Git branch or worktree; never work directly on the protected branch.
3. State a verifiable goal and reference the issue, PRD section, ADR, and affected files.
4. Use Plan mode for anything beyond a narrow edit.
5. Confirm authorization, data, API, schema, migration, and rollback impacts before coding.
6. Implement the smallest coherent change with tests.
7. Run the relevant local checks through mise tasks; never expose secrets in terminal output.
8. Use the built-in browser, Android emulator, or iOS simulator only with synthetic local data.
9. Review the entire diff, generated files, dependency lock changes, and test evidence.
10. Open a pull request using the repository template; CI and CODEOWNERS remain authoritative.

ZCode task completion must include:

- Changed files and behavior.
- Commands executed and exact outcomes.
- Tests not run and why.
- Security, compatibility, migration, and rollback considerations.
- Assumptions and unresolved decisions.

## 7. Build commands

The canonical task names are implemented through `mise` and must work identically for humans and ZCode:

```bash
mise run bootstrap
mise run lint
mise run typecheck
mise run test
mise run contracts:check
mise run security:check
mise run verify
mise run dev
mise run integration
```

Until a task exists, ZCode must not invent its implementation or claim it passed. Add missing tasks through a reviewed bootstrap pull request and document their underlying commands.

## 8. Remote development

For SSH, WSL, or container workspaces, ZCode runs agent operations on the target environment. Sync only approved skills/plugins and re-review remote configuration after synchronization. Never sync personal credentials or unrestricted MCP services to a shared host. Apply the same branch, least-privilege, secret, and CI requirements remotely.

## 9. MCP and plugins

No workspace MCP server is enabled by default. Workspace MCP declarations connect automatically at session start and can execute processes, access files, and reach networks; any addition therefore requires architecture and security review.

Requirements for an approved MCP or plugin:

- Pin source and version or commit.
- Review manifest, scripts, hooks, commands, requested tools, network destinations, and inherited environment access.
- Use least-privilege tools and read-only access where possible.
- Keep credentials in approved local or enterprise secret storage.
- Add a threat model, owner, update process, and removal procedure.
- Verify behavior in an isolated workspace before team rollout.

## 10. CI boundary

ZCode is an interactive engineering accelerator, not the CI control plane. GitHub Actions must independently reproduce formatting, linting, types, generation, unit/integration tests, security scanning, and build outputs from a clean checkout. A ZCode conversation, screenshot, local task result, or generated summary is never release evidence by itself.

## 11. Migration from OpenCode

- Remove OpenCode from recommended tools, onboarding, screenshots, templates, and developer guides.
- Do not copy OpenCode-specific permission or agent configuration into the repository.
- Re-express stable team rules in root `AGENTS.md`.
- Rebuild repeatable workflows as the reviewed `northstar` ZCode plugin.
- Recreate provider connections locally or through the enterprise APISIX development gateway; do not migrate plaintext credentials.
- Preserve Git branches and code changes, but start new ZCode tasks with explicit context.
- Keep CI and build commands unchanged so migration does not alter software behavior.

## 12. Acceptance checklist

- [ ] ZCode is the only named primary AI coding workbench in current documentation.
- [ ] Root `AGENTS.md` is present, reviewed, and consistent with the PRD/ADRs.
- [ ] No model key, MCP credential, ZCode local state, or task history is committed.
- [ ] The `northstar` plugin installs from the repository marketplace and exposes its commands/skill.
- [ ] A representative TypeScript, Python, gateway, and documentation task follows the workflow.
- [ ] `mise run verify` is reproducible from a clean checkout once bootstrap implementation lands.
- [ ] GitHub Actions independently enforces the required gates.
- [ ] Security review approves provider routing, data classification, plugins, and any MCP server.

## 13. Official documentation

- [ZCode Agent](https://zcode.z.ai/en/docs/agents)
- [Connect Models](https://zcode.z.ai/en/docs/configuration)
- [Commands](https://zcode.z.ai/en/docs/commands)
- [Skills](https://zcode.z.ai/en/docs/skill)
- [Subagents](https://zcode.z.ai/en/docs/subagents)
- [MCP](https://zcode.z.ai/en/docs/mcp-services)
- [Plugins](https://zcode.z.ai/en/docs/plugin)
- [Remote Development](https://zcode.z.ai/en/docs/remote-development)
