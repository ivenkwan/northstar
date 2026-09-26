"""Territory and whitespace analytics (Phase 3, §24.4).

Deterministic analytics over canonical entities:
- territory coverage: open pipeline vs territory plan, under-served flags
- whitespace: industries/domains with incumbent spend but no active pursuit,
  and accounts with closed-won history but no open pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel


class Account(BaseModel):
    account_id: str
    industry: str
    domain_id: str
    has_closed_won_history: bool = False


class TerritoryRow(BaseModel):
    territory_key: str  # domain_id or industry
    open_pipeline_minor: int = 0
    target_minor: int = 0
    account_count: int = 0
    accounts_with_open_pipeline: int = 0


class TerritoryCoverage(BaseModel):
    territory_key: str
    coverage: float | None       # open pipeline / remaining target
    unpenetrated_accounts: int   # accounts in territory with zero open pipeline
    under_served: bool


class Whitespace(BaseModel):
    kind: str                    # dormant_account | unpenetrated_industry
    key: str                     # account_id or industry
    detail: str
    evidence: str                # what makes this whitespace — always grounded


def coverage_by_territory(rows: list[TerritoryRow], under_served_floor: float = 2.0) -> list[TerritoryCoverage]:
    out: list[TerritoryCoverage] = []
    for r in rows:
        remaining = max(r.target_minor, 0)
        cov = (r.open_pipeline_minor / remaining) if remaining > 0 else None
        unpenetrated = r.account_count - r.accounts_with_open_pipeline
        under = (cov is not None and cov < under_served_floor) or unpenetrated > max(1, r.account_count // 3)
        out.append(TerritoryCoverage(territory_key=r.territory_key, coverage=cov,
                                     unpenetrated_accounts=unpenetrated, under_served=under))
    return out


def detect_whitespace(accounts: list[Account],
                      open_pipeline_by_account: dict[str, int],
                      industry_incumbent_threshold: int = 3) -> list[Whitespace]:
    out: list[Whitespace] = []
    for a in accounts:
        if a.has_closed_won_history and open_pipeline_by_account.get(a.account_id, 0) == 0:
            out.append(Whitespace(kind="dormant_account", key=a.account_id,
                                  detail="closed-won history but no open pipeline",
                                  evidence="crm: closed_won in history; open pipeline = 0"))
    industries: dict[str, list[Account]] = {}
    for a in accounts:
        industries.setdefault(a.industry, []).append(a)
    for industry, accts in industries.items():
        with_pipeline = sum(1 for a in accts if open_pipeline_by_account.get(a.account_id, 0) > 0)
        if len(accts) >= industry_incumbent_threshold and with_pipeline == 0:
            out.append(Whitespace(kind="unpenetrated_industry", key=industry,
                                  detail=f"{len(accts)} known accounts, none pursued",
                                  evidence="crm: accounts exist; open pipeline = 0"))
    return out
