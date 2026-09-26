/** Dashboard widgets (§17.5): discriminated union + exhaustive renderer registry.
 * Every chart kind has a registered table alternative (ADR-036 accessibility rule). */
import type { DashboardDefinition } from "@northstar/validation";

export type WidgetRendererKey =
  | "narrative"
  | "kpi"
  | "bar"
  | "table";

export type DashboardWidget =
  | { readonly kind: "kpi"; readonly id: string; readonly title: string; readonly metric: string }
  | { readonly kind: "bar"; readonly id: string; readonly title: string; readonly metric: string; readonly dimension: string }
  | { readonly kind: "table"; readonly id: string; readonly title: string; readonly query: string };

/** chart kinds that MUST carry a data-table alternative (ADR-036 / §23.4 gate). */
const TABLE_ALTERNATIVE_REQUIRED_FOR: readonly WidgetRendererKey[] = ["bar"];

export const WIDGET_RENDERERS: Readonly<Record<WidgetRendererKey, { tableAlternative: boolean }>> = {
  narrative: { tableAlternative: true },   // narrative has an a11y text equivalent
  kpi: { tableAlternative: true },
  bar: { tableAlternative: true },        // chart → focus-view table equivalent
  table: { tableAlternative: true },      // is its own table
};

/** Exhaustiveness guard (§17.5): adding a widget kind without a renderer fails to compile. */
function assertExhaustive(kind: never): never {
  throw new Error(`unhandled widget kind: ${String(kind)}`);
}

export function rendererFor(widget: DashboardWidget): { renderer: WidgetRendererKey; tableAlternative: boolean } {
  switch (widget.kind) {
    case "kpi":
    case "bar":
    case "table": {
      const renderer = widget.kind satisfies WidgetRendererKey;
      const meta = WIDGET_RENDERERS[renderer];
      if (meta === undefined || (!meta.tableAlternative && TABLE_ALTERNATIVE_REQUIRED_FOR.includes(renderer))) {
        throw new Error(`widget kind ${widget.kind} missing required table alternative`);
      }
      return { renderer, tableAlternative: true };
    }
    default:
      return assertExhaustive(widget);
  }
}

/** Validated dashboard (Zod at the boundary) → typed widgets for renderers. */
export function widgetsFrom(definition: DashboardDefinition): DashboardWidget[] {
  return definition.cards.map((card): DashboardWidget => {
    switch (card.kind) {
      case "kpi":
        return { kind: "kpi", id: card.id, title: card.title, metric: card.metric };
      case "bar":
        return { kind: "bar", id: card.id, title: card.title, metric: card.metric, dimension: card.dimension };
      case "table":
        return { kind: "table", id: card.id, title: card.title, query: card.query };
    }
  });
}
