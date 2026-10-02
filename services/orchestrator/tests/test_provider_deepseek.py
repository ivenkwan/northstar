"""DeepSeek adapter tests — offline wire-fixture replay, no network in CI (FR-6).

Vault and DeepSeek are exercised through an httpx mock transport injected into
the real code path; fixture credential strings below are synthetic placeholders
(e.g. "fixture-..."), never real secrets. T15 asserts they leak nowhere.
"""

import json

import httpx
import pytest
from orchestrator.errors import AICredentialUnavailableError, ProviderUnavailableError
from orchestrator.pipeline import Intent, Orchestrator, Risk, verify_trace_chain
from orchestrator.provider_deepseek import (
    BACKOFF_SECONDS,
    DEEPSEEK_TIMEOUT,
    DEGRADATION_CHAR_LIMIT,
    VAULT_SECRET_PATH,
    VAULT_TIMEOUT,
    DeepSeekProvider,
)
from orchestrator.scope import OrgGraph, Person, Role, ScopeResolver, Team

VAULT_ADDR = "http://127.0.0.1:8200"
VAULT_TOKEN = "fixture-vault-token"  # synthetic placeholder — never a real credential
API_KEY = "fixture-deepseek-key"     # synthetic placeholder — never a real credential
SANITIZED_MESSAGE = "AI credential unavailable for provider deepseek"

VALID_TURN = {
    "intent": "pipeline_question",
    "risk": "low",
    "answer": "Acme renewal is on track for the quarter.",
    "components": [
        {"type": "narrative", "title": "Summary", "payload": {"text": "Acme renewal is on track."}},
        {"type": "evidence_chips", "payload": {"refs": []}},
    ],
}
VALID_CONTENT = json.dumps(VALID_TURN)


class RouterTransport(httpx.BaseTransport):
    """Routes recorded Vault/DeepSeek wire behavior and records every request."""

    def __init__(self, vault, deepseek) -> None:
        self.vault, self.deepseek = vault, deepseek
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.host == "api.deepseek.com":
            return self.deepseek(request)
        return self.vault(request)


def vault_ok(key=API_KEY, status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status)
        body = {"data": {"data": {}}} if key is None else {"data": {"data": {"api_key": key}}}
        return httpx.Response(200, json=body)
    return handler


def deepseek_content(content: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": content}}]})
    return handler


def make_provider(monkeypatch, vault=None, deepseek=None):
    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)
    monkeypatch.setenv("VAULT_TOKEN", VAULT_TOKEN)
    transport = RouterTransport(vault or vault_ok(), deepseek or deepseek_content(VALID_CONTENT))
    sleeps: list[float] = []
    return DeepSeekProvider(transport=transport, sleep=sleeps.append), transport, sleeps


def _deepseek_requests(transport):
    return [r for r in transport.requests if r.url.host == "api.deepseek.com"]


def _vault_requests(transport):
    return [r for r in transport.requests if r.url.host != "api.deepseek.com"]


# ------------------------------------------------------------------ T1: wire-fixture happy path


def test_t1_happy_path_request_construction_and_mapping(monkeypatch):
    provider, transport, _ = make_provider(monkeypatch)
    intent, risk = provider.classify("What is my attainment this quarter?")
    assert (intent, risk) == (Intent.PIPELINE_QUESTION, Risk.LOW)

    req = _deepseek_requests(transport)[0]
    assert req.method == "POST"
    assert str(req.url) == "https://api.deepseek.com/chat/completions"
    assert req.headers["Authorization"] == f"Bearer {API_KEY}"
    assert req.headers["Content-Type"] == "application/json"
    body = json.loads(req.content)
    assert body["model"] == "deepseek-chat"
    assert body["temperature"] == 0
    assert body["max_tokens"] == 4096
    assert "response_format" not in body  # no JSON mode (FR-3.2)
    assert "stream" not in body           # non-streaming (FR-3.2)
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert "What is my attainment this quarter?" in body["messages"][1]["content"]

    # one Vault read + one DeepSeek call per question (single-turn granularity)
    assert len(_vault_requests(transport)) == 1
    assert len(_deepseek_requests(transport)) == 1

    # validated output maps into pipeline components; degradation flag absent (T10)
    turn = provider.last_turn
    assert turn.degraded is False
    assert turn.answer_text == "Acme renewal is on track for the quarter."
    assert [c.type for c in turn.components] == ["narrative", "evidence_chips"]
    assert turn.components[0].title == "Summary"
    assert all("degraded" not in c.payload for c in turn.components)
    assert provider.answer("What is my attainment this quarter?", context="metrics") == turn.answer_text

    # the step-12 fallback answer() call reuses the same turn — no second model call
    provider.answer("What is my attainment this quarter?", context="final")
    assert len(_deepseek_requests(transport)) == 1


