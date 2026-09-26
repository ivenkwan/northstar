"""Microsoft Dynamics 365 connector (Phase 2, C7; ADR-031).

Dynamics semantics differ from Salesforce: change tracking returns a
@odata.deltaLink watermark rather than replay ids, amounts arrive as JSON
numbers, and state codes need their own mapping. Transform rules match
transforms.py: unmapped values quarantine, never silently default.
"""

from __future__ import annotations

from pydantic import BaseModel

from .transforms import CanonicalOpportunity, QuarantineEntry, TransformResult

# Dynamics opportunity statecode/statuscode → canonical stage
DYNAMICS_STAGE_MAP = {
    (0, 1): "early",     # Open / In Progress
    (0, 2): "middle",    # Open / On Hold → treated as middle until mapped otherwise
    (1, 2): "late",      # Won (status 2..4 map to late/closed_won by policy)
    (2, 5): "closed_lost",
}
DYNAMICS_STAGE_EXACT = {
    (1, 3): "closed_won",
    (1, 4): "closed_won",
    (1, 2): "late",
}


class DynamicsDelta(BaseModel):
    """One row from a Dynamics 365 change-tracking delta query."""

    opportunityid: str
    name: str
    statecode: int
    statuscode: int
    estimatedvalue: float | None = None
    transactioncurrencyid: dict | None = None  # {isoCurrencyCode: "HKD"}
    ownerid: dict | None = None  # {@odata.id, ...}
    customerid: dict | None = None
    exchangerate: float | None = None
    closingsdate: str | None = None  # estimatedclosedate in real payloads; tolerated alias below
    estimatedclosedate: str | None = None
    _delta_removed: bool | None = None  # deleted marker "@removed" in raw feed

    model_config = {"populate_by_name": True}


def transform_dynamics_opportunity(row: dict, out: TransformResult | None = None) -> TransformResult:
    out = out or TransformResult(records=[], quarantined=[])

    def quarantine(field: str, raw: object) -> None:
        out.quarantined.append(QuarantineEntry(source_id=str(row.get("opportunityid", "?")),
                                               field=field, raw_value=str(raw), reason="unmapped_value"))

    removed = row.get("@removed")
    if removed is not None:
        # Deletion events propagate as soft-deletes; retention/GPM-09 handles exclusion.
        out.quarantined.append(QuarantineEntry(source_id=str(row.get("opportunityid", "?")),
                                               field="@removed", raw_value=str(removed), reason="source_deleted"))
        return out

    state, status = row.get("statecode"), row.get("statuscode")
    stage = DYNAMICS_STAGE_EXACT.get((state, status)) or DYNAMICS_STAGE_MAP.get((state, status))
    if stage is None:
        quarantine("statecode/statuscode", f"{state}/{status}")
        return out

    amount = row.get("estimatedvalue")
    if amount is None:
        quarantine("estimatedvalue", amount)
        return out

    currency = ((row.get("transactioncurrencyid") or {}).get("isoCurrencyCode", "HKD"))
    record = CanonicalOpportunity(
        source_system="dynamics365",
        source_id=str(row["opportunityid"]),
        account_id=str((row.get("customerid") or {}).get("id", "unknown_account")),
        owner_id=str((row.get("ownerid") or {}).get("id", "unknown_owner")),
        name=str(row.get("name", row["opportunityid"])),
        amount_minor=round(float(amount) * 100),
        currency=str(currency),
        stage=stage,
        probability=None,  # Dynamics has no direct probability field; probability source policy applies
        close_date=str(row.get("estimatedclosedate") or row.get("closingsdate") or ""),
        forecast_category="pipeline",
    )
    out.records.append(record)
    return out


def apply_delta_link(cursors: dict[str, str], response: dict) -> str | None:
    """Extracts the next @odata.deltaLink watermark; None means full re-sync required."""
    link = response.get("@odata.deltaLink")
    if isinstance(link, str):
        cursors["dynamics365"] = link
        return link
    return None
