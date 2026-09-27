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


class LiveOrchestratorDep(OrchestratorDep):
    """Runs the real 12-step pipeline in-process with the scripted model provider."""

    def __init__(self) -> None:
        graph, roles = _dev_org()
        self._resolver = ScopeResolver(graph, roles)
        self._provider = ScriptedProvider(intent=Intent.PIPELINE_QUESTION, risk=Risk.LOW)

    async def converse(self, user: str, text: str) -> dict:
        orch = Orchestrator(self._provider)
        token = self._resolver.resolve(user, date(2026, 9, 26))
        answer = orch.run(user, text, token, metrics=_dev_metrics(user))
        return serialize(answer, user)
