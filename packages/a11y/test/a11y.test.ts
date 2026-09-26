import { describe, expect, it } from "vitest";

import { AA_NORMAL_TEXT, AA_UI_COMPONENT, contrastRatio, meetsAA } from "../src/contrast.js";
import { STATUS_LABELS, TEXT_CONTRAST_PAIRS, TOKENS, UI_CONTRAST_PAIRS } from "../src/tokens.js";

describe("contrast math", () => {
  it("computes the canonical black/white ratio", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 0);
  });
  it("is symmetric", () => {
    expect(contrastRatio("#0B5CC0", "#FFFFFF")).toBeCloseTo(contrastRatio("#FFFFFF", "#0B5CC0"), 10);
  });
  it("rejects invalid colors", () => {
    expect(() => contrastRatio("nope", "#FFF")).toThrow();
  });
});

describe("design tokens meet WCAG 2.2 AA (automated §23.4 floor)", () => {
  it("text pairs clear 4.5:1", () => {
    for (const [fg, bg] of TEXT_CONTRAST_PAIRS) {
      const ratio = contrastRatio(TOKENS.color[fg as keyof typeof TOKENS.color], TOKENS.color[bg as keyof typeof TOKENS.color]);
      expect(ratio, `${fg} on ${bg} = ${ratio.toFixed(2)}:1`).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
    }
  });
  it("status/chart colors clear 3:1 against the page background", () => {
    for (const [fg, bg] of UI_CONTRAST_PAIRS) {
      const ratio = contrastRatio(TOKENS.color[fg as keyof typeof TOKENS.color], TOKENS.color[bg as keyof typeof TOKENS.color]);
      expect(ratio, `${fg} on ${bg} = ${ratio.toFixed(2)}:1`).toBeGreaterThanOrEqual(AA_UI_COMPONENT);
    }
  });
  it("touch targets satisfy the 44pt minimum (WCAG 2.5.8 / §10.2)", () => {
    expect(TOKENS.minTargetPoints).toBeGreaterThanOrEqual(44);
  });
  it("no status is color-only: every risk color has a label id", () => {
    for (const key of ["riskHigh", "riskMedium", "riskLow"] as const) {
      expect(STATUS_LABELS[key]).toMatch(/^status\./);
    }
  });
  it("meetsAA helper agrees with raw ratios", () => {
    expect(meetsAA("#1A2333", "#FFFFFF")).toBe(true);
    expect(meetsAA("#C9D2DE", "#FFFFFF")).toBe(false); // grid grey fails text AA
  });
});
