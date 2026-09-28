/** @northstar/contracts — generated from services/bff/openapi/openapi.json (PRD §17.4).
 *
 * DO NOT hand-edit src/generated/. CI regenerates and fails on drift
 * (`pnpm contracts:check`). Hand-authored DTO copies are prohibited (§17.3).
 */
export type { ApiError, ApiErrorCode, FieldError } from "./api-error";
export { USER_FACING_MESSAGES } from "./api-error";

import type { components, operations, paths } from "./generated/schema";

export type ConversationResponse = components["schemas"]["ConversationResponse"];
export type Conversation = components["schemas"]["Conversation"];
export type DashboardDefinition = components["schemas"]["DashboardDefinition"];
export type ActionPreview = components["schemas"]["ActionPreview"];
export type ActionReceipt = components["schemas"]["ActionReceipt"];
export type UserContext = components["schemas"]["UserContext"];
export type MetricLineage = components["schemas"]["MetricLineage"];

/** Every product endpoint, derived from the OpenAPI source — the typed route table. */
export type ApiRoute = keyof paths;
export type PostMessageOperation = operations["postMessage"];
