/** Branded identifiers (§17.7): a TeamId can never be passed where a DomainId is expected. */

declare const brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [brand]: B };

export type SalespersonId = Brand<string, "SalespersonId">;
export type TeamId = Brand<string, "TeamId">;
export type DomainId = Brand<string, "DomainId">;
export type GroupId = Brand<string, "GroupId">;
export type AccountId = Brand<string, "AccountId">;
export type DashboardId = Brand<string, "DashboardId">;
export type ThreadId = Brand<string, "ThreadId">;
export type FiscalPeriod = Brand<string, "FiscalPeriod">;

export const salespersonId = (v: string): SalespersonId => v as SalespersonId;
export const teamId = (v: string): TeamId => v as TeamId;
export const domainId = (v: string): DomainId => v as DomainId;
export const groupId = (v: string): GroupId => v as GroupId;
export const accountId = (v: string): AccountId => v as AccountId;
export const dashboardId = (v: string): DashboardId => v as DashboardId;
export const threadId = (v: string): ThreadId => v as ThreadId;
export const fiscalPeriod = (v: string): FiscalPeriod => v as FiscalPeriod;
