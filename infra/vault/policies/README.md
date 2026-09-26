# Vault policy layout (ADR-023)

| Policy file | Bound to | Grants |
|---|---|---|
| `northstar.hcl` | service accounts per workload | least-privilege read/create on `byok/*`, `connectors/*`, platform OIDC secret; lease revoke for rotation |

Binding rules:
- One token per workload (APISIX data plane, byok service, each connector) — no shared tokens.
- `byok/` is tenant-scoped: `byok/<tenant>/<provider>/<slot>`; the policy is combined with a
  per-tenant namespace/prefix guard at the auth-backend level in production.
- Audit device is enabled at the root path; policy changes go through Git + `vault policy write`
  from the config controller, never ad-hoc.
