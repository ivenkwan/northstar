import { describe, expect, it } from "vitest";
import type { DashboardDefinition } from "@northstar/validation";
import {
  rendererFor,
  widgetsFrom,
  WIDGET_RENDERERS,
  type DashboardWidget,
} from "../src/widgets";

describe("apps/mobile widget registry & ADR-036 compliance", () => {
  it("resolves renderers and ensures tableAlternative is required for charts", () => {
    const kpiWidget: DashboardWidget = {
      kind: "kpi",
      id: "w_kpi",
      title: "Attainment",
      metric: "attainment_pct",
    };
    const barWidget: DashboardWidget = {
      kind: "bar",
      id: "w_bar",
      title: "Pipeline by Stage",
      metric: "weighted_pipeline",
      dimension: "stage",
    };
    const tableWidget: DashboardWidget = {
      kind: "table",
      id: "w_table",
      title: "Deals Table",
      query: "SELECT * FROM deals",
    };

    expect(rendererFor(kpiWidget)).toEqual({ renderer: "kpi", tableAlternative: true });
    expect(rendererFor(barWidget)).toEqual({ renderer: "bar", tableAlternative: true });
    expect(rendererFor(tableWidget)).toEqual({ renderer: "table", tableAlternative: true });
  });

  it("verifies that WIDGET_RENDERERS registry maps all renderer keys to tableAlternative: true", () => {
    expect(WIDGET_RENDERERS.narrative.tableAlternative).toBe(true);
    expect(WIDGET_RENDERERS.kpi.tableAlternative).toBe(true);
    expect(WIDGET_RENDERERS.bar.tableAlternative).toBe(true);
    expect(WIDGET_RENDERERS.table.tableAlternative).toBe(true);
  });

  it("transforms Zod-validated DashboardDefinition cards into typed DashboardWidgets", () => {
    const definition: DashboardDefinition = {
      dashboardId: "dash_1",
      title: "Sales Executive Dashboard",
      scope: { type: "seller", id: "user_1" },
      layout: { mode: "mobile_grid", columns: 2 },
      cards: [
        {
          kind: "kpi",
          id: "c1",
          title: "Quota Attainment",
          metric: "attainment_pct",
          position: [0, 0, 1, 1],
        },
        {
          kind: "bar",
          id: "c2",
          title: "Pipeline by Domain",
          metric: "weighted_pipeline",
          dimension: "domain",
          position: [1, 0, 1, 1],
        },
        {
          kind: "table",
          id: "c3",
          title: "Top Deals",
          query: "deals_query",
          position: [2, 0, 2, 1],
        },
      ],
    };

    const widgets = widgetsFrom(definition);
    expect(widgets).toHaveLength(3);
    expect(widgets[0]).toEqual({
      kind: "kpi",
      id: "c1",
      title: "Quota Attainment",
      metric: "attainment_pct",
    });
    expect(widgets[1]).toEqual({
      kind: "bar",
      id: "c2",
      title: "Pipeline by Domain",
      metric: "weighted_pipeline",
      dimension: "domain",
    });
    expect(widgets[2]).toEqual({
      kind: "table",
      id: "c3",
      title: "Top Deals",
      query: "deals_query",
    });
  });
});
