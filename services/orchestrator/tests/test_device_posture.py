from datetime import UTC, datetime, timedelta

from orchestrator.device_posture import (
    DevicePosture,
    MdmAdapter,
    PostureRequirement,
    StaticMdm,
    authorize_scope,
    posture_ok,
)

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
REQ = PostureRequirement()


def healthy(device_id="d1", **kw) -> DevicePosture:
    defaults = dict(device_id=device_id, is_managed=True, is_compliant=True,
                    attested_at=NOW - timedelta(minutes=10))
    defaults.update(kw)
    return DevicePosture(**defaults)


def test_healthy_posture_passes():
    ok, reason = posture_ok(healthy(), REQ, now=NOW)
    assert ok and reason == "ok"


def test_unmanaged_or_noncompliant_rejected():
    assert posture_ok(healthy(is_managed=False), REQ, now=NOW) == (False, "device_not_managed")
    assert posture_ok(healthy(is_compliant=False), REQ, now=NOW) == (False, "device_not_compliant")
    assert posture_ok(healthy(jailbreak_detected=True), REQ, now=NOW) == (False, "jailbreak_detected")


def test_stale_attestation_rejected():
    stale = healthy(attested_at=NOW - timedelta(days=3))
    assert posture_ok(stale, PostureRequirement(max_attestation_age_minutes=60 * 24), now=NOW) \
        == (False, "attestation_stale")
    assert posture_ok(healthy(attested_at=None), REQ, now=NOW) == (False, "attestation_missing")


def test_sensitive_scopes_gate_read_only_do_not():
    unmanaged = healthy(is_managed=False)
    ok, _ = authorize_scope(unmanaged, "pipeline_read", REQ, now=NOW)
    assert ok  # read-only analytics unaffected (§10.2 progressive posture)
    blocked, reason = authorize_scope(unmanaged, "offline_cache", REQ, now=NOW)
    assert not blocked and reason == "device_not_managed"
    allowed, _ = authorize_scope(healthy(), "action_confirm", REQ, now=NOW)
    assert allowed  # healthy device passes the sensitive gate


def test_static_mdm_unknown_device_is_unmanaged():
    mdm: MdmAdapter = StaticMdm({"known": healthy("known")})
    assert mdm.fetch_posture("known").is_managed
    assert not mdm.fetch_posture("unknown").is_managed  # fail-closed default
