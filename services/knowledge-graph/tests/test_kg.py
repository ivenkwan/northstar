import pytest
from knowledge_graph.ir import (
    EdgeKind,
    GraphEdge,
    GraphNode,
    GraphQueryIR,
    NodeKind,
    Subgraph,
    assert_no_raw_model_query,
    compile_cypher,
)


def test_ir_compiles_to_parameterized_cypher():
    ir = GraphQueryIR(start_kind=NodeKind.organization, start_key="acme", edge=EdgeKind.affects,
                      target_kind=NodeKind.domain, limit=25)
    q, p = compile_cypher(ir)
    assert q.startswith("MATCH (s:organization {key: $key})")
    assert "-[e:affects]->" in q
    assert "t:domain" in q
    assert "LIMIT $limit" in q
    assert p == {"key": "acme", "limit": 25}
    # The user key travels as a parameter — never interpolated.
    assert "acme" not in q


def test_inbound_and_multi_hop_directions():
    ir_in = GraphQueryIR(start_kind=NodeKind.person, start_key="p1", edge=EdgeKind.employs, edge_direction="in")
    q_in, _ = compile_cypher(ir_in)
    assert "<-[e:employs]-" in q_in
    ir_2h = GraphQueryIR(start_kind=NodeKind.domain, start_key="d1", edge=EdgeKind.relates_to, hops=2)
    q_2, _ = compile_cypher(ir_2h)
    assert "-[e:relates_to*1..2]->" in q_2  # bounded variable-length hop


def test_effective_dating_adds_validity_predicate():
    ir = GraphQueryIR(start_kind=NodeKind.group, start_key="grp_x", edge=EdgeKind.participates_in,
                      valid_at="2026-09-01")
    q, p = compile_cypher(ir)
    assert "e.valid_from <= $valid_at" in q and "e.valid_to IS NULL" in q
    assert p["valid_at"] == "2026-09-01"


def test_rejects_raw_model_generated_queries():
    with pytest.raises(ValueError):
        assert_no_raw_model_query("MATCH (n) DETACH DELETE n")  # raw Cypher from a model
    with pytest.raises(ValueError):
        assert_no_raw_model_query("SELECT * FROM opportunities")  # raw SQL from a model
    assert_no_raw_model_query("show me accounts affected by the merger")  # natural language is fine


def test_subgraph_bounds_enforced():
    nodes = [GraphNode(id=f"n{i}", kind=NodeKind.person, label=f"p{i}") for i in range(60)]
    edges = [GraphEdge(id=f"e{i}", source="n0", target=f"n{i}", relation=EdgeKind.employs,
                       confidence=1.0) for i in range(1, 60)]
    with pytest.raises(ValueError):
        Subgraph(nodes=nodes, edges=edges).bounded(max_nodes=50)
