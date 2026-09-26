"""Entity resolution (Phase 2 'richer entity graph'): maps surface forms and
aliases to canonical entities with confidence + provenance, feeding news
ingestion's entity_keys (§8.4) and the graph bundle builder (§18).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CanonicalEntity(BaseModel):
    entity_id: str
    kind: str                 # organization | person | product | ...
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)


class EntityMatch(BaseModel):
    entity_id: str
    matched_surface: str
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: str           # rule | alias_table | fuzzy


class EntityResolver:
    """Deterministic resolver: exact canonical name (1.0), known alias (0.95),
    normalized containment (0.7). Below a floor it abstains — an unmatched
    company never silently maps to a wrong account (§8.4 entity resolution)."""

    FLOOR = 0.7

    def __init__(self, entities: list[CanonicalEntity]) -> None:
        self._by_surface: dict[str, tuple[str, float, str]] = {}
        for e in entities:
            self._by_surface[e.canonical_name.lower()] = (e.entity_id, 1.0, "rule")
            for alias in e.aliases:
                self._by_surface[alias.lower()] = (e.entity_id, 0.95, "alias_table")

    def resolve(self, surface: str) -> EntityMatch | None:
        key = surface.strip().lower()
        exact = self._by_surface.get(key)
        if exact is not None:
            entity_id, conf, prov = exact
            return EntityMatch(entity_id=entity_id, matched_surface=surface, confidence=conf, provenance=prov)
        # normalized containment: "Acme Corp (APAC)" contains canonical "acme corp"
        for cand, (entity_id, _conf, _) in self._by_surface.items():
            if len(cand) >= 4 and cand in key:
                return EntityMatch(entity_id=entity_id, matched_surface=surface, confidence=0.7, provenance="fuzzy")
        return None  # abstain rather than guess

    def resolve_many(self, surfaces: list[str]) -> list[EntityMatch]:
        out: list[EntityMatch] = []
        seen: set[str] = set()
        for s in surfaces:
            m = self.resolve(s)
            if m is not None and m.entity_id not in seen:
                seen.add(m.entity_id)
                out.append(m)
        return out
