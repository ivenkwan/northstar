/** Locale-aware formatting (PRD §22): dates, numbers, currency, fiscal period labels. */
import type { Locale } from "./locale.js";

const INTL_LOCALE: Readonly<Record<Locale, string>> = {
  "en-HK": "en-HK",
  "zh-Hant-HK": "zh-Hant-HK",
};

export function formatDate(iso: string, locale: Locale): string {
  return new Intl.DateTimeFormat(INTL_LOCALE[locale], { dateStyle: "medium" }).format(new Date(iso));
}

export function formatNumber(value: number, locale: Locale, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(INTL_LOCALE[locale], options).format(value);
}

/** Money renders in minor units as input (canonical model convention) with ISO-4217 currency. */
export function formatMoney(minorUnits: number, currency: string, locale: Locale): string {
  const scale = currency === "JPY" ? 0 : 2; // zero-decimal currency handling
  const value = minorUnits / 10 ** scale;
  return new Intl.NumberFormat(INTL_LOCALE[locale], { style: "currency", currency }).format(value);
}

/** Percent with the locale's conventions (attainment 61.4 → "61.4%"/"61.4%"). */
export function formatPercent(value: number, locale: Locale, fractionDigits = 1): string {
  return new Intl.NumberFormat(INTL_LOCALE[locale], {
    style: "percent",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value / 100);
}

/** Fiscal period labels (§8.3): "FY27-Q1" stays stable across locales; long form is localized. */
export function formatFiscalPeriod(period: string, locale: Locale): string {
  const match = /^FY(\d{2})-(Q[1-4]|M(0[1-9]|1[0-2])|FY)$/.exec(period);
  if (!match) return period;
  const year = match[1];
  const part = match[2];
  if (year === undefined || part === undefined) return period;
  if (locale === "zh-Hant-HK") {
    return `20${year}財年 ${part.startsWith("Q") ? part.replace("Q", "第") + "季" : part}`;
  }
  return `FY20${year} ${part}`;
}
