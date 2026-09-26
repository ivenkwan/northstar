import pytest
from orchestrator.playbooks import load_catalog, select_plays


def test_catalog_loads_and_validates():
    cat = load_catalog()
    assert cat.catalog_version >= 1
    assert len(cat.plays) >= 4
    assert all(p["evidence_basis"] for p in cat.plays)  # no uncited plays


def test_renewal_risk_needs_two_signals():
    cat = load_catalog()
    one = select_plays(cat, ["inactivity"], "late")
    assert not any(p.play_id == "renewal_risk_early_warning" for p in one)
    two = select_plays(cat, ["inactivity", "close_date_push"], "late")
    assert any(p.play_id == "renewal_risk_early_warning" for p in two)
    play = next(p for p in two if p.play_id == "renewal_risk_early_warning")
    assert play.matched_signals == ["close_date_push", "inactivity"]
    assert play.methodology and play.recommendation and play.evidence_basis


def test_stage_gates_apply():
    cat = load_catalog()
    early = select_plays(cat, ["competitor_mention"], "early")
    assert not any(p.play_id == "competitor_displacement" for p in early)  # middle/late play


def test_ranking_by_signal_count_then_id():
    cat = load_catalog()
    plays = select_plays(cat, ["competitor_mention", "pricing_pressure", "missing_stakeholder"], "middle")
    ids = [p.play_id for p in plays]
    assert "competitor_displacement" in ids and "multi_thread_late_stage" in ids
    assert len(plays) <= 3


def test_recommends_never_executes():
    cat = load_catalog()
    for p in select_plays(cat, ["inactivity", "close_date_push"], "late"):
        assert p.recommendation  # advisory text with provenance — no action payloads (§8.7 posture)


def test_unknown_stage_in_catalog_rejected(tmp_path):
    bad = tmp_path / "catalog.yaml"
    bad.write_text("catalog_version: 1\nplays:\n- play_id: x\n  name: x\n  methodology: x\n  version: 1\n"
                   "  match: {signals: [a], stages: [bogus], min_signals: 1}\n"
                   "  recommendation: r\n  evidence_basis: e\n  owner: o\n")
    with pytest.raises(ValueError):
        load_catalog(bad)
