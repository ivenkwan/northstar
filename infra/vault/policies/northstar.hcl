# Vault policies (ADR-023): tenant-scoped BYOK paths, least privilege per workload.
# Dev values live in docker-compose; these policies apply to the production Vault.

# APISIX data plane: read only the byok secrets it resolves for routing,
# never write, never list, never platform secrets.
path "byok/*" {
  capabilities = ["read"]
}

# BYOK credential service: lifecycle writes under its tenant prefix + reads
# for verification probes. No delete — revocation is a versioned operation.
path "byok/*" {
  capabilities = ["create", "read", "update"]
}

path "sys/leases/revoke" {
  capabilities = ["update"]   # credential rotation revokes old leases
}

# Platform OIDC client secret (gateway config) — config controller only.
path "platform/oidc-client-secret" {
  capabilities = ["read"]
}

# Connectors: per-source credentials, read-only at runtime.
path "connectors/*" {
  capabilities = ["read"]
}
