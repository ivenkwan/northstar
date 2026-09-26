import { describe, expect, it } from "vitest";

import {
  ConversationResponseSchema,
  DashboardDefinitionSchema,
  MAX_SUBGRAPH_NODES,
  SubgraphSchema,
  parseDeepLink,
} from "../src/index.js";

const validConversation = {
  messageId: "m1",
  answer: "Coverage is 2.1x.",
  scope: { type: "seller", id: "sp_1042", asOf: "2026-09-26T09:00:00Z" },
  components: [{ type: "narrative", payload: { text: "Coverage is 2.1x." } }],
  evidence: [{ type: "crm_record", ref: "opp_887", label: "Opportunity record" }],
  warnings: [],
  suggestedActions: [{ action: "create_follow_up_task", requiresConfirmation: true }],
};

const validDashboard = {
  title: "Monday Review",
  scope: { type: "team", id: "team_12" },
  layout: { mode: "mobile_grid", columns: 2 },
  cards: [
    { kind: "kpi", id: "c1", title: "Attainment", metric: "attainment_pct", position: [0, 0, 1, 1] },
    { kind: "bar", id: "c2", title: "Coverage", metric: "coverage", dimension: "salesperson", position: [0, 1, 2, 2] },
  ],
};

describe("conversation responses (CONV-03, §19.3)", () => {
  it("accepts a well-formed response", () => {
    const parsed = ConversationResponseSchema.parse(validConversation);
    expect(parsed.components[0]?.type).toBe("narrative");
  });
  it("rejects unknown component types and missing components", () => {
    const bad = { ...validConversation, components: [{ type: "hologram" }] };
    expect(ConversationResponseSchema.safeParse(bad).success).toBe(false);
    expect(ConversationResponseSchema.safeParse({ ...validConversation, components: [] }).success).toBe(false);
  });
});

describe("dashboard definitions (§8.5 — agent output must pass before render)", () => {
  it("accepts a valid definition and applies defaults", () => {
    const parsed = DashboardDefinitionSchema.parse(validDashboard);
    expect(parsed.refreshPolicy).toBe("on_open");
    expect(parsed.dashboardId).toBeNull();
  });
  it("rejects non-certified shape violations: empty cards, bad column range, unknown kind", () => {
    expect(DashboardDefinitionSchema.safeParse({ ...validDashboard, cards: [] }).success).toBe(false);
    expect(DashboardDefinitionSchema.safeParse({ ...validDashboard,
      layout: { mode: "mobile_grid", columns: 9 } }).success).toBe(false);
    expect(DashboardDefinitionSchema.safeParse({ ...validDashboard,
      cards: [{ kind: "iframe", id: "x", title: "t" }] }).success).toBe(false);
  });
  it("rejects executable content: payload fields do not exist on cards", () => {
    // dashboards are declarative cards, never free-form code (§8.5)
    expect(DashboardDefinitionSchema.safeParse({ ...validDashboard,
      cards: [{ kind: "kpi", id: "c", title: "t", metric: "m", script: "rm -rf" }] }).success).toBe(false);
  });
});

describe("bounded subgraphs (§18)", () => {
  const node = (id: string) => ({ id, kind: "organization" as const, label: id, provenance: ["src"] });

  it("accepts a coherent subgraph with provenance", () => {
    const g = { nodes: [node("a"), node("b")],
                edges: [{ id: "e1", source: "a", target: "b", relation: "affects", confidence: 0.9, provenance: ["s"] }] };
    expect(SubgraphSchema.safeParse(g).success).toBe(true);
  });
  it("rejects dangling edges, missing provenance, and over-bounds", () => {
    expect(SubgraphSchema.safeParse({ nodes: [node("a")],
      edges: [{ id: "e", source: "a", target: "ghost", relation: "r", confidence: 1, provenance: ["s"] }] }).success).toBe(false);
    expect(SubgraphSchema.safeParse({ nodes: [{ ...node("a"), provenance: [] }], edges: [] }).success).toBe(false);
    expect(SubgraphSchema.safeParse({
      nodes: Array.from({ length: MAX_SUBGRAPH_NODES + 1 }, (_, i) => node(`n${i}`)), edges: [],
    }).success).toBe(false);
  });
});

describe("deep links (§17.7 — validated before navigation)", () => {
  it("parses route and query params", () => {
    const link = parseDeepLink("northstar://Pipeline?period=FY27-Q1");
    expect(link).toEqual({ route: "Pipeline", period: "FY27-Q1" });
  });
  it("rejects unknown routes and malformed URLs with null, never a throw", () => {
    expect(parseDeepLink("northstar://AdminPanel")).toBeNull();
    expect(parseDeepLink("https://evil.example/Pipeline")).toBeNull();
    expect(parseDeepLink("garbage")).toBeNull();
  });
  it("forward-compatible extra params are dropped, not fatal (§23.4)", () => {
    const link = parseDeepLink("northstar://Dashboard?dashboardId=d1&futureParam=x");
    expect(link).toEqual({ route: "Dashboard", dashboardId: "d1" });
  });
});
