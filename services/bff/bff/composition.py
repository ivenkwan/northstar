"""Composition root: BFF ↔ orchestrator ↔ metrics wired in-process for local dev.

Production splits these into separate services behind APISIX (§13); locally the
same objects run in one process so the whole §9.2 pipeline executes end-to-end
against the real engines. The provider is the deterministic ScriptedProvider —
no network, no keys (§13.1 mobile trust boundary holds even in dev).
"""

from __future__ import annotations

import os
from datetime import date
from uuid import uuid4

from orchestrator.errors import ConfigError
from orchestrator.pipeline import Intent, MetricRow, Orchestrator, Risk, ScriptedProvider
from orchestrator.scope import OrgGraph, Person, Role, ScopeResolver, Team

from .api import OrchestratorDep


def _dev_org() -> tuple[OrgGraph, dict[str, Role]]:
    graph = OrgGraph(
        people=[Person(salesperson_id="s1", user_id="u_dev", primary_team_id="t1", valid_from=date(2026, 1, 1))],
        teams=[Team(team_id="t1", domain_id="dom1", manager_id="s1", valid_from=date(2026, 1, 1))],
    )
    return graph, {"u_dev": Role.SELLER}


def _dev_metrics(user_id: str) -> list[MetricRow]:
    """Scenario-A-shaped dev data (§28.1) so conversations carry real governed numbers."""
    if os.environ.get("NORTHSTAR_DEV_DATA", "1") != "1":
        return []
    from metrics.engine import Opportunity, PlanRow, compute_attainment_report

    opps = [
        Opportunity(opportunity_id="o1", owner_id="s1", account_id="acct_1", amount_minor=600_000,
                    forecast_category="closed", is_open=False),
        Opportunity(opportunity_id="o2", owner_id="s1", account_id="acct_1", amount_minor=400_000,
                    probability=0.9, forecast_category="commit"),
    ]
    plans = [PlanRow(assignee_id="s1", period="FY27-Q1", target_minor=1_000_000)]
    graph, _ = _dev_org()
    salesperson = next(p.salesperson_id for p in graph.people if p.user_id == user_id)
    return [
        MetricRow(metric_id=r.metric_id, version=r.version, value=r.value, owner_id=salesperson)
        for r in compute_attainment_report(opps, plans, salesperson, "FY27-Q1", "2026-09-26T09:00:00Z")
    ]


def serialize(answer, user_id: str) -> dict:
    """ConversationAnswer (snake_case) → §19.3 wire shape (camelCase, contract-tested)."""
    return {
        "messageId": f"msg_{uuid4().hex[:10]}",
        "answer": answer.answer,
        "scope": {"type": answer.scope_type, "id": answer.scope_id, "asOf": answer.as_of},
        "components": [
            {"type": c.type, **({"title": c.title} if c.title else {}), "payload": c.payload}
            for c in answer.components
        ],
        "evidence": [{"type": e.type, "ref": e.ref, "label": e.label} for e in answer.evidence],
        "warnings": list(answer.warnings),
        "suggestedActions": list(answer.suggested_actions),
    }


def _select_provider():
    """NORTHSTAR_PROVIDER selection — exact, case-sensitive, fail-closed (NFR-5).

    Unset/`scripted` keeps the deterministic default (zero test regression);
    `deepseek` wires the real adapter; anything else refuses to boot.
    """
    name = os.environ.get("NORTHSTAR_PROVIDER", "scripted")
    if name == "scripted":
        return ScriptedProvider(intent=Intent.PIPELINE_QUESTION, risk=Risk.LOW)
    if name == "deepseek":
        from orchestrator.provider_deepseek import DeepSeekProvider

        return DeepSeekProvider()
    raise ConfigError(f"Unknown NORTHSTAR_PROVIDER value: {name!r}")


class LiveOrchestratorDep(OrchestratorDep):
    """Runs the real 12-step pipeline in-process with the selected model provider."""

    def __init__(self) -> None:
        graph, roles = _dev_org()
        self._resolver = ScopeResolver(graph, roles)
        self._provider = _select_provider()

    async def converse(self, user: str, text: str) -> dict:
        orch = Orchestrator(self._provider)
        token = self._resolver.resolve(user, date(2026, 9, 26))
        answer = orch.run(user, text, token, metrics=_dev_metrics(user))
        return serialize(answer, user)


