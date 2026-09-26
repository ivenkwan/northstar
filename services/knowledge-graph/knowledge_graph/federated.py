"""Federated retrieval across approved internal knowledge sources (Phase 3, §24.4).

Fan-out query over a source registry where each source carries its own policy:
approval status, classification ceiling, freshness SLA, and scope rules. Results
merge with per-source provenance, and classification filtering happens BEFORE
anything is returned — no source can bypass policy (§11.1, §19.1 GraphQL rule
generalized to all federated reads).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

CLASSIFICATION_ORDER = {"public": 0, "internal": 1, "confidential": 2}  # ordered ceiling check


class SourcePolicy(BaseModel):
    source_id: str
    approved: bool = False
    classification_ceiling: str = "internal"   # highest classification it may return
    freshness_sla_minutes: int = 60
    requires_scope_match: bool = True          # results must pass scope filter


class FederatedDoc(BaseModel):
    source_id: str
    doc_id: str
    title: str
    classification: str = "internal"
    scope_owner: str | None = None             # None = org-wide
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FederatedResult(BaseModel):
    docs: list[FederatedDoc] = Field(default_factory=list)
    excluded_sources: list[str] = Field(default_factory=list)
    redacted_count: int = 0


def _class_ok(doc_class: str, ceiling: str) -> bool:
    return CLASSIFICATION_ORDER.get(doc_class, 99) <= CLASSIFICATION_ORDER[ceiling]


def federated_query(docs: list[FederatedDoc], policies: dict[str, SourcePolicy],
                    user_scope_ids: set[str],
                    as_of: datetime | None = None) -> FederatedResult:
    as_of = as_of or datetime.now(UTC)
    excluded: list[str] = []
    redacted = 0
    out: list[FederatedDoc] = []
    for doc in docs:
        policy = policies.get(doc.source_id)
        if policy is None or not policy.approved:
            if policy is not None and policy.source_id not in excluded:
                excluded.append(policy.source_id)
            elif policy is None and doc.source_id not in excluded:
                excluded.append(doc.source_id)
            continue  # unapproved/unknown sources never contribute
        if not _class_ok(doc.classification, policy.classification_ceiling):
            redacted += 1
            continue
        if policy.requires_scope_match and doc.scope_owner is not None and doc.scope_owner not in user_scope_ids:
            redacted += 1
            continue
        if as_of - doc.retrieved_at > timedelta(minutes=policy.freshness_sla_minutes):
            continue  # stale docs silently age out (§14.3 discipline)
        out.append(doc)
    return FederatedResult(docs=out, excluded_sources=excluded, redacted_count=redacted)
