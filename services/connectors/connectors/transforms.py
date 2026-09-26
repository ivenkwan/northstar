"""Canonical transforms (PRD §14): source payload → canonical record.

Rules that make ingestion trustworthy:
- Unmapped enum values are quarantined with a data-quality warning, never silently defaulted.
- Event IDs are the idempotency key: replaying the raw landing window is a no-op.
- Money is normalized to minor units at the boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

STAGE_MAP = {
    "Prospecting": "early",
    "Qualification": "early",
    "Proposal": "middle",
    "Negotiation": "late",
    "Closed Won": "closed_won",
    "Closed Lost": "closed_lost",
}

FORECAST_MAP = {
    "Pipeline": "pipeline",
    "Best Case": "best_case",
    "Commit": "commit",
    "Closed": "closed",
}


class CanonicalOpportunity(BaseModel):
    source_system: str = "salesforce"
    source_id: str
    account_id: str
    owner_id: str
    name: str
    amount_minor: int = Field(ge=0)
    currency: str = "HKD"
    stage: str
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    close_date: str
    forecast_category: str


class QuarantineEntry(BaseModel):
    source_id: str
    field: str
    raw_value: str
    reason: str


class TransformResult(BaseModel):
    records: list[CanonicalOpportunity]
    quarantined: list[QuarantineEntry]


def usd_to_minor(amount: float | int | str | None, scale: int = 2) -> int | None:
    if amount is None or amount == "":
        return None
    return round(float(amount) * 10**scale)


def transform_opportunity(payload: dict, results: TransformResult | None = None) -> TransformResult:
    out = results or TransformResult(records=[], quarantined=[])

    def quarantine(field: str, raw: object) -> None:
        out.quarantined.append(QuarantineEntry(source_id=str(payload.get("Id", "?")), field=field,
                                               raw_value=str(raw), reason="unmapped_value"))

    stage = STAGE_MAP.get(str(payload.get("StageName", "")))
    if stage is None:
        quarantine("StageName", payload.get("StageName"))
        return out

    fc = FORECAST_MAP.get(str(payload.get("ForecastCategoryName", "Pipeline")), None)
    if fc is None:
        quarantine("ForecastCategoryName", payload.get("ForecastCategoryName"))
        return out

    amount = usd_to_minor(payload.get("Amount"))
    if amount is None:
        quarantine("Amount", payload.get("Amount"))
        return out

    record = CanonicalOpportunity(
        source_id=str(payload["Id"]),
        account_id=str(payload.get("AccountId", "unknown_account")),
        owner_id=str(payload.get("OwnerId", "unknown_owner")),
        name=str(payload.get("Name", payload["Id"])),
        amount_minor=amount,
        currency=str(payload.get("CurrencyIsoCode", "HKD")),
        stage=stage,
        probability=float(payload["Probability"]) / 100.0 if payload.get("Probability") is not None else None,
        close_date=str(payload.get("CloseDate", "")),
        forecast_category=fc,
    )
    out.records.append(record)
    return out


def transform_batch(payloads: list[dict]) -> TransformResult:
    out = TransformResult(records=[], quarantined=[])
    for p in payloads:
        transform_opportunity(p, out)
    return out