# ------------------------------------------------------------------ briefing wiring (§7.1/§9.1)


def _dev_deals() -> list:
    from orchestrator.briefing import DealSnapshot

    return [
        DealSnapshot(opportunity_id="opp_1", account_id="acct_1", name="ACME renewal", owner_id="s1",
                     amount_minor=400_000, stage="middle", probability=0.6, close_date="2026-12-15",
                     stage_age_days=70, days_since_activity=30, close_date_push_count=2,
                     has_next_step=False),
        DealSnapshot(opportunity_id="opp_2", account_id="acct_2", name="BetaSoft expansion", owner_id="s1",
                     amount_minor=250_000, stage="early", probability=0.3, close_date="2027-03-31",
                     stage_age_days=10, days_since_activity=4, close_date_push_count=0,
                     has_next_step=True),
    ]


def _dev_signals() -> list:
    from orchestrator.briefing import SignalItem

    return [
        SignalItem(signal_type="expansion", entity="Acme Corp",
                   headline="Acme expands APAC data-centre footprint",
                   source="licensed_wire", published_at="2026-09-26T08:00:00Z", confidence=0.9),
        SignalItem(signal_type="regulation", entity="BetaSoft",
                   headline="Regulator fines BetaSoft over disclosures",
                   source="licensed_wire", published_at="2026-09-25T10:00:00Z", confidence=0.8),
    ]


def _briefing_out(b) -> dict:
    kpis = [{"metricId": k.metric_id, "version": k.version, "value": k.value, "unit": k.unit} for k in b.kpis]
    top_risks = [{
        "opportunityId": r.opportunity_id, "name": r.name, "headline": r.headline,
        "summary": list(r.summary), "nextSteps": list(r.next_steps),
        "topSeverity": r.indicators[0].severity if r.indicators else "none",
        "riskCount": len(r.indicators),
    } for r in b.top_risks]
    signals = [{"signalType": s.signal_type, "entity": s.entity, "headline": s.headline,
                "source": s.source, "publishedAt": s.published_at, "confidence": s.confidence}
               for s in b.market_signals]
    evidence = [{"type": e.type, "ref": e.ref, "label": e.label} for e in b.evidence]
    return {"asOf": b.as_of, "scopeId": b.scope_id, "greeting": b.greeting, "kpis": kpis,
            "topRisks": top_risks, "marketSignals": signals,
            "overdueActions": b.overdue_actions, "evidence": evidence}


def _deal_brief_out(brief) -> dict:
    ind = [{"kind": i.kind, "detail": i.detail, "severity": i.severity} for i in brief.indicators]
    ev = [{"type": e.type, "ref": e.ref, "label": e.label} for e in brief.evidence]
    return {"opportunityId": brief.opportunity_id, "accountId": brief.account_id, "name": brief.name,
            "ownerId": brief.owner_id, "asOf": brief.as_of, "headline": brief.headline,
            "summary": list(brief.summary), "indicators": ind, "risks": ind,
            "nextSteps": list(brief.next_steps), "evidence": ev}


class LiveBriefingDep:
    """Wires the briefing engines with dev data; production swaps the data sources."""

    async def today(self, user: str) -> dict:
        from orchestrator.briefing import compose_daily_briefing

        graph, _ = _dev_org()
        salesperson = next(p.salesperson_id for p in graph.people if p.user_id == user)
        rows = _dev_metrics(user)
        deals = [d for d in _dev_deals() if d.owner_id == salesperson]
        briefing = compose_daily_briefing("2026-09-27T08:00:00Z", user, rows, deals, _dev_signals())
        return _briefing_out(briefing)

    async def deal_brief(self, opportunity_id: str) -> dict | None:
        from orchestrator.briefing import compose_deal_brief

        for d in _dev_deals():
            if d.opportunity_id == opportunity_id:
                return _deal_brief_out(compose_deal_brief(d, "2026-09-27T08:00:00Z"))
        return None
