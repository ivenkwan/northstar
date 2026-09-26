import { describe, expect, it } from "vitest";
import { DashboardDefinitionSchema } from "@northstar/validation";

import { rendererFor, resolveDeepLink, widgetsFrom } from "../src/index.js";

describe("typed deep links (§17.7)", () => {
  it("resolves valid links into typed routes", () => {
    const r = resolveDeepLink("northstar://Account?accountId=acct_9");
    expect(r).toEqual({ route: "Account", params: { accountId: "acct_9" } });
  });
  it("requires required params: Account without accountId is rejected", () => {
    expect(resolveDeepLink("northstar://Account")).toBeNull();
  });
  it("drops unknown extras (forward-compatible) and never throws", () => {
    const r = resolveDeepLink("northstar://Dashboard?dashboardId=d1&newParam=whatever");
    expect(r).toEqual({ route: "Dashboard", params: { dashboardId: "d1" } });
    expect(resolveDeepLink("javascript:alert(1)")).toBeNull();
  });
});

describe("widget union + exhaustive registry (§17.5, ADR-036)", () => {
  const definition = DashboardDefinitionSchema.parse({
    title: "Monday Review",
    scope: { type: "team", id: "team_12" },
    layout: { mode: "mobile_grid", columns: 2 },
    cards: [
      { kind: "kpi", id: "c1", title: "Attainment", metric: "attainment_pct" },
      { kind: "bar", id: "c2", title: "Coverage", metric: "coverage", dimension: "salesperson" },
      { kind: "table", id: "c3", title: "Stalled", query: "stalled_opportunities" },
    ],
  });

  it("maps validated dashboard cards to typed widgets", () => {
    const widgets = widgetsFrom(definition);
    expect(widgets.map((w) => w.kind)).toEqual(["kpi", "bar", "table"]);
  });

  it("every widget kind has a renderer with a table alternative", () => {
    for (const w of widgetsFrom(definition)) {
      const { renderer, tableAlternative } = rendererFor(w);
      expect(renderer).toBe(w.kind);
      expect(tableAlternative).toBe(true);  // ADR-036: no chart without its table
    }
  });
});
