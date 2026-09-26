"""Identity & Scope Agent (PRD §9.1): effective-dated scope resolution.

Resolves what a user may see at a point in time from the org model (§6):
membership, record ownership, reporting scope. This module powers the
permission golden suite (tests/golden, GPM-01..08).
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    SELLER = "seller"
    TEAM_MANAGER = "team_manager"
    DOMAIN_LEADER = "domain_leader"
    GROUP_LEADER = "group_leader"
    SALES_OPS = "sales_ops"
    EXECUTIVE = "executive"


class Person(BaseModel):
    salesperson_id: str
    user_id: str
    primary_team_id: str
    valid_from: date
    valid_to: date | None = None  # effective-dated transfers (§6.1)


class Team(BaseModel):
    team_id: str
    domain_id: str
    manager_id: str
    valid_from: date
    valid_to: date | None = None


class DomainGroup(BaseModel):
    domain_id: str
    group_id: str
    valid_from: date
    valid_to: date | None = None


class OrgGraph(BaseModel):
    people: list[Person]
    teams: list[Team]
    memberships: list[DomainGroup] = Field(default_factory=list)


class ScopeToken(BaseModel):
    """What the pipeline may query on this user's behalf (step 5: authorize every query)."""

    user_id: str
    role: Role
    visible_salesperson_ids: frozenset[str] = Field(default_factory=frozenset)
    visible_team_ids: frozenset[str] = Field(default_factory=frozenset)
    visible_domain_ids: frozenset[str] = Field(default_factory=frozenset)
    visible_group_ids: frozenset[str] = Field(default_factory=frozenset)
    masking: str = "standard"  # masking policy for inaccessible evidence (CONV-05)
    as_of: date


class ScopeResolver:
    def __init__(self, graph: OrgGraph, roles: dict[str, Role]) -> None:
        self.graph = graph
        self.roles = roles  # user_id -> role

    def _person_at(self, user_id: str, at: date) -> Person | None:
        for p in self.graph.people:
            if p.user_id == user_id and p.valid_from <= at and (p.valid_to is None or at < p.valid_to):
                return p
        return None

    def resolve(self, user_id: str, as_of: date | str) -> ScopeToken:
        if isinstance(as_of, str):
            as_of = date.fromisoformat(as_of)
        role = self.roles.get(user_id, Role.SELLER)
        person = self._person_at(user_id, as_of)
        if person is None:
            return ScopeToken(user_id=user_id, role=role, as_of=as_of, masking="denied")

        teams_now = [t for t in self.graph.teams if t.valid_from <= as_of and (t.valid_to is None or as_of < t.valid_to)]
        domains_now = {t.domain_id for t in teams_now}
        groups_now = [
            m for m in self.graph.memberships if m.valid_from <= as_of and (m.valid_to is None or as_of < m.valid_to)
        ]

        match role:
            case Role.SELLER:
                return ScopeToken(
                    user_id=user_id,
                    role=role,
                    visible_salesperson_ids=frozenset({person.salesperson_id}),
                    visible_team_ids=frozenset(),
                    as_of=as_of,
                )
            case Role.TEAM_MANAGER:
                my_teams = {t.team_id for t in teams_now if t.manager_id == person.salesperson_id}
                members = {
                    p.salesperson_id
                    for p in self.graph.people
                    if p.primary_team_id in my_teams and p.valid_from <= as_of and (p.valid_to is None or as_of < p.valid_to)
                }
                members |= {person.salesperson_id}
                return ScopeToken(
                    user_id=user_id,
                    role=role,
                    visible_salesperson_ids=frozenset(members),
                    visible_team_ids=frozenset(my_teams),
                    as_of=as_of,
                )
            case Role.DOMAIN_LEADER:
                my_domains = {t.domain_id for t in teams_now if t.manager_id == person.salesperson_id}
                # A domain leader sees every team in the domain (GPM-04), not just managed ones.
                my_domains |= {d for d in domains_now if any(t.manager_id == person.salesperson_id for t in teams_now if t.domain_id == d)}
                dom_teams = {t.team_id for t in teams_now if t.domain_id in my_domains}
                members = {p.salesperson_id for p in self.graph.people if p.primary_team_id in dom_teams}
                return ScopeToken(
                    user_id=user_id,
                    role=role,
                    visible_salesperson_ids=frozenset(members),
                    visible_team_ids=frozenset(dom_teams),
                    visible_domain_ids=frozenset(my_domains),
                    visible_group_ids=frozenset(m.group_id for m in groups_now if m.domain_id in my_domains),
                    as_of=as_of,
                )
            case Role.GROUP_LEADER:
                my_groups = {m.group_id for m in groups_now}
                doms = {m.domain_id for m in groups_now}
                dom_teams = {t.team_id for t in teams_now if t.domain_id in doms}
                members = {p.salesperson_id for p in self.graph.people if p.primary_team_id in dom_teams}
                return ScopeToken(
                    user_id=user_id,
                    role=role,
                    visible_salesperson_ids=frozenset(members),
                    visible_team_ids=frozenset(dom_teams),
                    visible_domain_ids=frozenset(doms),
                    visible_group_ids=frozenset(my_groups),
                    as_of=as_of,
                )
            case Role.SALES_OPS | Role.EXECUTIVE:
                members = {
                    p.salesperson_id for p in self.graph.people
                    if p.valid_from <= as_of and (p.valid_to is None or as_of < p.valid_to)
                }
                return ScopeToken(
                    user_id=user_id,
                    role=role,
                    visible_salesperson_ids=frozenset(members),
                    visible_team_ids=frozenset(t.team_id for t in teams_now),
                    visible_domain_ids=frozenset(domains_now),
                    visible_group_ids=frozenset(m.group_id for m in groups_now),
                    as_of=as_of,
                )


def authorize_record(token: ScopeToken, owner_id: str) -> bool:
    """Record-level authorization (ReBAC ownership; §11.1). Used by pipeline step 5 and output recheck."""
    return owner_id in token.visible_salesperson_ids
