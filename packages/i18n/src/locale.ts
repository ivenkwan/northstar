/** Supported locales (PRD §22: English first, Traditional Chinese next). */
export const SUPPORTED_LOCALES = ["en-HK", "zh-Hant-HK"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en-HK";

/** Negotiates a supported locale from an Accept-Language header (BFF uses this). */
export function negotiateLocale(acceptLanguage: string | undefined): Locale {
  if (!acceptLanguage) return DEFAULT_LOCALE;
  const candidates = acceptLanguage
    .split(",")
    .map((part) => {
      const [rawTag, ...params] = part.trim().split(";");
      const q = params.find((p) => p.trim().startsWith("q="));
      const tag = (rawTag ?? "").trim().toLowerCase();
      return { tag, q: q ? Number.parseFloat(q.slice(2)) : 1 };
    })
    .sort((a, b) => b.q - a.q);
  for (const { tag } of candidates) {
    if (tag === undefined) continue;
    if (tag.startsWith("zh-hant") || tag === "zh-tw" || tag === "zh-hk") return "zh-Hant-HK";
    if (tag.startsWith("zh")) return "zh-Hant-HK"; // default Chinese variant: Traditional (HK deployment)
    if (tag.startsWith("en")) return "en-HK";
  }
  return DEFAULT_LOCALE;
}
