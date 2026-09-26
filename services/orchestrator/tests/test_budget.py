from orchestrator.budget import (
    BudgetLedger,
    TokenUsage,
    anomaly_detected,
    as_of_bucket,
    semantic_cache_key,
)


def ledger() -> tuple[BudgetLedger, str]:
    led = BudgetLedger()
    led.ensure("tenant_a", "2026-09", token_limit=10_000, request_limit=5)
    return led, "2026-09"


def test_budget_blocks_at_token_limit():
    led, period = ledger()
    assert led.check("tenant_a", period).allowed
    led.record("tenant_a", period, input_tokens=6_000, output_tokens=4_100)  # 10_100 > 10_000
    d = led.check("tenant_a", period)
    assert not d.allowed and d.reason == "token_budget_exhausted"  # denial-of-wallet guard (T-12)


def test_budget_blocks_at_request_limit():
    led, period = ledger()
    for _ in range(5):
        led.record("tenant_a", period, input_tokens=10, output_tokens=10)
    d = led.record("tenant_a", period, input_tokens=10, output_tokens=10)
    assert not d.allowed and d.reason == "request_budget_exhausted"


def test_tenants_are_isolated():
    led, period = ledger()
    led.record("tenant_a", period, 10_000, 0)
    other = led.check("tenant_b", period)
    assert other.allowed and other.reason == "no_budget_configured"


def test_anomaly_detection_triggers_above_factor():
    assert anomaly_detected(window_avg_tokens=5_000, baseline_avg_tokens=800) is True
    assert anomaly_detected(window_avg_tokens=900, baseline_avg_tokens=800) is False
    assert anomaly_detected(window_avg_tokens=100, baseline_avg_tokens=0) is False


def test_semantic_cache_key_deterministic_and_scoped():
    a = semantic_cache_key("team", "t1", ["coverage", "attainment_pct"], "FY27-Q1", "1761178000")
    b = semantic_cache_key("team", "t1", ["attainment_pct", "coverage"], "FY27-Q1", "1761178000")
    assert a == b  # metric order irrelevant
    c = semantic_cache_key("team", "t2", ["coverage", "attainment_pct"], "FY27-Q1", "1761178000")
    assert a != c  # scope change invalidates


def test_conversational_context_never_cached():
    assert semantic_cache_key("conversation", "thread_1", ["coverage"], "FY27-Q1", "x") is None
    assert semantic_cache_key("seller", "s1", [], "FY27-Q1", "x") is None  # no metrics → no key


def test_as_of_bucket_floors_to_15m():
    assert as_of_bucket(1761177600) == "1761177600"      # 900×1956864 — on the boundary stays
    assert as_of_bucket(1761178000) == "1761177600"      # 400s into the bucket floors back
    assert as_of_bucket(1761178900) == "1761178500"      # past 900s → next bucket
    assert as_of_bucket(1761178499) == "1761177600"      # last second of the first bucket


def test_usage_record_is_content_free():
    u = TokenUsage(tenant_id="t", route="anthropic-messages", model_profile="reasoning.standard",
                   input_tokens=100, output_tokens=20, latency_ms=350)
    dumped = u.model_dump()
    assert "prompt" not in str(dumped) and "content" not in str(dumped)  # metadata only (§21)
