/** Briefing wire schemas (§7.1 Today, §9.1 deal brief) — the boundary the
 * mobile Today screen validates against (ADR-026). Mirrors the OpenAPI
 * components: packages/contracts regenerates from the same source. */
import { z } from "zod";

export const EvidenceItemSchema = z.object({
  type: z.string(),
  ref: z.string(),
  label: z.string(),
}).strict();

export const KpiEntrySchema = z.object({
  metricId: z.string(),
  version: z.number().int(),
  value: z.number().nullable(), // null = suppressed per §8.3 guards
  unit: z.enum(["percent", "ratio", "minor", "raw"]),
}).strict();

export const HealthIndicatorSchema = z.object({
  kind: z.string(),
  detail: z.string(),
  severity: z.enum(["warning", "critical"]),
}).strict();

export const SignalItemSchema = z.object({
  signalType: z.string(),
  entity: z.string(),
  headline: z.string(),
  source: z.string().min(1),   // sourced signals only (§8.4) — empty source rejects
  publishedAt: z.string(),
  confidence: z.number().min(0).max(1),
}).strict();

export const BriefingRiskSchema = z.object({
  opportunityId: z.string(),
  name: z.string(),
  headline: z.string(),
  summary: z.array(z.string()),
  nextSteps: z.array(z.string()),
  topSeverity: z.enum(["warning", "critical", "none"]),
  riskCount: z.number().int().min(0),
}).strict();

export const BriefingSchema = z.object({
  asOf: z.string(),
  scopeId: z.string(),
  greeting: z.string(),
  kpis: z.array(KpiEntrySchema),
  topRisks: z.array(BriefingRiskSchema).max(3),  // §7.1: top three risks
  marketSignals: z.array(SignalItemSchema).max(2), // §7.1: two evidence-backed signals
  overdueActions: z.number().int().min(0),
  evidence: z.array(EvidenceItemSchema),
});
export type Briefing = z.infer<typeof BriefingSchema>;

export const DealBriefSchema = z.object({
  opportunityId: z.string(),
  accountId: z.string(),
  name: z.string(),
  ownerId: z.string(),
  asOf: z.string(),
  headline: z.string(),
  summary: z.array(z.string()),
  indicators: z.array(HealthIndicatorSchema),
  risks: z.array(HealthIndicatorSchema),
  nextSteps: z.array(z.string()),
  evidence: z.array(EvidenceItemSchema),
});
export type DealBrief = z.infer<typeof DealBriefSchema>;
