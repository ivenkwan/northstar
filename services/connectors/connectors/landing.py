"""Durable landing semantics: cursors, idempotent event landing, replay determinism, reconciliation.

ADR-031: each connector is a Temporal workflow with durable cursors, bounded
retries, and poison quarantine. The workflow mechanics live with Temporal at
deploy time; the pure logic below is what those workflows execute and test.
"""

from __future__ import annotations

from pydantic import BaseModel


class Cursor(BaseModel):
    source: str
    offset: str  # Salesforce replayId / Dynamics token / watermark timestamp
    updated_at: str


class LandedEvent(BaseModel):
    event_id: str  # source event id — the idempotency key
    source: str
    payload: dict


class RawLanding:
    """Append-only raw zone (schema.sql raw landing semantics) keyed by event id."""

    def __init__(self) -> None:
        self.events: dict[str, LandedEvent] = {}
        self.quarantine: list[tuple[LandedEvent, str]] = []

    def land(self, events: list[LandedEvent]) -> tuple[int, int]:
        """Returns (new, duplicates). Duplicate event ids are dropped — replay is a no-op."""
        new = dupes = 0
        for e in events:
            if e.event_id in self.events:
                dupes += 1
                continue
            self.events[e.event_id] = e
            new += 1
        return new, dupes


class ReconciliationReport(BaseModel):
    source: str
    day: str
    source_count: int
    landed_count: int
    source_amount_minor: int
    landed_amount_minor: int
    within_tolerance: bool


def reconcile(day: str, source_count: int, source_amount_minor: int,
              landed: list[dict], tolerance_pct: float = 0.001) -> ReconciliationReport:
    """§27 exit: certified totals reconcile to source. Breach blocks the release gate (§23.1)."""
    landed_count = sum(1 for r in landed if r.get("_day") == day)
    landed_amount = sum(r.get("amount_minor", 0) for r in landed if r.get("_day") == day)
    count_ok = source_count == 0 or abs(landed_count - source_count) / max(source_count, 1) <= tolerance_pct
    amount_ok = abs(landed_amount - source_amount_minor) / max(abs(source_amount_minor), 1) <= tolerance_pct
    return ReconciliationReport(source="crm", day=day, source_count=source_count,
                                landed_count=landed_count, source_amount_minor=source_amount_minor,
                                landed_amount_minor=landed_amount,
                                within_tolerance=count_ok and amount_ok)


def advance_cursor(cursor: Cursor, events: list[LandedEvent]) -> Cursor:
    """Cursors only advance over durably landed events (exactly-once landing, at-least-once source)."""
    max_off = cursor.offset
    for e in events:
        off = str(e.payload.get("replayId", e.event_id))
        if off.isdigit() and (not max_off.isdigit() or int(off) > int(max_off)):
            max_off = off
    return Cursor(source=cursor.source, offset=max_off, updated_at=cursor.updated_at)
