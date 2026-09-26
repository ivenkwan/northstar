from datetime import UTC, datetime, time

from alerts.engine import (
    AlertEvent,
    Channel,
    DeliveryPolicy,
    Severity,
    decide,
    in_quiet_hours,
    render_push,
    render_teams,
)


def event(**kw) -> AlertEvent:
    defaults = dict(rule_id="r1", user_id="u1", alert_type="target_gap",
                    correlation_id="c-1", deep_link="northstar://alert/c-1")
    defaults.update(kw)
    return AlertEvent(**defaults)


# ------------------------------------------------------------------ quiet hours (§8.6)


def test_quiet_hours_blocks_push_and_defers_to_digest():
    policy = DeliveryPolicy(quiet_hours=(time(22, 0), time(7, 0)), digest=True)
    now = datetime(2026, 9, 26, 16, 0, tzinfo=UTC)  # 00:00 HK — inside quiet hours
    d = decide(event(), Channel.PUSH, policy, sent_today=0, now_utc=now)
    assert not d.send_now and d.reason == "quiet_hours"
    assert d.digest_key == "digest:u1"


def test_critical_bypasses_quiet_hours():
    policy = DeliveryPolicy(quiet_hours=(time(22, 0), time(7, 0)))
    now = datetime(2026, 9, 26, 16, 0, tzinfo=UTC)
    d = decide(event(severity=Severity.CRITICAL), Channel.PUSH, policy, sent_today=0, now_utc=now)
    assert d.send_now


def test_email_not_subject_to_quiet_hours():
    policy = DeliveryPolicy(quiet_hours=(time(22, 0), time(7, 0)))
    now = datetime(2026, 9, 26, 16, 0, tzinfo=UTC)
    d = decide(event(), Channel.EMAIL, policy, sent_today=0, now_utc=now)
    assert d.send_now  # email is digest-only channel; no wake-the-phone semantics


def test_quiet_hours_window_crossing_midnight():
    assert in_quiet_hours(time(23, 30), (time(22, 0), time(7, 0)))
    assert in_quiet_hours(time(6, 59), (time(22, 0), time(7, 0)))
    assert not in_quiet_hours(time(12, 0), (time(22, 0), time(7, 0)))


# ------------------------------------------------------------------ frequency caps


def test_frequency_cap_defers_non_critical():
    policy = DeliveryPolicy(max_per_day=10)
    now = datetime(2026, 9, 26, 3, 0, tzinfo=UTC)  # 11:00 HK
    d = decide(event(), Channel.PUSH, policy, sent_today=10, now_utc=now)
    assert not d.send_now and d.reason == "frequency_cap"
    d2 = decide(event(severity=Severity.CRITICAL), Channel.PUSH, policy, sent_today=10, now_utc=now)
    assert d2.send_now  # critical always delivered (§8.6 escalation)


# ------------------------------------------------------------------ Teams channel (Phase 2, F-06)


def test_teams_card_metadata_only_with_deep_link():
    card = render_teams(event(), {"target_gap": "Target gap widened"})
    body = str(card)
    assert "northstar://alert/c-1" in body          # deep link present
    assert "HK$" not in body and "amount" not in body  # no amounts/content (ADR-034)
    assert card["attachments"][0]["content"]["version"] == "1.5"


def test_teams_card_localized():
    card = render_teams(event(), {"target_gap": "Target gap widened"},
                        {"target_gap": "目標差距擴大"}, language="zh-Hant")
    assert "目標差距擴大" in str(card)


def test_push_payload_is_metadata_only():
    payload = render_push(event())
    data = payload["message"]["data"]
    assert set(data) == {"alertType", "severity", "correlationId", "deepLink"}
    assert payload["message"]["notification"]["body"] == "New target_gap alert"  # generic text only
