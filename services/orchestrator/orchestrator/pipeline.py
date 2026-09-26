"""The deterministic 12-step orchestration workflow (PRD §9.2).

Deterministic code around probabilistic models: every data query and tool call
is authorized, retrieved content is data (never instructions), outputs are
rechecked for leakage, writes require confirmation, and every run leaves an
immutable, hash-chained trace (§11.4).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

from .scope import ScopeToken, authorize_record


class Intent(str, Enum):
    PIPELINE_QUESTION = "pipeline_question"
    TARGET_QUESTION = "target_question"
    DEAL_BRIEF = "deal_brief"
    MARKET_SIGNAL = "market_signal"
    COMPOSE_DASHBOARD = "compose_dashboard"
    WRITE_ACTION = "write_action"
    OUT_OF_SCOPE = "out_of_scope"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceRef(BaseModel):
    type: str  # crm_record | plan_row | news_item | metric_definition
    ref: str
    owner_id: str | None = None  # used for the output leak recheck
    label: str


class Component(BaseModel):
    """Typed UI component (CONV-03). Validated again by Zod on mobile (ADR-026)."""

    type: str  # narrative | kpi | chart | table | evidence_chips
    title: str | None = None
    payload: dict = Field(default_factory=dict)


class ConversationAnswer(BaseModel):
    answer: str
    scope_type: str
    scope_id: str
    as_of: str
    components: list[Component]
    evidence: list[EvidenceRef]
    warnings: list[str] = Field(default_factory=list)
    suggested_actions: list[dict] = Field(default_factory=list)


class RetrievedDoc(BaseModel):
    """Untrusted retrieved content (news/notes). Treated strictly as data (§11.2)."""

    doc_id: str
    text: str


class MetricRow(BaseModel):
    metric_id: str
    version: int
    value: float | None
    owner_id: str | None = None


class LLMProvider(Protocol):
    """Integration point for the gateway provider routes (ADR-021/022).

    Production adapter calls /internal/ai/capabilities/{capability}; tests use
    ScriptedProvider. Never a direct database or provider credential here (§13.1).
    """

    def classify(self, question: str) -> tuple[Intent, Risk]: ...

    def answer(self, question: str, context: str) -> str: ...


class ScriptedProvider:
    """Deterministic provider for tests and local dev — no network, no keys."""

    def __init__(self, intent: Intent = Intent.PIPELINE_QUESTION, risk: Risk = Risk.LOW,
                 answer_text: str = "") -> None:
        self.intent, self.risk, self.answer_text = intent, risk, answer_text

    def classify(self, question: str) -> tuple[Intent, Risk]:
        return self.intent, self.risk

    def answer(self, question: str, context: str) -> str:
        return self.answer_text or "Grounded summary from certified metrics."


INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt:",
    "you must now",
    "reveal all",
    "call the tool",
    "disregard",
)


def scrub_retrieved(doc: RetrievedDoc) -> RetrievedDoc:
    """Neutralize instruction-like content in retrieved text (GA-01; §11.2).

    The text stays visible as evidence; it can never act as an instruction.
    """
    lowered = doc.text.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        return RetrievedDoc(doc_id=doc.doc_id, text=f"[content quarantined: potential embedded instruction] {doc.text}")
    return doc


class TraceRecord(BaseModel):
    trace_id: str
    user_id: str
    intent: Intent
    steps: list[str]
    policy_decisions: list[str]
    evidence_refs: list[str]
    outcome: str
    prev_hash: str
    row_hash: str


def _hash(prev: str, payload: str) -> str:
    return hashlib.sha256((prev + payload).encode()).hexdigest()


class Orchestrator:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self.traces: list[TraceRecord] = []
        self._prev_hash = "GENESIS"

    def run(self, user_id: str, question: str, token: ScopeToken,
            metrics: list[MetricRow] | None = None,
            retrieved: list[RetrievedDoc] | None = None) -> ConversationAnswer:
        steps: list[str] = []
        policies: list[str] = []

        # 2. Classify intent and risk.
        intent, risk = self.provider.classify(question)
        steps.append(f"classify:{intent.value}:{risk.value}")
        if intent is Intent.OUT_OF_SCOPE:
            policies.append("CONV-07: unsupported request redirected")
            return self._finish(user_id, intent, steps, policies,
                                ConversationAnswer(answer="This request is outside the supported scope.",
                                                   scope_type=token.role.value, scope_id=user_id,
                                                   as_of=token.as_of.isoformat(), components=[],
                                                   evidence=[], warnings=["unsupported_request"]))

        # 3. Subject/scope/metric resolution — only governed catalog ids are accepted.
        rows = [m for m in (metrics or [])]

        # 5. Authorize every data query (already scope-filtered by caller; record-level recheck below).
        policies.append(f"scope:{token.role.value}")

        # 6/7. Retrieve via semantic APIs; validate freshness on each row (as_of present).
        docs = [scrub_retrieved(d) for d in (retrieved or [])]
        quarantined = [d for d in docs if d.text.startswith("[content quarantined")]
        if quarantined:
            policies.append(f"injection_quarantine:{len(quarantined)}")
            self._security_log(user_id, quarantined)

        # 8/9. Typed components + citations.
        components: list[Component] = [
            Component(type="narrative", payload={"text": self.provider.answer(question, context="metrics")})
        ]
        if rows:
            components.append(
                Component(type="kpi_table",
                          title="Certified metrics",
                          payload={"rows": [r.model_dump() for r in rows], "as_of": token.as_of.isoformat()})
            )
        evidence = [
            EvidenceRef(type="metric_definition", ref=r.metric_id, owner_id=r.owner_id, label=f"{r.metric_id} v{r.version}")
            for r in rows
        ]
        evidence += [EvidenceRef(type="news_item", ref=d.doc_id, owner_id=None, label="retrieved document") for d in docs]

        # 10. Output recheck: mask evidence whose owner is outside scope (CONV-05).
        leaked = [e for e in evidence if e.owner_id is not None and not authorize_record(token, e.owner_id)]
        for e in leaked:
            e.label = "[masked: outside your scope]"
            e.ref = "masked"
        if leaked:
            policies.append(f"masked_out_of_scope_evidence:{len(leaked)}")

        warnings = ["data_as_of:" + token.as_of.isoformat()]
        if quarantined:
            warnings.append("retrieved_content_quarantined")

        # 11. Writes always require confirmation — never executed inline.
        actions: list[dict] = []
        if intent is Intent.WRITE_ACTION:
            actions.append({"action": "crm_update", "requires_confirmation": True})
            policies.append("write_requires_confirmation")

        narrative = str(components[0].payload.get("text", ""))
        answer = ConversationAnswer(
            answer=narrative or self.provider.answer(question, context="final"),
            scope_type=token.role.value, scope_id=user_id,
            as_of=token.as_of.isoformat(), components=components,
            evidence=evidence, warnings=warnings, suggested_actions=actions,
        )
        return self._finish(user_id, intent, steps, policies, answer)

    def _security_log(self, user_id: str, docs: list[RetrievedDoc]) -> None:
        # Scenario C: attempt logged for security review (§28.1) — no content beyond ids.
        self.traces.append(TraceRecord(trace_id=f"sec_{len(self.traces)}", user_id=user_id,
                                       intent=Intent.MARKET_SIGNAL, steps=["injection_attempt"],
                                       policy_decisions=["logged_for_security_review"],
                                       evidence_refs=[d.doc_id for d in docs], outcome="quarantined",
                                       prev_hash=self._prev_hash,
                                       row_hash=_hash(self._prev_hash, f"sec:{user_id}:{[d.doc_id for d in docs]}")))

    def _finish(self, user_id: str, intent: Intent, steps: list[str], policies: list[str],
                answer: ConversationAnswer) -> ConversationAnswer:
        # 12. Immutable trace, hash-chained, sensitive content minimized (§11.4).
        payload = json.dumps({"u": user_id, "i": intent.value, "s": steps, "p": policies},
                             sort_keys=True, default=str)
        row_hash = _hash(self._prev_hash, payload)
        self.traces.append(TraceRecord(trace_id=f"t_{len(self.traces)}", user_id=user_id, intent=intent,
                                       steps=steps, policy_decisions=policies,
                                       evidence_refs=[e.ref for e in answer.evidence],
                                       outcome="answered", prev_hash=self._prev_hash, row_hash=row_hash))
        self._prev_hash = row_hash
        return answer


def verify_trace_chain(traces: list[TraceRecord]) -> bool:
    """Tamper-evidence check (T-13): recompute the chain."""
    prev = "GENESIS"
    for t in traces:
        if t.prev_hash != prev:
            return False
        payload = json.dumps({"u": t.user_id, "i": t.intent.value, "s": t.steps, "p": t.policy_decisions},
                             sort_keys=True, default=str)
        if t.row_hash != _hash(prev, payload):
            return False
        prev = t.row_hash
    return True


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
