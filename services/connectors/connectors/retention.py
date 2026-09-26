"""Retention and deletion execution (Phase 2; review F-12; DPIA §6 schedule).

Policies per data class from the DPIA retention table. Deletion propagates
source → raw landing expiry → canonical soft-delete → retrieval exclusion
(golden GPM-09 verifies the retrieval side).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field


class DataClass(str, Enum):
    RAW_LANDING = "raw_landing"          # 30 days (DPIA §6)
    CONVERSATION_LOGS = "conversation_logs"  # 24 months then aggregate
    AGENT_TRACES = "agent_traces"        # 24 months
    NEWS_ITEMS = "news_items"            # per license + signal expiry
    DEVICE_TELEMETRY = "device_telemetry"  # 12 months aggregated


RETENTION_DAYS: dict[DataClass, int | None] = {
    DataClass.RAW_LANDING: 30,
    DataClass.CONVERSATION_LOGS: 24 * 30,
    DataClass.AGENT_TRACES: 24 * 30,   # months approximated for sweep math; policy text governs
    DataClass.NEWS_ITEMS: None,        # license-dependent; expires_at on the row decides
    DataClass.DEVICE_TELEMETRY: 365,
}


class RetentionRecord(BaseModel):
    record_id: str
    data_class: DataClass
    created_at: datetime
    expires_at: datetime | None = None  # explicit expiry (news) overrides class default
    is_deleted: bool = False


class SweepResult(BaseModel):
    expired_ids: list[str] = Field(default_factory=list)
    soft_deleted_ids: list[str] = Field(default_factory=list)


def due_for_expiry(records: list[RetentionRecord], now: datetime) -> list[str]:
    out: list[str] = []
    for r in records:
        if r.is_deleted:
            continue
        default_days = RETENTION_DAYS.get(r.data_class)
        horizon = r.expires_at
        if horizon is None and default_days is not None:
            horizon = r.created_at + timedelta(days=default_days)
        if horizon is not None and horizon <= now:
            out.append(r.record_id)
    return out


def propagate_source_deletion(source_id: str, landing: dict[str, dict], canonical: dict[str, dict]) -> SweepResult:
    """Deletion propagation chain (§23.2 golden: deleted content disappears end-to-end)."""
    result = SweepResult()
    for key in list(landing):
        if landing[key].get("source_id") == source_id:
            landing[key]["expired"] = True
            result.expired_ids.append(key)
    for key in list(canonical):
        if canonical[key].get("source_id") == source_id:
            canonical[key]["is_deleted"] = True  # soft-delete; retrieval excludes (GPM-09)
            result.soft_deleted_ids.append(key)
    return result


def aggregate_after_expiry(conversations: list[dict], now: datetime) -> tuple[list[dict], int]:
    """Conversation logs older than retention collapse to aggregate counters, content dropped."""
    kept: list[dict] = []
    aggregated = 0
    for c in conversations:
        created = datetime.fromisoformat(c["created_at"])
        if now - created > timedelta(days=RETENTION_DAYS[DataClass.CONVERSATION_LOGS]):
            aggregated += 1  # only counts survive
        else:
            kept.append(c)
    return kept, aggregated
