import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiRequestError,
  askQuestion,
  checkHealth,
  getTodayBriefing,
} from "../src/transport";

describe("apps/mobile transport layer", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("checkHealth returns true when backend healthz is ok", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    } as Response);

    const isHealthy = await checkHealth("http://localhost:18000");
    expect(isHealthy).toBe(true);
    expect(globalThis.fetch).toHaveBeenCalledWith("http://localhost:18000/healthz", expect.any(Object));
  });

  it("askQuestion creates conversation and posts message successfully", async () => {
    globalThis.fetch = vi.fn()
      // First call: create conversation
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          conversationId: "conv_test123",
          scopeType: "seller",
          scopeId: "user1",
          createdAt: "2026-09-27T00:00:00Z",
        }),
      } as Response)
      // Second call: post message
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          messageId: "m1",
          answer: "Your quota attainment is 60%.",
          scope: { type: "seller", id: "user1", asOf: "2026-09-27T00:00:00Z" },
          components: [
            {
              type: "narrative",
              payload: { text: "Your quota attainment is 60%." },
            },
          ],
          evidence: [],
          warnings: [],
          suggestedActions: [],
        }),
      } as Response);

    const response = await askQuestion("http://localhost:18000", "How am I tracking?");
    expect(response.messageId).toBe("m1");
    expect(response.answer).toBe("Your quota attainment is 60%.");
    expect(response.components[0].type).toBe("narrative");
  });

  it("getTodayBriefing parses raw response through Zod boundary", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        asOf: "2026-09-27T08:00:00Z",
        scopeId: "u_dev",
        greeting: "Here is your day at a glance.",
        kpis: [
          {
            metricId: "attainment_pct",
            version: 3,
            value: 60.0,
            unit: "percent",
          },
        ],
        topRisks: [
          {
            opportunityId: "opp_1",
            name: "ACME renewal",
            headline: "ACME renewal: needs attention",
            summary: ["middle stage, 400000 minor units"],
            nextSteps: ["Re-engage the champion"],
            topSeverity: "critical",
            riskCount: 1,
          },
        ],
        marketSignals: [
          {
            signalType: "expansion",
            entity: "Acme Corp",
            headline: "Acme expands APAC",
            source: "licensed_wire",
            publishedAt: "2026-09-26T08:00:00Z",
            confidence: 0.9,
          },
        ],
        overdueActions: 1,
        evidence: [
          {
            type: "metric_definition",
            ref: "attainment_pct",
            label: "attainment_pct v3",
          },
        ],
      }),
    } as Response);

    const briefing = await getTodayBriefing("http://localhost:18000");
    expect(briefing.asOf).toBe("2026-09-27T08:00:00Z");
    expect(briefing.kpis).toHaveLength(1);
    expect(briefing.kpis[0].metricId).toBe("attainment_pct");
    expect(briefing.kpis[0].value).toBe(60.0);
  });

  it("maps network error to DEPENDENCY_UNAVAILABLE ApiRequestError", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError("Network error"));

    await expect(checkHealth("http://localhost:18000")).rejects.toThrow(ApiRequestError);
    await expect(checkHealth("http://localhost:18000")).rejects.toThrow(
      "Cannot reach the Northstar backend."
    );
  });

  it("maps non-200 HTTP error code to user-facing error message", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({
        code: "FORBIDDEN",
        message: "Internal forbidden detail",
      }),
    } as Response);

    await expect(askQuestion("http://localhost:18000", "test")).rejects.toThrow(
      "You do not have access to this data."
    );
  });
});