# ------------------------------------------------------------------ T2–T5: fail-closed credentials


def test_t2_secret_absent(monkeypatch):
    provider, _, _ = make_provider(monkeypatch, vault=vault_ok(status=404))
    with pytest.raises(AICredentialUnavailableError) as exc:
        provider.classify("q")
    assert exc.value.message == SANITIZED_MESSAGE
    assert API_KEY not in str(exc.value) and VAULT_TOKEN not in str(exc.value)


def test_t3a_malformed_or_unset_vault_addr(monkeypatch):
    for addr in ("", "not-a-url", "ftp://vault", "127.0.0.1:8200"):
        provider, _, _ = make_provider(monkeypatch)
        monkeypatch.setenv("VAULT_ADDR", addr)  # override after wiring; env is read at call time
        with pytest.raises(AICredentialUnavailableError) as exc:
            provider.classify("q")
        assert exc.value.message == SANITIZED_MESSAGE
        if addr:
            assert addr not in str(exc.value)


def test_t3b_unset_vault_token(monkeypatch):
    provider, _, _ = make_provider(monkeypatch)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(AICredentialUnavailableError):
        provider.answer("q", context="metrics")


def test_t4_vault_unreachable(monkeypatch):
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider, _, _ = make_provider(monkeypatch, vault=unreachable)
    with pytest.raises(AICredentialUnavailableError) as exc:
        provider.classify("q")
    assert exc.value.message == SANITIZED_MESSAGE  # identical handling to a missing key


def test_t4b_vault_timeout(monkeypatch):
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("read timed out")

    provider, _, _ = make_provider(monkeypatch, vault=slow)
    with pytest.raises(AICredentialUnavailableError):
        provider.classify("q")


def test_t5_missing_or_invalid_api_key_field(monkeypatch):
    cases = [vault_ok(key=None), vault_ok(key=""), vault_ok(key=12345)]
    for vault in cases:
        provider, _, _ = make_provider(monkeypatch, vault=vault)
        with pytest.raises(AICredentialUnavailableError) as exc:
            provider.classify("q")
        assert exc.value.message == SANITIZED_MESSAGE


