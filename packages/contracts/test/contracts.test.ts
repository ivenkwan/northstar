import { describe, expect, it } from "vitest";
import {
  USER_FACING_MESSAGES,
  type ApiError,
  type ApiErrorCode,
  type ConversationResponse,
  type DashboardDefinition,
  type ActionPreview,
  type ActionReceipt,
  type UserContext,
  type MetricLineage,
} from "../src/index";

describe("@northstar/contracts", () => {
  it("defines user facing messages for all ApiErrorCodes without leaking secrets or system internals", () => {
    const errorCodes: ApiErrorCode[] = [
      "UNAUTHENTICATED",
      "FORBIDDEN",
      "VALIDATION_FAILED",
      "AI_CREDENTIAL_UNAVAILABLE",
      "AI_RATE_LIMITED",
      "AI_PROTOCOL_FEATURE_UNSUPPORTED",
      "DEPENDENCY_UNAVAILABLE",
      "INTERNAL_ERROR",
    ];

    for (const code of errorCodes) {
      const msg = USER_FACING_MESSAGES[code];
      expect(msg).toBeDefined();
      expect(typeof msg).toBe("string");
      expect(msg.length).toBeGreaterThan(0);

      // Verify no sensitive internal strings or key patterns are leaked
      const lower = msg.toLowerCase();
      expect(lower).not.toContain("sk-");
      expect(lower).not.toContain("vault");
      expect(lower).not.toContain("secret");
      expect(lower).not.toContain("password");
      expect(lower).not.toContain("bearer");
    }
  });

  it("validates ApiError structure and constraints", () => {
    const sampleError: ApiError = {
      code: "VALIDATION_FAILED",
      message: USER_FACING_MESSAGES.VALIDATION_FAILED,
      correlationId: "corr-12345",
      retryable: false,
      fieldErrors: [
        { field: "metric", message: "Metric is required" },
      ],
    };

    expect(sampleError.code).toBe("VALIDATION_FAILED");
    expect(sampleError.correlationId).toBe("corr-12345");
    expect(sampleError.retryable).toBe(false);
    expect(sampleError.fieldErrors).toHaveLength(1);
    expect(sampleError.fieldErrors?.[0].field).toBe("metric");
  });

  it("exports contract interface types that can be instantiated/type-checked", () => {
    const userContext: UserContext = {
      userId: "usr_100",
      role: "seller",
      teamIds: ["team_alpha"],
      domainIds: ["domain_hk"],
      groupIds: ["group_sales"],
      preferences: { currency: "HKD", locale: "en-HK" },
      allowedScopes: ["seller:usr_100"],
    };
    expect(userContext.userId).toBe("usr_100");

    const lineage: MetricLineage = {
      metricId: "attainment_pct",
      version: "v3",
      name: "Quota Attainment %",
      formula: "closed_won / target",
      grain: "monthly",
      certification: "certified",
    };
    expect(lineage.metricId).toBe("attainment_pct");

    const preview: ActionPreview = {
      actionId: "act_1",
      actionType: "update_stage",
      changes: [{ field: "stage", oldValue: "Qualification", newValue: "Proposal" }],
      requiresConfirmation: true,
      stepUpAuthRequired: false,
    };
    expect(preview.actionId).toBe("act_1");

    const receipt: ActionReceipt = {
      actionId: "act_1",
      status: "executed",
      idempotentReplay: false,
      externalRef: "crm_ref_123",
      executedAt: "2026-09-27T00:00:00Z",
    };
    expect(receipt.status).toBe("executed");
  });
});
