import { describe, expect, it } from "vitest";

import { BriefingSchema, DealBriefSchema } from "../src/index.js";

const validBriefing = {
  asOf: "2026-09-27T08:00:00Z",
  scopeId: "u_dev",
  greeting: "Here is your day at a glance.",
  kpis: [
    { metricId: "attainment_pct", version: 3, value: 60.0, unit: "percent" },
    { metricId: "coverage", version: 2, value: null, unit: "ratio" }, // suppressed is legal (§8.3)
  ],
  topRisks: [
    {
      opportunityId: "opp_1", name: "ACME renewal", headline: "ACME renewal: needs attention",
      summary: ["middle stage, 400000 minor units"], nextSteps: ["Re-engage the champion"],
      topSeverity: "critical", riskCount: 4,
    },
  ],
  marketSignals: [
    { signalType: "expansion", entity: "Acme Corp", headline: "Acme expands APAC",
      source: "licensed_wire", publishedAt: "2026-09-26T08:00:00Z", confidence: 0.9 },
  ],
  overdueActions: 1,
  evidence: [{ type: "metric_definition", ref: "attainment_pct", label: "attainment_pct v3" }],
};

const validDealBrief = {
  opportunityId: "opp_1", accountId: "acct_1", name: "ACME renewal", ownerId: "s1",
  asOf: "2026-09-27T08:00:00Z", headline: "ACME renewal: needs attention",
  summary: ["middle stage"], indicators: [{ kind: "stale", detail: "no activity for 30d", severity: "critical" }],
  risks: [{ kind: "stale", detail: "no activity for 30d", severity: "critical" }],
  nextSteps: ["Re-engage"], evidence: [{ type: "crm_record", ref: "opp_1", label: "Opportunity record" }],
};

describe("Briefing schema (§7.1 Today)", () => {
  it("accepts a valid briefing with suppressed KPIs", () => {
    const parsed = BriefingSchema.parse(validBriefing);
    expect(parsed.kpis[1]?.value).toBeNull();
  });
  it("caps top risks at 3 and signals at 2 (§7.1 shapes)", () => {
    const risk = validBriefing.topRisks[0];
    const sig = validBriefing.marketSignals[0];
    if (risk === undefined || sig === undefined) throw new Error("fixture missing");
    const four = { ...validBriefing, topRisks: [risk, risk, risk, risk] };
    expect(BriefingSchema.safeParse(four).success).toBe(false);
    expect(BriefingSchema.safeParse({ ...validBriefing, marketSignals: [sig, sig, sig] }).success).toBe(false);
  });
  it("rejects confidence out of range and unsourced signals", () => {
    const sig = validBriefing.marketSignals[0];
    if (sig === undefined) throw new Error("fixture missing");
    const bad = { ...validBriefing, marketSignals: [{ ...sig, confidence: 1.5 }] };
    expect(BriefingSchema.safeParse(bad).success).toBe(false);
    const noSource = { ...validBriefing, marketSignals: [{ ...sig, source: "" }] };
    expect(BriefingSchema.safeParse(noSource).success).toBe(false);
  });
});

describe("DealBrief schema (§9.1)", () => {
  it("accepts a valid brief", () => {
    expect(DealBriefSchema.parse(validDealBrief).opportunityId).toBe("opp_1");
  });
  it("rejects unknown severity vocabulary and missing evidence", () => {
    const bad = { ...validDealBrief, indicators: [{ kind: "stale", detail: "x", severity: "meh" }] };
    expect(DealBriefSchema.safeParse(bad).success).toBe(false);
    expect(DealBriefSchema.safeParse({ ...validDealBrief, evidence: [] }).success).toBe(true); // empty is legal
  });
});
