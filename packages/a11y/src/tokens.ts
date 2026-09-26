/** Design tokens and the automated WCAG 2.2 AA gates over them (§22, §23.4).
 *
 * The external accessibility review remains a Phase 2 [INPUT REQUIRED] item;
 * these gates are the automated floor: contrast pairs, target sizes, and the
 * no-color-only-encoding rule for status indicators.
 */

export const TOKENS = {
  color: {
    bg: "#FFFFFF",
    surfaceMuted: "#F5F7FA",
    textPrimary: "#1A2333",
    textSecondary: "#4A5568",
    textOnAccent: "#FFFFFF",
    accent: "#0B5CC0",
    riskHigh: "#B3261E",
    riskMedium: "#8A6D00",
    riskLow: "#1E6B3A",
    chartPrimary: "#0B5CC0",
    chartGrid: "#C9D2DE",
  },
  /** Minimum touch target (points) — §10.2 one-handed use / WCAG 2.2 AA 2.5.8. */
  minTargetPoints: 44,
  /** Dynamic type must remain usable at this scale before layouts may reflow-break. */
  maxDynamicTypeScale: 2.0,
} as const;

/** Foreground/background pairs that must satisfy AA normal-text contrast. */
export const TEXT_CONTRAST_PAIRS: readonly (readonly [string, string])[] = [
  ["textPrimary", "bg"],
  ["textPrimary", "surfaceMuted"],
  ["textSecondary", "bg"],
  ["textOnAccent", "accent"],
];

/** Status/UI colors measured against the page background; AA non-text threshold. */
export const UI_CONTRAST_PAIRS: readonly (readonly [string, string])[] = [
  ["riskHigh", "bg"],
  ["riskMedium", "bg"],
  ["riskLow", "bg"],
  ["chartPrimary", "bg"],
];

/**
 * Risk indicators must never encode meaning by color alone (§ ux-ia-blueprint):
 * every status color is paired with a mandatory text label id.
 */
export const STATUS_LABELS: Readonly<Record<string, string>> = {
  riskHigh: "status.risk.high",
  riskMedium: "status.risk.medium",
  riskLow: "status.risk.low",
};
