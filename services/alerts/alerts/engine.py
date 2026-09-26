"""Alert dispatch engine (PRD §8.6; ADR-034).

Channels: in_app, push, email (MVP) and teams (Phase 2 — this module).
Delivery rules: quiet hours, per-user frequency caps, digest bundling,
snooze and acknowledgement. Push payloads are metadata-only (ADR-034);
content is fetched from the API after authentication.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from enum import Enum

from pydantic import BaseModel, Field


class Channel(str, Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    TEAMS = "teams"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertEvent(BaseModel):
    rule_id: str
    user_id: str
    severity: Severity = Severity.INFO
    alert_type: str  # threshold | pct_change | stage_aging | target_gap | market_signal ...
    correlation_id: str
    # Metadata-only payload rule (ADR-034): never amounts, customer names, or record data
    # in push/Teams surfaces; deep link re-authorizes at open time (§10.2).
    deep_link: str


class DeliveryPolicy(BaseModel):
    quiet_hours: tuple[time, time] | None = None  # local user time, e.g. (22:00, 07:00)
    quiet_hours_tz_offset_minutes: int = 480  # HK default
    max_per_day: int = Field(default=10, ge=1)
    digest: bool = False
    critical_bypasses_quiet_hours: bool = True


class DispatchDecision(BaseModel):
    channel: Channel
    send_now: bool
    reason: str  # audit-explainable decision (§8.6 telemetry)
    digest_key: str | None = None


def _local_time(now_utc: datetime, tz_offset_minutes: int) -> time:
    return (now_utc + timedelta(minutes=tz_offset_minutes)).time()


def in_quiet_hours(now_local: time, quiet: tuple[time, time]) -> bool:
    start, end = quiet
    if start <= end:
        return start <= now_local < end
    return now_local >= start or now_local < end  # window crosses midnight


def decide(event: AlertEvent, channel: Channel, policy: DeliveryPolicy,
           sent_today: int, now_utc: datetime) -> DispatchDecision:
    if channel is Channel.PUSH or channel is Channel.TEAMS:
        if policy.quiet_hours is not None:
            local = _local_time(now_utc, policy.quiet_hours_tz_offset_minutes)
            if in_quiet_hours(local, policy.quiet_hours):
                bypass = policy.critical_bypasses_quiet_hours and event.severity is Severity.CRITICAL
                if not bypass:
                    return DispatchDecision(
                        channel=channel, send_now=False, reason="quiet_hours",
                        digest_key=f"digest:{event.user_id}" if policy.digest else None,
                    )
    if sent_today >= policy.max_per_day and event.severity is not Severity.CRITICAL:
        return DispatchDecision(channel=channel, send_now=False,
                                reason="frequency_cap",
                                digest_key=f"digest:{event.user_id}" if policy.digest else None)
    return DispatchDecision(channel=channel, send_now=True, reason="ok")


class TeamsMessage(BaseModel):
    """Teams adaptive card body. Metadata + deep link only; no record content (ADR-034 note)."""

    rule_id: str
    title: str
    severity: Severity
    deep_link: str
    correlation_id: str


def render_teams(event: AlertEvent, catalog_en: dict[str, str], catalog_zh: dict[str, str] | None = None,
                 language: str = "en") -> dict:
    """Adaptive-card-shaped payload for the enterprise Teams app (Graph API consent: Phase 2 ops)."""
    base_title = catalog_en.get(event.alert_type, event.alert_type)
    title = base_title if language == "en" else (catalog_zh or {}).get(event.alert_type, base_title)
    card = TeamsMessage(rule_id=event.rule_id, title=title, severity=event.severity,
                        deep_link=event.deep_link, correlation_id=event.correlation_id)
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard", "version": "1.5",
                "body": [
                    {"type": "TextBlock", "text": card.title, "weight": "Bolder"},
                    {"type": "TextBlock", "text": f"severity: {card.severity.value}", "isSubtle": True},
                    {"type": "ActionSet", "actions": [
                        {"type": "Action.OpenUrl", "title": "Open", "url": card.deep_link}
                    ]},
                ],
            },
        }],
    }


def render_push(event: AlertEvent) -> dict:
    """FCM/APNs payload: metadata only. Body text is generic; details fetched post-auth (ADR-034)."""
    return {
        "message": {
            "token": "<device-token>",
            "notification": {"title": "sales-northstar", "body": f"New {event.alert_type} alert"},
            "data": {
                "alertType": event.alert_type,
                "severity": event.severity.value,
                "correlationId": event.correlation_id,
                "deepLink": event.deep_link,
            },
        }
    }
