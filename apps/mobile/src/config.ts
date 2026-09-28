/** Dev-preview configuration. EXPO_PUBLIC_API_BASE overrides the LAN default. */
export const DEFAULT_API_BASE = "http://192.168.1.129:18000";

export function apiBase(): string {
  const fromEnv = process.env["EXPO_PUBLIC_API_BASE"];
  return fromEnv !== undefined && fromEnv !== "" ? fromEnv : DEFAULT_API_BASE;
}

/** Dev auth placeholder — production issues gateway-verified OIDC tokens (§13.1). */
export const DEV_AUTH_HEADER = { Authorization: "Bearer u_dev" };
