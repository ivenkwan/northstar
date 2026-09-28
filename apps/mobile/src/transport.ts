/** The ONLY module permitted to call fetch (PRD §17.3 transport boundary).
 *
 * Requests go to the BFF; responses cross the Zod boundary from
 * @northstar/validation before reaching UI (ADR-026). Typed errors map to
 * approved user messages via @northstar/contracts (§17.8) — never provider
 * bodies or internal paths.
 */
import type { ApiError, Conversation } from "@northstar/contracts";
import { USER_FACING_MESSAGES } from "@northstar/contracts";
import type { Briefing, ConversationResponse } from "@northstar/validation";
import { BriefingSchema, ConversationResponseSchema } from "@northstar/validation";

import { DEV_AUTH_HEADER } from "./config";

export class ApiRequestError extends Error {
  constructor(message: string, readonly code: string) {
    super(message);
  }
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { ...DEV_AUTH_HEADER, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiRequestError("Cannot reach the Northstar backend. Is the stack running?", "DEPENDENCY_UNAVAILABLE");
  }
  if (!response.ok) {
    // Narrow unknown → ApiError envelope (§17.8); never surface raw bodies.
    const parsed: unknown = await response.json().catch(() => null);
    const apiError = parsed as Partial<ApiError> | null;
    const code = apiError?.code ?? "INTERNAL_ERROR";
    const known = USER_FACING_MESSAGES[code];
    throw new ApiRequestError(known ?? USER_FACING_MESSAGES.INTERNAL_ERROR, code);
  }
  return (await response.json()) as T;
}

async function getJson(url: string): Promise<unknown> {
  const response = await fetch(url, { headers: DEV_AUTH_HEADER }).catch(() => {
    throw new ApiRequestError("Cannot reach the Northstar backend.", "DEPENDENCY_UNAVAILABLE");
  });
  if (!response.ok) throw new ApiRequestError("Service unavailable.", "DEPENDENCY_UNAVAILABLE");
  return response.json();
}

export async function checkHealth(apiBase: string): Promise<boolean> {
  const body = await getJson(`${apiBase}/healthz`);
  return (body as { status?: string }).status === "ok";
}

export async function askQuestion(apiBase: string, text: string): Promise<ConversationResponse> {
  const conversation = await postJson<Conversation>(`${apiBase}/api/v1/conversations`, {});
  const raw: unknown = await postJson(`${apiBase}/api/v1/conversations/${conversation.conversationId}/messages`, { text });
  return ConversationResponseSchema.parse(raw); // malformed/mismatched payloads reject here
}

export async function getTodayBriefing(apiBase: string): Promise<Briefing> {
  const raw: unknown = await getJson(`${apiBase}/api/v1/briefings/today`);
  return BriefingSchema.parse(raw); // §7.1 payload crosses the Zod boundary here (ADR-026)
}
