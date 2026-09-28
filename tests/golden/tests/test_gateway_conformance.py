"""GW gateway conformance goldens (§23.3) — route config + wire contract + SSE semantics."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from golden.wire import (
    TERMINATOR_ANTHROPIC,
    TERMINATOR_OPENAI,
    AnthropicContentBlock,
    AnthropicMessage,
    OpenAIChatCompletion,
    parse_sse_events,
)
from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def routes() -> dict:
    return yaml.safe_load((REPO / "infra" / "apisix" / "routes.yaml").read_text())


def route(name: str) -> dict:
    return next(r for r in routes()["routes"] if r["name"] == name)


# ------------------------------------------------------------------ GW-01: OpenAI non-streaming contract


def test_gw01_openai_non_streaming_round_trip():
    payload = json.loads((FIXTURES / "openai_completion.json").read_text())
    completion = OpenAIChatCompletion.model_validate(payload)  # field-preserving contract
    assert completion.choices[0].message.role == "assistant"
    assert completion.usage.total_tokens >= completion.usage.completion_tokens


def test_gw01_openai_contract_rejects_wrong_shape():
    bad = {"id": "x", "object": "chat.completion", "choices": []}  # empty choices violate the contract
    try:
        OpenAIChatCompletion.model_validate(bad)
        raise AssertionError("should have failed")
    except ValidationError:
        pass


# ------------------------------------------------------------------ GW-02: header stripping + credential precedence (config-level)


def test_gw02_sensitive_headers_stripped_before_ai_proxy():
    openai = route("openai-chat-completions")["plugins"]
    anthropic = route("anthropic-messages")["plugins"]
    assert set(openai["proxy-rewrite"]["headers"]["remove"]) >= {"cookie", "x-api-key", "x-internal-token"}
    assert set(anthropic["proxy-rewrite"]["headers"]["remove"]) >= {"cookie", "authorization", "x-internal-token"}


def test_gw02_credentials_resolve_server_side_from_vault_only():
    for name, provider in (("openai-chat-completions", "openai"), ("anthropic-messages", "anthropic")):
        cfg = route(name)["plugins"]["ai-proxy"]
        auth = cfg["auth"]["header"]
        values = list(auth.values())
        assert all("$SECRET://vault/" in v for v in values), f"{provider}: BYOK must come from Vault"
        assert cfg.get("conversion", "disabled") == "disabled"  # ADR-024 default


def test_gw02_anthropic_route_ends_in_v1_messages():
    assert route("anthropic-messages")["uri"].endswith("/v1/messages")  # native pass-through (§15.5)


def test_gw02_output_token_caps_enforced_server_side():
    assert route("openai-chat-completions")["plugins"]["ai-proxy"]["override"]["max_completion_tokens"] == 4096
    assert route("anthropic-messages")["plugins"]["ai-proxy"]["override"]["max_tokens"] == 4096


# ------------------------------------------------------------------ GW-03/08: SSE event order through terminators


def test_gw03_openai_sse_ends_with_done_terminator():
    raw = (FIXTURES / "openai_sse.txt").read_text()
    events = parse_sse_events(raw)
    datas = [d for _, d in events]
    assert datas[-1] == TERMINATOR_OPENAI
    assert TERMINATOR_OPENAI not in datas[:-1]  # terminator appears exactly once, last


def test_gw08_anthropic_sse_event_order_through_message_stop():
    raw = (FIXTURES / "anthropic_sse.txt").read_text()
    order = [e for e, _ in parse_sse_events(raw)]
    assert order[0] == "message_start"
    assert order[-1] == TERMINATOR_ANTHROPIC
    assert order[-2] == "message_delta"
    assert order.index("content_block_start") < order.index("content_block_delta")
    assert order.count(TERMINATOR_ANTHROPIC) == 1


# ------------------------------------------------------------------ GW-09: tool semantics per protocol


def test_gw09_openai_tool_call_round_trip():
    payload = json.loads((FIXTURES / "openai_tool_call.json").read_text())
    completion = OpenAIChatCompletion.model_validate(payload)
    assert completion.choices[0].finish_reason == "tool_calls"


def test_gw09_anthropic_tool_use_block_preserved():
    payload = json.loads((FIXTURES / "anthropic_tool_use.json").read_text())
    msg = AnthropicMessage.model_validate(payload)
    tool_block = next(b for b in msg.content if b.type == "tool_use")
    assert tool_block.name == "query_pipeline"
    assert msg.stop_reason == "tool_use"  # Anthropic semantics, not reinterpreted (ADR-022)


def test_gw09_content_blocks_and_stop_reason_survive_validation():
    payload = json.loads((FIXTURES / "anthropic_tool_use.json").read_text())
    msg = AnthropicMessage.model_validate(payload)
    assert all(isinstance(b, AnthropicContentBlock) for b in msg.content)
    assert msg.usage.output_tokens > 0


# ------------------------------------------------------------------ GW-10: bounded retry/fallback (criterion 6)


def _ai_routes() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in routes()["routes"]:
        plugins = r.get("plugins", {})
        for key in ("ai-proxy", "ai-proxy-multi"):
            if key in plugins:
                out[f"{r['name']} ({key})"] = plugins[key]
    return out


def test_gw10_multi_provider_policy_has_bounded_retries():
    """§15.4 internal-capability-pool: retries bounded; no unbounded latency."""
    multi = _ai_routes()["internal-capability-pool (ai-proxy-multi)"]
    retries = multi["retries"]
    assert 1 <= retries["max_retries"] <= 3                      # bounded, small
    assert retries["retry_on"] == ["http_429", "http_5xx"]       # only retryable classes
    assert retries["retry_on_failure_within_ms"] <= 10000        # never retry old calls


def test_gw10_retry_window_never_exceeds_timeout():
    """A retry can never extend a call past its own timeout — no duplicate long calls."""
    multi = _ai_routes()["internal-capability-pool (ai-proxy-multi)"]
    assert multi["retries"]["retry_on_failure_within_ms"] < multi["timeout_ms"]
    assert multi["timeout_ms"] < multi["max_stream_duration_ms"]


def test_gw10_all_ai_routes_have_time_and_size_bounds():
    for name, cfg in _ai_routes().items():
        assert cfg["timeout_ms"] > 0, f"{name}: missing timeout"
        assert cfg["max_response_bytes"] > 0, f"{name}: missing response size cap"
        if "max_stream_duration_ms" in cfg:
            assert cfg["timeout_ms"] <= cfg["max_stream_duration_ms"], f"{name}: timeout exceeds stream cap"
        logging_cfg = cfg.get("logging", {})
        assert logging_cfg.get("payloads") is not True            # payloads off everywhere (§21)


def test_gw10_no_platform_key_fallback():
    """Criterion 6: every credential on every AI route resolves from tenant BYOK in Vault."""
    for name, cfg in _ai_routes().items():
        auth = cfg.get("auth") or {}
        providers = cfg.get("provider-order") or [{"provider": cfg.get("provider", ""), "auth": auth}]
        for p in providers:
            pa = p.get("auth", auth)
            values = list(pa.get("header", {}).values())
            assert values, f"{name}: no credential"
            for v in values:
                assert "$SECRET://vault/1/byok/" in v, f"{name}/{p.get('provider')}: platform fallback forbidden"
