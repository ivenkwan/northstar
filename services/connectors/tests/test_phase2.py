from datetime import datetime, timedelta

from connectors.dynamics import apply_delta_link, transform_dynamics_opportunity
from connectors.retention import (
    DataClass,
    RetentionRecord,
    aggregate_after_expiry,
    due_for_expiry,
    propagate_source_deletion,
)
from connectors.transforms import TransformResult


def dyn_row(state=0, status=1, amount=25000.0, **extra):
    return {
        "opportunityid": "guid-1", "name": "Contoso deal", "statecode": state, "statuscode": status,
        "estimatedvalue": amount,
        "transactioncurrencyid": {"isoCurrencyCode": "HKD"},
        "ownerid": {"id": "owner-9"}, "customerid": {"id": "acct-3"},
        "estimatedclosedate": "2026-11-30", **extra,
    }


# ------------------------------------------------------------------ Dynamics (C7)


def test_dynamics_open_opportunity_maps_to_canonical():
    r = transform_dynamics_opportunity(dyn_row(), TransformResult(records=[], quarantined=[]))
    assert len(r.records) == 1
    rec = r.records[0]
    assert rec.source_system == "dynamics365"
    assert rec.stage == "early"
    assert rec.amount_minor == 2_500_000
    assert rec.account_id == "acct-3" and rec.owner_id == "owner-9"


def test_dynamics_won_and_lost_states():
    won = transform_dynamics_opportunity(dyn_row(state=1, status=3), TransformResult(records=[], quarantined=[]))
    assert won.records[0].stage == "closed_won"
    lost = transform_dynamics_opportunity(dyn_row(state=2, status=5), TransformResult(records=[], quarantined=[]))
    assert lost.records[0].stage == "closed_lost"


def test_dynamics_unmapped_state_quarantined():
    r = transform_dynamics_opportunity(dyn_row(state=7, status=99), TransformResult(records=[], quarantined=[]))
    assert not r.records
    assert r.quarantined[0].field == "statecode/statuscode"


def test_dynamics_removal_marker_becomes_deletion_event():
    r = transform_dynamics_opportunity(dyn_row(**{"@removed": {"reason": "deleted"}}),
                                       TransformResult(records=[], quarantined=[]))
    assert not r.records
    assert r.quarantined[0].reason == "source_deleted"


def test_delta_link_advances_cursor():
    cursors: dict[str, str] = {}
    assert apply_delta_link(cursors, {"@odata.deltaLink": "https://…/delta?$deltatoken=abc"}) is not None
    assert "deltatoken=abc" in cursors["dynamics365"]
    assert apply_delta_link(cursors, {"value": []}) is None  # no new watermark


# ------------------------------------------------------------------ retention (F-12)


def test_raw_landing_expires_after_30_days():
    now = datetime(2026, 9, 26)
    old = RetentionRecord(record_id="e1", data_class=DataClass.RAW_LANDING, created_at=now - timedelta(days=31))
    fresh = RetentionRecord(record_id="e2", data_class=DataClass.RAW_LANDING, created_at=now - timedelta(days=3))
    assert due_for_expiry([old, fresh], now) == ["e1"]


def test_news_uses_explicit_expiry_not_class_default():
    now = datetime(2026, 9, 26)
    n1 = RetentionRecord(record_id="n1", data_class=DataClass.NEWS_ITEMS,
                         created_at=now - timedelta(days=365), expires_at=now + timedelta(days=5))
    assert due_for_expiry([n1], now) == []  # license expiry not reached → kept


def test_source_deletion_propagates_to_canonical_soft_delete():
    landing = {"l1": {"source_id": "guid-1"}, "l2": {"source_id": "other"}}
    canonical = {"c1": {"source_id": "guid-1", "is_deleted": False}}
    result = propagate_source_deletion("guid-1", landing, canonical)
    assert result.expired_ids == ["l1"]
    assert result.soft_deleted_ids == ["c1"]
    assert canonical["c1"]["is_deleted"] is True  # retrieval exclusion follows (GPM-09)
    assert landing["l2"].get("expired") is None


def test_old_conversations_aggregate_content_away():
    now = datetime(2026, 9, 26)
    convs = [
        {"id": "old", "created_at": (now - timedelta(days=730)).isoformat(), "text": "secret"},
        {"id": "new", "created_at": (now - timedelta(days=5)).isoformat(), "text": "recent"},
    ]
    kept, aggregated = aggregate_after_expiry(convs, now)
    assert aggregated == 1 and len(kept) == 1
    assert kept[0]["id"] == "new"