def test_t5b_missing_data_envelope(monkeypatch):
    def broken(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": ["no data"]})

    provider, _, _ = make_provider(monkeypatch, vault=broken)
    with pytest.raises(AICredentialUnavailableError):
        provider.classify("q")


# ------------------------------------------------------------------ T6: Vault KV v2 read semantics


def test_t6_vault_kv2_read_url_token_and_reread(monkeypatch):
    provider, transport, _ = make_provider(monkeypatch)
    provider.classify("first question")
    provider.classify("second question")  # new question → new provider invocation
    vault_reqs = _vault_requests(transport)
    assert len(vault_reqs) == 2  # re-read on every call — no process-level caching
    for req in vault_reqs:
        assert req.method == "GET"
        assert req.url.path == VAULT_SECRET_PATH == "/v1/secret/data/byok/local/deepseek/primary"
        assert req.headers["X-Vault-Token"] == VAULT_TOKEN
    # data.data.api_key unwrapping reaches the DeepSeek call as the bearer key
    assert _deepseek_requests(transport)[0].headers["Authorization"] == f"Bearer {API_KEY}"


# ------------------------------------------------------------------ T7: retry bounds


def test_t7a_retries_on_5xx_429_then_succeeds(monkeypatch):
    statuses = [500, 429, 200]

    def flaky(request: httpx.Request) -> httpx.Response:
        status = statuses.pop(0)
        if status == 200:
            return httpx.Response(200, json={"choices": [{"message": {"content": VALID_CONTENT}}]})
        return httpx.Response(status)

    provider, transport, sleeps = make_provider(monkeypatch, deepseek=flaky)
    assert provider.answer("q", context="metrics") == "Acme renewal is on track for the quarter."
    assert len(_deepseek_requests(transport)) == 3  # initial + exactly 2 retries
    assert sleeps == [0.5, 2.0]                    # exponential backoff


def test_t7b_retries_on_read_timeout(monkeypatch):
    calls = {"n": 0}

    def slow(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] <= 2:
            raise httpx.ReadTimeout("read timed out")
        return httpx.Response(200, json={"choices": [{"message": {"content": VALID_CONTENT}}]})

    provider, transport, sleeps = make_provider(monkeypatch, deepseek=slow)
    provider.classify("q")
    assert len(_deepseek_requests(transport)) == 3
    assert sleeps == [0.5, 2.0]


def test_t7c_exhausted_retries_raise_typed_provider_error(monkeypatch):
    def down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("connect timed out")

    provider, transport, sleeps = make_provider(monkeypatch, deepseek=down)
    with pytest.raises(ProviderUnavailableError) as exc:
        provider.classify("q")
    assert len(_deepseek_requests(transport)) == 3
    assert sleeps == [0.5, 2.0]
    assert exc.value.retryable is True
    assert API_KEY not in str(exc.value)  # sanitized — status/timing only


def test_t7d_no_retry_on_other_client_errors(monkeypatch):
    for status in (400, 401, 403, 422):

        def reject(request: httpx.Request, status=status) -> httpx.Response:
            return httpx.Response(status)

        provider, transport, sleeps = make_provider(monkeypatch, deepseek=reject)
        with pytest.raises(ProviderUnavailableError) as exc:
            provider.classify("q")
        assert len(_deepseek_requests(transport)) == 1  # no retry
        assert sleeps == []
        assert f"HTTP {status}" in exc.value.message


def test_t7e_transport_bounds_configured():
    assert DEEPSEEK_TIMEOUT.connect == 5.0 and DEEPSEEK_TIMEOUT.read == 30.0
    assert VAULT_TIMEOUT.connect == 5.0 and VAULT_TIMEOUT.read == 10.0
    assert BACKOFF_SECONDS == (0.5, 2.0)


# ------------------------------------------------------------------ T8–T11: degradation (GA-05)


def _degrade_with(monkeypatch, content):
    provider, _, _ = make_provider(monkeypatch, deepseek=deepseek_content(content))
    text = provider.answer("q", context="metrics")
    return provider, text


def _assert_single_flagged_component(turn, expected_text):
    assert turn.degraded is True
    assert len(turn.components) == 1  # exactly one plain-text component
    component = turn.components[0]
    assert component.type == "narrative"
    assert component.payload["degraded"] is True
    assert component.payload["text"] == expected_text
    assert not any(c.type in ("kpi", "kpi_table") for c in turn.components)  # no metrics — never invented


def test_t8_malformed_json_degrades(monkeypatch):
    provider, text = _degrade_with(monkeypatch, "Acme is fine (definitely not JSON)")
    _assert_single_flagged_component(provider.last_turn, "Acme is fine (definitely not JSON)")
    assert text == "Acme is fine (definitely not JSON)"
    assert provider.classify("q") == (Intent.PIPELINE_QUESTION, Risk.LOW)


@pytest.mark.parametrize("envelope", [
    {"intent": "pipeline_question", "risk": "low", "components": []},                     # missing answer
    {"intent": "chitchat", "risk": "low", "answer": "hi", "components": []},             # unknown intent
    {"intent": "pipeline_question", "risk": "extreme", "answer": "hi", "components": []},  # unknown risk
    {"intent": "pipeline_question", "risk": "low", "answer": "", "components": []},      # empty answer
    {"intent": "pipeline_question", "risk": "low", "answer": "hi"},                      # missing components
    {"intent": "pipeline_question", "risk": "low", "answer": "hi", "components": [], "extra": 1},  # extra key
    {"intent": "pipeline_question", "risk": "low", "answer": 42, "components": []},       # non-string answer
    {"intent": "pipeline_question", "risk": "low", "answer": "hi",
     "components": [{"type": "gauge", "payload": {"value": "made-up"}}]},                # invalid component type
    {"intent": "pipeline_question", "risk": "low", "answer": "hi",
     "components": [{"type": "narrative", "payload": "text-not-object"}]},               # payload not a dict
])
def test_t9_schema_invalid_json_degrades(monkeypatch, envelope):
    provider, text = _degrade_with(monkeypatch, json.dumps(envelope))
    _assert_single_flagged_component(provider.last_turn, json.dumps(envelope))
    assert text.startswith("{")


def test_t9b_malformed_choices_envelope_degrades(monkeypatch):
    raw = '{"id":"resp_1","object":"chat.completion"}'  # no choices[0].message.content

    def broken(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=raw)

    provider, _, _ = make_provider(monkeypatch, deepseek=broken)
    provider.classify("q")
    _assert_single_flagged_component(provider.last_turn, raw)


def test_t9c_non_json_success_body_degrades(monkeypatch):
    def html(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>upstream proxy page</html>")

    provider, _, _ = make_provider(monkeypatch, deepseek=html)
    provider.classify("q")
    _assert_single_flagged_component(provider.last_turn, "<html>upstream proxy page</html>")


def test_t11_oversized_output_truncated_to_4000(monkeypatch):
    provider, text = _degrade_with(monkeypatch, "x" * 6000)
    _assert_single_flagged_component(provider.last_turn, "x" * DEGRADATION_CHAR_LIMIT)
    assert len(text) == 4000 == DEGRADATION_CHAR_LIMIT


# ------------------------------------------------------------------ T15: no-secret-leak sweep


def test_t15_no_credential_leakage_in_any_error_surface(monkeypatch):
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    scenarios = [
        vault_ok(status=404),          # secret absent
        vault_ok(key=None),            # missing api_key field
        vault_ok(key=""),              # empty api_key
        unreachable,                   # Vault unreachable
    ]
    captured: list[str] = []
    for vault in scenarios:
        provider, _, _ = make_provider(monkeypatch, vault=vault)
        try:
            provider.classify("q")
        except AICredentialUnavailableError as exc:
            captured.append(f"{exc.code.value}:{exc.message}")
        else:
            raise AssertionError("expected fail-closed AICredentialUnavailableError")
    assert len(captured) == len(scenarios)
    for blob in captured:
        assert API_KEY not in blob and VAULT_TOKEN not in blob  # only the sanitized message surfaces


# ------------------------------------------------------------------ seam integration (offline)


def test_full_pipeline_with_deepseek_provider_keeps_trace_owned(monkeypatch):
    provider, _, _ = make_provider(monkeypatch)
    graph = OrgGraph(
        people=[Person(salesperson_id="s1", user_id="u_s1", primary_team_id="t1", valid_from="2026-01-01")],
        teams=[Team(team_id="t1", domain_id="dom1", manager_id="s1", valid_from="2026-01-01")],
    )
    orch = Orchestrator(provider)
    token = ScopeResolver(graph, {"u_s1": Role.SELLER}).resolve("u_s1", "2026-09-01")
    out = orch.run("u_s1", "What is my attainment?", token)
    assert out.answer == "Acme renewal is on track for the quarter."
    assert out.components[0].type == "narrative"
    assert out.components[0].payload["text"] == out.answer  # §19.3 shape downstream
    assert verify_trace_chain(orch.traces)  # hash-chained trace remains pipeline-owned
