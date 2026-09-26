/** Typed error envelope (PRD §17.8). Identical contract to the BFF/metrics services. */
export type ApiErrorCode =
  | "UNAUTHENTICATED"
  | "FORBIDDEN"
  | "VALIDATION_FAILED"
  | "AI_CREDENTIAL_UNAVAILABLE"
  | "AI_RATE_LIMITED"
  | "AI_PROTOCOL_FEATURE_UNSUPPORTED"
  | "DEPENDENCY_UNAVAILABLE"
  | "INTERNAL_ERROR";

export type FieldError = Readonly<{
  field: string;
  message: string;
}>;

export type ApiError = Readonly<{
  code: ApiErrorCode;
  message: string;
  correlationId: string;
  retryable: boolean;
  retryAfterSeconds?: number;
  fieldErrors?: readonly FieldError[];
}>;

/** UI mapping rule (§17.8): never display provider keys, upstream bodies, or secret references. */
export const USER_FACING_MESSAGES: Readonly<Record<ApiErrorCode, string>> = {
  UNAUTHENTICATED: "Please sign in again.",
  FORBIDDEN: "You do not have access to this data.",
  VALIDATION_FAILED: "The request could not be processed.",
  AI_CREDENTIAL_UNAVAILABLE: "The AI service is unavailable. Contact your administrator.",
  AI_RATE_LIMITED: "Too many requests. Please retry shortly.",
  AI_PROTOCOL_FEATURE_UNSUPPORTED: "This feature is not supported right now.",
  DEPENDENCY_UNAVAILABLE: "A dependency is unavailable. Please retry.",
  INTERNAL_ERROR: "Something went wrong. Please retry.",
};
