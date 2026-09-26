"""Graph query IR and Cypher compiler (PRD §18; ADR-026/029).

Agents produce typed IR; this module compiles it to parameterized Cypher for
Apache AGE. Raw Cypher/Gremlin/SQL from a model is NEVER executed — the compiler
only accepts whitelisted identifiers and always emits parameters.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_HOPS = 3
MAX_LIMIT = 200


class NodeKind(str, Enum):
    organization = "organization"
    industry = "industry"
    domain = "domain"
    group = "group"
    person = "person"
    product = "product"
    event = "event"


class EdgeKind(str, Enum):
    owns = "owns"
    employs = "employs"
    classified_as = "classified_as"
    participates_in = "participates_in"
    relates_to = "relates_to"
    affects = "affects"


class GraphQueryIR(BaseModel):
    start_kind: NodeKind
    start_key: str = Field(min_length=1, max_length=200)  # exact-match key, parameterized
    edge: EdgeKind
    edge_direction: str = Field(default="out", pattern="^(out|in|both)$")
    hops: int = Field(default=1, ge=1, le=MAX_HOPS)
    target_kind: NodeKind | None = None
    limit: int = Field(default=50, ge=1, le=MAX_LIMIT)
    valid_at: str | None = None  # effective-dating filter


def compile_cypher(ir: GraphQueryIR) -> tuple[str, dict[str, object]]:
    """Compiles IR → parameterized Cypher for AGE. Identifier-whitelisted, bounded."""
    if not IDENT.match(ir.start_kind.value) or not IDENT.match(ir.edge.value):
        raise ValueError("identifier not whitelisted")
    depth = f"*1..{ir.hops}" if ir.hops > 1 else ""
    left, right = {"out": ("-", "->"), "in": ("<-", "-"), "both": ("-", "-")}[ir.edge_direction]
    rel = f"{left}[e:{ir.edge.value}{depth}]{right}"
    where_target = f" AND t:{ir.target_kind.value}" if ir.target_kind else ""
    valid = " AND e.valid_from <= $valid_at AND (e.valid_to IS NULL OR e.valid_to > $valid_at)" \
        if ir.valid_at else ""
    query = (
        f"MATCH (s:{ir.start_kind.value} {{key: $key}})"
        f"{rel}(t)"
        f" WHERE 1=1{where_target}{valid}"
        f" RETURN s, e, t LIMIT $limit"
    )
    params: dict[str, object] = {"key": ir.start_key, "limit": ir.limit}
    if ir.valid_at:
        params["valid_at"] = ir.valid_at
    return query, params


class GraphNode(BaseModel):
    id: str
    kind: NodeKind
    label: str
    attributes: dict = Field(default_factory=dict)
    provenance: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: EdgeKind
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: list[str] = Field(default_factory=list)


class Subgraph(BaseModel):
    """Bounded subgraph for mobile renderers (§18): hard caps, provenance attached."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]

    def bounded(self, max_nodes: int = 50, max_edges: int = 100) -> Subgraph:
        if len(self.nodes) > max_nodes or len(self.edges) > max_edges:
            raise ValueError("subgraph exceeds mobile bounds; narrow the query")
        return self


def assert_no_raw_model_query(text: str) -> None:
    """Guard (ADR-026 / §28.2 criterion 10): model-generated query text never executes."""
    lowered = text.lower()
    for marker in ("match (", "call {", "gremlin:", "g.v(", "select ", "drop ", "delete ", "create "):
        if marker in lowered:
            raise ValueError("raw model-generated query rejected")
