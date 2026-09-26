"""Device posture policy (Phase 2 MDM integration, repo side).

ABAC (§11.1) includes device posture as an attribute: sensitive scopes
(require step-up surfaces, offline cache, push subscriptions) demand a managed,
compliant device with fresh attestation. The MDM vendor adapter is an
interface — the Intune/production adapter plugs in at deploy time
(**[DEPLOY]**: MDM environment, Intune Graph access).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field


class DevicePosture(BaseModel):
    device_id: str
    is_managed: bool = False
    is_compliant: bool = False
    os_version: str = ""
    attested_at: datetime | None = None
    jailbreak_detected: bool = False


class PostureRequirement(BaseModel):
    require_managed: bool = True
    require_compliant: bool = True
    max_attestation_age_minutes: int = Field(default=60 * 24, ge=1)


# Sensitive scope classes per §10.2/§11.1 that gate on posture
POSTURE_GATED_SCOPES = frozenset({"offline_cache", "push_subscription", "action_confirm"})


def posture_ok(posture: DevicePosture, req: PostureRequirement, now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now(UTC)
    if req.require_managed and not posture.is_managed:
        return False, "device_not_managed"
    if req.require_compliant and not posture.is_compliant:
        return False, "device_not_compliant"
    if posture.jailbreak_detected:
        return False, "jailbreak_detected"
    if posture.attested_at is None:
        return False, "attestation_missing"
    age = now - posture.attested_at
    if age > timedelta(minutes=req.max_attestation_age_minutes):
        return False, "attestation_stale"
    return True, "ok"


class MdmAdapter:
    """Interface to the enterprise MDM (Intune in the target deployment)."""

    def fetch_posture(self, device_id: str) -> DevicePosture:
        raise NotImplementedError


class StaticMdm(MdmAdapter):
    """Test/dev adapter: fixed postures per device, no network, no MDM."""

    def __init__(self, postures: dict[str, DevicePosture]) -> None:
        self._postures = postures

    def fetch_posture(self, device_id: str) -> DevicePosture:
        posture = self._postures.get(device_id)
        if posture is None:
            return DevicePosture(device_id=device_id)  # unknown device = unmanaged posture
        return posture


def authorize_scope(device: DevicePosture, scope: str, req: PostureRequirement,
                    now: datetime | None = None) -> tuple[bool, str]:
    """Posture gate applies only to sensitive scopes (§10.2); read-only analytics is unaffected."""
    if scope not in POSTURE_GATED_SCOPES:
        return True, "not_posture_gated"
    return posture_ok(device, req, now)
