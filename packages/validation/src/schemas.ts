/** Zod runtime boundary schemas (PRD §17.1, ADR-026).
 *
 * Every untrusted dynamic payload crosses one of these before it reaches UI or
 * domain code: agent/dashboard/graph output and deep links. Unknown extra
 * fields are stripped (forward compatibility, §23.4); malformed input rejects.
 */
import { z } from "zod";

/** Conversation components (CONV-03 / §19.3) — discriminated by `type`. */
export const ComponentSchema = z.object({
  type: z.enum(["narrative", "kpi", "kpi_table", "chart", "table", "evidence_chips"]),
  title: z.string().optional(),
  payload: z.record(z.unknown()).default({}),
  datasetRef: z.string().optional(),
  metricDefinitionId: z.string().optional(),
}).strict();

export const EvidenceRefSchema = z.object({
  type: z.enum(["crm_record", "plan_row", "news_item", "metric_definition"]),
  ref: z.string(),
  label: z.string(),
}).strict();

export const ConversationResponseSchema = z.object({
  messageId: z.string(),
  answer: z.string(),
  scope: z.object({ type: z.string(), id: z.string(), asOf: z.string() }),
  components: z.array(ComponentSchema).min(1),
  evidence: z.array(EvidenceRefSchema).default([]),
  warnings: z.array(z.string()).default([]),
  suggestedActions: z.array(z.object({
    action: z.string(),
    requiresConfirmation: z.boolean(),
  })).default([]),
}).strict();
export type ConversationResponse = z.infer<typeof ConversationResponseSchema>;

/** Dashboard definitions (§8.5, §10.3) — agent output must pass this AND
 * server-side authorization before rendering (ADR-026). */
const position = z.tuple([z.number().int(), z.number().int(), z.number().int(), z.number().int()]);

export const DashboardCardSchema = z.discriminatedUnion("kind", [
  z.object({
    kind: z.literal("kpi"),
    id: z.string(), title: z.string(),
    metric: z.string(),
    position: position.optional(),
  }).strict(),  // declarative cards only — unknown fields (e.g. script) reject (§8.5)
  z.object({
    kind: z.literal("bar"),
    id: z.string(), title: z.string(),
    metric: z.string(), dimension: z.string(),
    position: position.optional(),
  }).strict(),
  z.object({
    kind: z.literal("table"),
    id: z.string(), title: z.string(),
    query: z.string(),
    position: position.optional(),
  }).strict(),
]);
export type DashboardCard = z.infer<typeof DashboardCardSchema>;

export const DashboardDefinitionSchema = z.object({
  dashboardId: z.string().nullable().default(null),
  title: z.string().min(1),
  scope: z.object({
    type: z.enum(["seller", "team", "domain", "group"]),
    id: z.string(),
  }),
  globalFilters: z.record(z.unknown()).default({}),
  layout: z.object({
    mode: z.enum(["mobile_grid", "tablet_grid"]),
    columns: z.number().int().min(1).max(4),
  }),
  cards: z.array(DashboardCardSchema).min(1),
  refreshPolicy: z.enum(["on_open", "scheduled"]).default("on_open"),
  sharing: z.string().default("private"),
});
export type DashboardDefinition = z.infer<typeof DashboardDefinitionSchema>;

/** Knowledge-graph bounded subgraphs (§18) — provenance mandatory. */
export const GraphNodeSchema = z.object({
  id: z.string(),
  kind: z.enum(["organization", "industry", "domain", "group", "person", "product", "event"]),
  label: z.string(),
  attributes: z.record(z.unknown()).default({}),
  provenance: z.array(z.string()).min(1),  // every node carries provenance
});

export const GraphEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  relation: z.string(),
  confidence: z.number().min(0).max(1),
  provenance: z.array(z.string()).min(1),
});

export const MAX_SUBGRAPH_NODES = 50;
export const MAX_SUBGRAPH_EDGES = 100;

export const SubgraphSchema = z.object({
  nodes: z.array(GraphNodeSchema).max(MAX_SUBGRAPH_NODES),
  edges: z.array(GraphEdgeSchema).max(MAX_SUBGRAPH_EDGES),
}).superRefine((g, ctx) => {
  const ids = new Set(g.nodes.map((n) => n.id));
  if (ids.size !== g.nodes.length) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "duplicate node ids" });
  }
  for (const e of g.edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: `edge ${e.id} references unknown node` });
    }
  }
});
export type Subgraph = z.infer<typeof SubgraphSchema>;

/** Deep links (§17.7) — runtime-validated before navigation; permission check at open. */
export const DeepLinkSchema = z.object({
  route: z.enum(["Home", "Pipeline", "Account", "Intelligence", "Dashboard", "Conversation"]),
  accountId: z.string().optional(),
  dashboardId: z.string().optional(),
  threadId: z.string().optional(),
  topic: z.string().optional(),
  period: z.string().optional(),
});
export type DeepLink = z.infer<typeof DeepLinkSchema>;

export function parseDeepLink(url: string): DeepLink | null {
  // northstar://Pipeline?period=FY27-Q1 → validated shape or null (never throws into navigation)
  const m = /^northstar:\/\/([A-Za-z]+)(\?.*)?$/.exec(url);
  if (m === null || m[1] === undefined) return null;
  const params: Record<string, string> = {};
  const query = m[2] ?? "";
  for (const pair of query.replace(/^\?/, "").split("&")) {
    if (pair === "") continue;
    const [k, v = ""] = pair.split("=");
    if (k === undefined) continue;
    params[k] = decodeURIComponent(v);
  }
  const result = DeepLinkSchema.safeParse({ route: m[1], ...params });
  return result.success ? result.data : null;
}
