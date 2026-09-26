import { describe, expect, it } from "vitest";

import { CATALOGS, formatFiscalPeriod, formatMoney, formatPercent, negotiateLocale, t } from "../src/index.js";

describe("locale negotiation (Accept-Language)", () => {
  it("prefers explicit Traditional Chinese", () => {
    expect(negotiateLocale("zh-Hant-HK,zh;q=0.9,en;q=0.8")).toBe("zh-Hant-HK");
    expect(negotiateLocale("zh-TW")).toBe("zh-Hant-HK");
  });
  it("defaults generic zh to Traditional (HK deployment)", () => {
    expect(negotiateLocale("zh")).toBe("zh-Hant-HK");
  });
  it("respects q-weights", () => {
    expect(negotiateLocale("en;q=0.9, zh-Hant;q=1.0")).toBe("zh-Hant-HK");
    expect(negotiateLocale("en-GB,en;q=0.9")).toBe("en-HK");
  });
  it("falls back to default on garbage or empty", () => {
    expect(negotiateLocale(undefined)).toBe("en-HK");
    expect(negotiateLocale("fr-FR")).toBe("en-HK");
  });
});

describe("catalogs (§22 localization)", () => {
  it("every key exists in every catalog — no partial translations", () => {
    const enKeys = Object.keys(CATALOGS.en).sort();
    for (const lang of Object.keys(CATALOGS)) {
      expect(Object.keys(CATALOGS[lang] ?? {}).sort()).toEqual(enKeys);
    }
  });
  it("translates navigation and error strings", () => {
    expect(t("today.title", "zh-Hant")).toBe("今日");
    expect(t("error.forbidden", "zh-Hant")).toContain("權限");
    expect(t("today.title", "en")).toBe("Today");
  });
});

describe("formatting", () => {
  it("money uses locale currency conventions from minor units", () => {
    const en = formatMoney(1_234_560, "HKD", "en-HK");
    const zh = formatMoney(1_234_560, "HKD", "zh-Hant-HK");
    expect(en).toContain("12,345.60");
    expect(zh).toContain("12,345.60");
    expect(en.startsWith("HK$")).toBe(true); // HK dollar display convention in both locales
  });
  it("handles zero-decimal currencies", () => {
    expect(formatMoney(1000, "JPY", "en-HK")).toContain("1,000");
  });
  it("percent formats attainment", () => {
    expect(formatPercent(61.4, "en-HK")).toBe("61.4%");
  });
  it("fiscal labels: stable id preserved, long form localized", () => {
    expect(formatFiscalPeriod("FY27-Q1", "en-HK")).toBe("FY2027 Q1");
    expect(formatFiscalPeriod("FY27-Q1", "zh-Hant-HK")).toBe("2027財年 第1季");
    expect(formatFiscalPeriod("not-a-period", "en-HK")).toBe("not-a-period"); // never mangles unknown ids
  });
});
