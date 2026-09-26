-- Sales Northstar — canonical model draft v0.1 (Phase 0)
-- PostgreSQL DDL for the PRD §14.1 entities. Draft for review; becomes Track C's
-- migration baseline after discovery answers are folded in (docs/discovery README, A-1..A-7).
-- Conventions:
--   * All organizational membership/allocation rows are effective-dated (PRD §6.1):
--       valid_from inclusive, valid_to exclusive, NULL valid_to = current.
--   * Money is stored as amount MINOR UNITS (bigint) + ISO-4217 currency; no floats.
--   * Surrogate UUID PKs; source-system IDs kept with system discriminator (CRM-agnostic, §4.1).

CREATE TYPE org_role        AS ENUM ('seller','team_manager','domain_leader','group_leader','sales_ops','executive','platform_admin','auditor');            -- §5
CREATE TYPE reporting_role  AS ENUM ('primary','secondary','overlay','virtual');                                                                            -- §6.2
CREATE TYPE agg_policy      AS ENUM ('full_view','proportional_allocation','primary_only','excluded_from_enterprise_total');                                  -- §6.2
CREATE TYPE forecast_cat    AS ENUM ('pipeline','best_case','commit','closed','other');                                                                       -- §8.2
CREATE TYPE plan_assignee   AS ENUM ('salesperson','team','domain','group','product','combination');                                                           -- §8.3
CREATE TYPE signal_type     AS ENUM ('funding','leadership','expansion','procurement','regulation','partnership','earnings','incident','product_launch','merger','risk','intent'); -- §8.4

-- Reference tables first (no forward FK references allowed in PostgreSQL DDL)
CREATE TABLE currency (
  code               char(3) PRIMARY KEY,             -- ISO 4217
  minor_unit_scale   int NOT NULL DEFAULT 2
);

CREATE TABLE fiscal_calendar (
  fiscal_calendar_id uuid PRIMARY KEY,
  name               text NOT NULL,
  year_start_month   int NOT NULL DEFAULT 1           -- A-2; questionnaire Q3.1
);

CREATE TABLE fiscal_period (
  period_id          uuid PRIMARY KEY,
  fiscal_calendar_id uuid NOT NULL REFERENCES fiscal_calendar(fiscal_calendar_id),
  period_kind        text NOT NULL CHECK (period_kind IN ('year','quarter','month','custom')),
  label              text NOT NULL,                   -- FY27-Q1
  starts_on          date NOT NULL,
  ends_on            date NOT NULL,
  CHECK (starts_on < ends_on),
  UNIQUE (fiscal_calendar_id, label)
);

-- §14.2 semantic layer anchor (full catalog: data/semantic-layer/metric-catalog.yaml)
CREATE TABLE metric_definition (
  metric_id          text PRIMARY KEY,                -- e.g. 'attainment_pct'
  version            int NOT NULL,
  name               text NOT NULL,
  formula            text NOT NULL,                   -- governed expression; rendered by lineage API (§19.2)
  grain              text NOT NULL,
  dimensions         text[] NOT NULL DEFAULT '{}',
  owner              text NOT NULL,
  certification      text NOT NULL DEFAULT 'draft',   -- draft/certified/deprecated
  UNIQUE (metric_id, version)
);

