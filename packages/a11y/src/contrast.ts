/** WCAG 2.2 contrast math and thresholds (§22: WCAG 2.2 AA for core flows). */

export const AA_NORMAL_TEXT = 4.5;
export const AA_LARGE_TEXT = 3.0;
export const AA_UI_COMPONENT = 3.0; // non-text UI (chart strokes, icons, focus indicators)

function channelToLinear(c8: number): number {
  const c = c8 / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

export function relativeLuminance(hex: string): number {
  const norm = hex.replace("#", "");
  if (norm.length !== 6 || !/^[0-9a-fA-F]{6}$/.test(norm)) {
    throw new Error(`invalid hex color: ${hex}`);
  }
  const r = Number.parseInt(norm.slice(0, 2), 16);
  const g = Number.parseInt(norm.slice(2, 4), 16);
  const b = Number.parseInt(norm.slice(4, 6), 16);
  return 0.2126 * channelToLinear(r) + 0.7152 * channelToLinear(g) + 0.0722 * channelToLinear(b);
}

export function contrastRatio(fgHex: string, bgHex: string): number {
  const l1 = relativeLuminance(fgHex);
  const l2 = relativeLuminance(bgHex);
  const [hi, lo] = l1 >= l2 ? [l1, l2] : [l2, l1];
  return (hi + 0.05) / (lo + 0.05);
}

export function meetsAA(fgHex: string, bgHex: string, threshold: number = AA_NORMAL_TEXT): boolean {
  return contrastRatio(fgHex, bgHex) >= threshold;
}
