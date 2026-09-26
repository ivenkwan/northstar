# tools/zcode — ZCode team workflows

ZCode is the required AI coding workbench for Sales Northstar (PRD §17.9, ADR-027). Repository-wide instructions live in `/AGENTS.md`; the complete operating standard is in `/docs/development/zcode-toolchain.md`.

## Layout

- `/marketplace.json` — repository marketplace entry.
- `plugins/northstar/` — reviewed commands and delivery skill.

## Install

In ZCode, add this repository through **Settings → Plugins → Create → Add marketplace**, install `northstar`, and review its source before enabling it. Refresh the marketplace after version changes.

## Security

This plugin intentionally contains no MCP servers, executable hooks, model credentials, or binaries. Any future addition of those capabilities requires security review and a version bump in both the plugin and marketplace manifests.
