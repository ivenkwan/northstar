from connectors.landing import Cursor, LandedEvent, RawLanding, advance_cursor, reconcile
from connectors.transforms import transform_batch, usd_to_minor


def sf_payload(oid="OPP-1", stage="Proposal", amount=12500.0, **extra):
    return {"Id": oid, "StageName": stage, "Amount": amount, "ForecastCategoryName": "Commit",
            "Name": "ACME renewal", "Probability": 75, "CloseDate": "2026-12-15", **extra}


def test_transform_maps_enums_and_minor_units():
    r = transform_batch([sf_payload()])
    assert len(r.records) == 1 and not r.quarantined
    rec = r.records[0]
    assert rec.stage == "middle" and rec.forecast_category == "commit"
    assert rec.amount_minor == 1_250_000  # minor units
    assert rec.probability == 0.75


def test_unmapped_stage_is_quarantined_never_defaulted():
    r = transform_batch([sf_payload(stage="Weird New Stage")])
    assert not r.records
    assert r.quarantined[0].field == "StageName"
    assert r.quarantined[0].reason == "unmapped_value"


def test_missing_amount_quarantined():
    r = transform_batch([sf_payload(amount=None)])
    assert not r.records and r.quarantined[0].field == "Amount"


def test_minor_unit_conversion():
    assert usd_to_minor(99.999) == 10000
    assert usd_to_minor(None) is None


def test_landing_is_idempotent_on_event_ids():
    zone = RawLanding()
    events = [LandedEvent(event_id="e1", source="salesforce", payload={"replayId": "100"}),
              LandedEvent(event_id="e2", source="salesforce", payload={"replayId": "101"})]
    assert zone.land(events) == (2, 0)
    assert zone.land(events) == (0, 2)  # replay is a no-op (§replay determinism)


def test_cursor_advances_only_over_landed():
    c = Cursor(source="salesforce", offset="100", updated_at="t")
    events = [LandedEvent(event_id="e1", source="s", payload={"replayId": "105"}),
              LandedEvent(event_id="e2", source="s", payload={"replayId": "103"})]
    assert advance_cursor(c, events).offset == "105"


def test_reconciliation_detects_breach():
    rows = [{"_day": "2026-09-26", "amount_minor": 100} for _ in range(10)]
    ok = reconcile("2026-09-26", source_count=10, source_amount_minor=1000, landed=rows)
    assert ok.within_tolerance
    breach = reconcile("2026-09-26", source_count=10, source_amount_minor=2000, landed=rows)
    assert not breach.within_tolerance  # blocks the release gate (§23.1)