-- §14.1 User / SalesPerson
CREATE TABLE app_user (
  user_id            uuid PRIMARY KEY,
  identity_provider_id text NOT NULL UNIQUE,          -- IdP subject (Q6.1)
  display_name       text NOT NULL,
  status             text NOT NULL DEFAULT 'active',
  locale             text NOT NULL DEFAULT 'en-HK',
  time_zone          text NOT NULL DEFAULT 'Asia/Hong_Kong',
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE salesperson (
  salesperson_id     uuid PRIMARY KEY,
  user_id            uuid NOT NULL REFERENCES app_user(user_id),
  employee_ref       text,                            -- HR system reference
  primary_team_id    uuid,                            -- FK added after team; exactly one at a point in time (§6.1)
  valid_from         date NOT NULL,
  valid_to           date,                            -- history preserved for transfers
  UNIQUE (user_id, valid_from)
);

-- §6 organization
CREATE TABLE domain (
  domain_id          uuid PRIMARY KEY,
  owner_id           uuid REFERENCES salesperson(salesperson_id),
  taxonomy_code      text NOT NULL,
  name               text NOT NULL,
  currency           char(3) NOT NULL REFERENCES currency(code),
  fiscal_calendar_id uuid NOT NULL REFERENCES fiscal_calendar(fiscal_calendar_id),
  valid_from         date NOT NULL,
  valid_to           date
);

CREATE TABLE sales_group (
  group_id           uuid PRIMARY KEY,
  owner_id           uuid REFERENCES salesperson(salesperson_id),
  group_type         text NOT NULL,                   -- §14.1 SalesGroup.type
  name               text NOT NULL,
  valid_from         date NOT NULL,
  valid_to           date
);

CREATE TABLE team (
  team_id            uuid PRIMARY KEY,
  domain_id          uuid NOT NULL REFERENCES domain(domain_id),   -- exactly one domain at a time (§6.1)
  manager_id         uuid NOT NULL REFERENCES salesperson(salesperson_id),
  name               text NOT NULL,
  valid_from         date NOT NULL,
  valid_to           date
);
ALTER TABLE salesperson ADD CONSTRAINT fk_primary_team
  FOREIGN KEY (primary_team_id) REFERENCES team(team_id);

-- §6.2 multi-group attribution: the double-counting guard lives here
CREATE TABLE domain_group_membership (
  membership_id            uuid PRIMARY KEY,
  domain_id                uuid NOT NULL REFERENCES domain(domain_id),
  group_id                 uuid NOT NULL REFERENCES sales_group(group_id),
  reporting_role           reporting_role NOT NULL,
  pipeline_allocation_pct  numeric(5,4) NOT NULL CHECK (pipeline_allocation_pct BETWEEN 0 AND 1),
  target_allocation_pct    numeric(5,4) NOT NULL CHECK (target_allocation_pct BETWEEN 0 AND 1),
  aggregation_policy       agg_policy NOT NULL,
  valid_from               date NOT NULL,
  valid_to                 date,
  UNIQUE (domain_id, group_id, valid_from)
);

-- §14.1 accounts and domain classification
CREATE TABLE account (
  account_id         uuid PRIMARY KEY,
  source_system      text NOT NULL,
  source_id          text NOT NULL,
  legal_name         text NOT NULL,
  parent_account_id  uuid REFERENCES account(account_id),
  industry           text,
  geography           text,                            -- ISO country/region
  owner_id           uuid REFERENCES salesperson(salesperson_id),
  aliases            text[] NOT NULL DEFAULT '{}',
  valid_from         timestamptz NOT NULL,
  valid_to           timestamptz,
  UNIQUE (source_system, source_id)
);

CREATE TABLE account_domain (
  account_id         uuid NOT NULL REFERENCES account(account_id),
  domain_id          uuid NOT NULL REFERENCES domain(domain_id),
  is_primary         boolean NOT NULL DEFAULT false,   -- exactly one primary per account (§6.1)
  allocation_pct     numeric(5,4) NOT NULL DEFAULT 1 CHECK (allocation_pct BETWEEN 0 AND 1),
  valid_from         date NOT NULL,
  valid_to           date,
  PRIMARY KEY (account_id, domain_id, valid_from)
);

-- §14.1 opportunities (§8.2 analytics grain)
CREATE TABLE opportunity (
  opportunity_id     uuid PRIMARY KEY,
  source_system      text NOT NULL,
  source_id          text NOT NULL,
  account_id         uuid NOT NULL REFERENCES account(account_id),
  owner_id           uuid NOT NULL REFERENCES salesperson(salesperson_id),
  team_id            uuid REFERENCES team(team_id),
  name               text NOT NULL,
  amount_minor       bigint NOT NULL,
  currency           char(3) NOT NULL REFERENCES currency(code),
  stage              text NOT NULL,                   -- mapped via stage_map (§8.3)
  probability        numeric(5,4) CHECK (probability BETWEEN 0 AND 1),
  close_date         date NOT NULL,
  forecast_category  forecast_cat NOT NULL,
  created_at         timestamptz NOT NULL,
  updated_at         timestamptz NOT NULL,
  closed_at          timestamptz,
  is_deleted         boolean NOT NULL DEFAULT false,   -- deletion propagates to retrieval (§23.2)
  UNIQUE (source_system, source_id)
);

CREATE TABLE opportunity_team (
  opportunity_id     uuid NOT NULL REFERENCES opportunity(opportunity_id),
  salesperson_id     uuid NOT NULL REFERENCES salesperson(salesperson_id),
  role               text NOT NULL,
  credit_allocation_pct numeric(5,4) NOT NULL DEFAULT 1 CHECK (credit_allocation_pct BETWEEN 0 AND 1),
  valid_from         timestamptz NOT NULL,
  valid_to           timestamptz,
  PRIMARY KEY (opportunity_id, salesperson_id, valid_from)
);

CREATE TABLE activity (
  activity_id        uuid PRIMARY KEY,
  source_system      text NOT NULL,
  source_id          text NOT NULL,
  related_kind       text NOT NULL CHECK (related_kind IN ('opportunity','account','contact')),
  related_id         uuid NOT NULL,
  actor_id           uuid REFERENCES salesperson(salesperson_id),
  activity_type      text NOT NULL,                   -- call/meeting/email/task (metadata only — DPIA §2)
  occurred_at        timestamptz NOT NULL,
  outcome            text,
  sensitivity        text NOT NULL DEFAULT 'internal',
  UNIQUE (source_system, source_id)
);

-- §8.3 plans and forecasts
CREATE TABLE target_plan (
  plan_id            uuid PRIMARY KEY,
  assignee_kind      plan_assignee NOT NULL,
  assignee_id        uuid NOT NULL,                   -- polymorphic; integrity enforced by service layer
  metric_id          text NOT NULL REFERENCES metric_definition(metric_id),
  period_id          uuid NOT NULL REFERENCES fiscal_period(period_id),
  target_minor       bigint NOT NULL,
  currency           char(3) NOT NULL REFERENCES currency(code),
  version            int NOT NULL,
  approval_status    text NOT NULL DEFAULT 'draft',   -- draft/approved/superseded
  valid_from         timestamptz NOT NULL,
  UNIQUE (assignee_kind, assignee_id, metric_id, period_id, version)
);

CREATE TABLE forecast_snapshot (
  snapshot_id        uuid PRIMARY KEY,
  scope_kind         text NOT NULL CHECK (scope_kind IN ('salesperson','team','domain','group')),
  scope_id           uuid NOT NULL,
  period_id          uuid NOT NULL REFERENCES fiscal_period(period_id),
  category           forecast_cat NOT NULL,
  amount_minor       bigint NOT NULL,
  currency           char(3) NOT NULL REFERENCES currency(code),
  submitted_by       uuid REFERENCES app_user(user_id),
  submitted_at       timestamptz NOT NULL
);

-- FX reference (resolves review F-08): rate of 1 unit currency_from → currency_to
CREATE TABLE fx_rate (
  currency_from      char(3) NOT NULL REFERENCES currency(code),
  currency_to        char(3) NOT NULL REFERENCES currency(code),
  rate_date          date NOT NULL,
  rate               numeric(18,8) NOT NULL CHECK (rate > 0),
  source             text NOT NULL,                   -- approved provider (metric-catalog currency_treatment)
  PRIMARY KEY (currency_from, currency_to, rate_date)
);

-- §8.4 market intelligence
CREATE TABLE news_item (
  news_id            uuid PRIMARY KEY,
  cluster_id         uuid NOT NULL,                   -- deduplication cluster; canonical member flagged
  is_canonical       boolean NOT NULL DEFAULT false,
  source_name        text NOT NULL,
  url                text NOT NULL,
  title              text NOT NULL,
  published_at       timestamptz NOT NULL,
  retrieved_at       timestamptz NOT NULL,
  summary            text NOT NULL,                   -- factual summary (§8.4)
  rights_status      text NOT NULL,                   -- license/AI-summarization rights (connector plan C6)
  expires_at         timestamptz,                     -- retention per license
  entity_keys        text[] NOT NULL DEFAULT '{}'     -- resolved canonical entity ids
);

CREATE TABLE signal (
  signal_id          uuid PRIMARY KEY,
  signal_type        signal_type NOT NULL,
  entity_kind        text NOT NULL,                   -- account/competitor/domain/...
  entity_id          uuid NOT NULL,
  news_id            uuid REFERENCES news_item(news_id),
  relevance          numeric(5,4) NOT NULL CHECK (relevance BETWEEN 0 AND 1),
  confidence         numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  expires_at         timestamptz NOT NULL
);

-- §8.5/§10.3 dashboards and alerts (definitions; rendering contract in packages/validation)
CREATE TABLE dashboard (
  dashboard_id       uuid PRIMARY KEY,
  owner_id           uuid NOT NULL REFERENCES app_user(user_id),
  title              text NOT NULL,
  scope_kind         text NOT NULL CHECK (scope_kind IN ('seller','team','domain','group')),
  scope_id           uuid NOT NULL,
  definition         jsonb NOT NULL,                  -- validated by server-side schema before save (ADR-026)
  version            int NOT NULL,
  sharing_policy     text NOT NULL DEFAULT 'private',
  updated_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (dashboard_id, version)
);

CREATE TABLE alert_rule (
  rule_id            uuid PRIMARY KEY,
  owner_id           uuid NOT NULL REFERENCES app_user(user_id),
  metric_id          text REFERENCES metric_definition(metric_id),
  signal_type        signal_type,
  predicate          jsonb NOT NULL,                  -- threshold/pct-change/aging… (§8.6)
  schedule           jsonb NOT NULL,                  -- incl. quiet hours, digest, frequency cap
  channel            text NOT NULL CHECK (channel IN ('in_app','push','email')),  -- Teams: Phase 2 (ADR-034)
  status             text NOT NULL DEFAULT 'active'
);

-- §11.4 audit (append-only; tamper-evidence via hash chain)
CREATE TABLE agent_trace (
  trace_id           uuid PRIMARY KEY,
  user_id            uuid NOT NULL REFERENCES app_user(user_id),
  intent             text NOT NULL,
  scope_snapshot     jsonb NOT NULL,                  -- effective scope, redacted (§11.4)
  tools_called       jsonb NOT NULL DEFAULT '[]',
  policy_decisions   jsonb NOT NULL DEFAULT '[]',
  model_profile      text NOT NULL,
  prompt_version     text,
  evidence_refs      jsonb NOT NULL DEFAULT '[]',
  outcome            text NOT NULL,
  started_at         timestamptz NOT NULL,
  prev_hash          bytea,                           -- hash chain → tamper-evident
  row_hash           bytea NOT NULL
);

-- Integrity invariants the golden suite enforces (§23.2) — documented here, enforced by tests:
--   * one primary team per salesperson per day; one domain per team per day
--   * exactly one is_primary account_domain row per account per day
--   * Σ pipeline_allocation_pct per domain across full-view groups is checked by roll-up tests,
--     not constrained here (policies differ per §6.2)
