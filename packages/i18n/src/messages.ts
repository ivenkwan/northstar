/** Message catalogs (en + zh-Hant). Keys are stable ids; missing keys fall back to English. */
export const MESSAGE_KEYS = [
  "today.title",
  "ask.placeholder",
  "dashboard.title",
  "pipeline.title",
  "intelligence.title",
  "error.ai_credential_unavailable",
  "error.forbidden",
  "metric.attainment_pct",
  "metric.coverage",
  "metric.forecast_gap",
  "alert.quiet_hours_active",
  "action.confirm_title",
] as const;

export type MessageKey = (typeof MESSAGE_KEYS)[number];

export const CATALOGS: Readonly<Record<string, Readonly<Record<MessageKey, string>>>> = {
  en: {
    "today.title": "Today",
    "ask.placeholder": "Ask about your pipeline…",
    "dashboard.title": "Dashboard",
    "pipeline.title": "Pipeline",
    "intelligence.title": "Intelligence",
    "error.ai_credential_unavailable": "The AI service is unavailable. Contact your administrator.",
    "error.forbidden": "You do not have access to this data.",
    "metric.attainment_pct": "Attainment %",
    "metric.coverage": "Coverage",
    "metric.forecast_gap": "Forecast Gap",
    "alert.quiet_hours_active": "Quiet hours are active; delivery is paused.",
    "action.confirm_title": "Confirm this action",
  },
  "zh-Hant": {
    "today.title": "今日",
    "ask.placeholder": "詢問你的銷售管道…",
    "dashboard.title": "儀表板",
    "pipeline.title": "銷售管道",
    "intelligence.title": "市場情報",
    "error.ai_credential_unavailable": "AI 服務暫時無法使用，請聯絡你的管理員。",
    "error.forbidden": "你沒有存取這些資料的權限。",
    "metric.attainment_pct": "達成率 %",
    "metric.coverage": "管道覆蓋率",
    "metric.forecast_gap": "預測差距",
    "alert.quiet_hours_active": "靜音時段生效中，暫停傳送通知。",
    "action.confirm_title": "確認此操作",
  },
};

export type CatalogLanguage = keyof typeof CATALOGS;

export function t(key: MessageKey, language: CatalogLanguage): string {
  const catalog = CATALOGS[language];
  const fallback = CATALOGS["en"];
  return catalog?.[key] ?? fallback?.[key] ?? key;
}
