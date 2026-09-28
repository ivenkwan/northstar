/** Typed navigation (§17.7): single root parameter list; deep links runtime-validated first. */
import { parseDeepLink } from "@northstar/validation";

import type { AccountId, DashboardId, FiscalPeriod, SalespersonId, ThreadId } from "./ids";
import { accountId as mkAccount, dashboardId as mkDashboard, fiscalPeriod as mkPeriod, threadId as mkThread } from "./ids";

export type RootStackParamList = {
  Home: undefined;
  Today: undefined; // §10.1 first destination: briefing, alerts, target gap, priority actions
  Pipeline: Readonly<{ ownerId?: SalespersonId; period: FiscalPeriod }>;
  Account: Readonly<{ accountId: AccountId }>;
  Intelligence: Readonly<{ topic?: string }>;
  Dashboard: Readonly<{ dashboardId: DashboardId; revision?: number }>;
  Conversation: Readonly<{ threadId?: ThreadId }>;
};

export type RouteName = keyof RootStackParamList;

export type ResolvedRoute =
  | { route: "Home" }
  | { route: "Today" }
  | { route: "Pipeline"; params: RootStackParamList["Pipeline"] }
  | { route: "Account"; params: RootStackParamList["Account"] }
  | { route: "Intelligence"; params: RootStackParamList["Intelligence"] }
  | { route: "Dashboard"; params: RootStackParamList["Dashboard"] }
  | { route: "Conversation"; params: RootStackParamList["Conversation"] };

/** Deep link → typed route. Invalid links return null — navigation never throws.
 * Permission is re-checked at open time by the screen loader (§10.2). */
export function resolveDeepLink(url: string): ResolvedRoute | null {
  const link = parseDeepLink(url);
  if (link === null) return null;
  switch (link.route) {
    case "Home":
      return { route: "Home" };
    case "Today":
      return { route: "Today" };
    case "Pipeline":
      return { route: "Pipeline", params: { period: mkPeriod(link.period ?? "FY27-Q1") } };
    case "Account":
      return link.accountId === undefined ? null : { route: "Account", params: { accountId: mkAccount(link.accountId) } };
    case "Intelligence":
      return { route: "Intelligence", params: link.topic === undefined ? {} : { topic: link.topic } };
    case "Dashboard":
      return link.dashboardId === undefined ? null : { route: "Dashboard", params: { dashboardId: mkDashboard(link.dashboardId) } };
    case "Conversation":
      return { route: "Conversation", params: link.threadId === undefined ? {} : { threadId: mkThread(link.threadId) } };
  }
}
