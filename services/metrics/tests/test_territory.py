from metrics.territory import (
    Account,
    TerritoryRow,
    coverage_by_territory,
    detect_whitespace,
)


def test_coverage_computed_with_none_guard():
    rows = [
        TerritoryRow(territory_key="dom_telco", open_pipeline_minor=1_000_000, target_minor=2_000_000,
                     account_count=10, accounts_with_open_pipeline=4),
        TerritoryRow(territory_key="dom_fintech", open_pipeline_minor=0, target_minor=0,
                     account_count=5, accounts_with_open_pipeline=5),
    ]
    out = {c.territory_key: c for c in coverage_by_territory(rows)}
    assert out["dom_telco"].coverage == 0.5
    assert out["dom_fintech"].coverage is None  # no target → undefined, not zero
    assert out["dom_telco"].under_served and out["dom_telco"].unpenetrated_accounts == 6


def test_under_served_by_unpenetrated_majority():
    rows = [TerritoryRow(territory_key="dom_health", open_pipeline_minor=10_000_000, target_minor=1_000_000,
                         account_count=9, accounts_with_open_pipeline=2)]
    out = coverage_by_territory(rows)[0]
    assert out.coverage == 10.0                       # coverage looks great, but…
    assert out.under_served and out.unpenetrated_accounts == 7  # …concentration risk flags it


def test_dormant_account_whitespace_only_with_history():
    accts = [
        Account(account_id="a1", industry="telco", domain_id="d1", has_closed_won_history=True),
        Account(account_id="a2", industry="telco", domain_id="d1", has_closed_won_history=False),
    ]
    ws = detect_whitespace(accts, {"a1": 0, "a2": 0})
    kinds = {w.key: w.kind for w in ws}
    assert kinds.get("a1") == "dormant_account"   # history + no pipeline
    assert "a2" not in kinds                      # no history → not whitespace by this rule


def test_unpenetrated_industry_requires_threshold():
    accts = [Account(account_id=f"a{i}", industry="fintech", domain_id="d1") for i in range(4)]
    ws = detect_whitespace(accts, {})
    assert any(w.kind == "unpenetrated_industry" and w.key == "fintech" for w in ws)
    few = detect_whitespace(accts[:2], {})  # below threshold
    assert not any(w.kind == "unpenetrated_industry" for w in few)


def test_every_whitespace_carries_evidence():
    accts = [Account(account_id="a1", industry="telco", domain_id="d1", has_closed_won_history=True)]
    for w in detect_whitespace(accts, {"a1": 0}):
        assert w.evidence  # grounded insight, never a bare assertion
