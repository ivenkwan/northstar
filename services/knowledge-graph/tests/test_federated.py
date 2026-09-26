from datetime import UTC, datetime, timedelta

from knowledge_graph.federated import FederatedDoc, SourcePolicy, federated_query

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

POLICIES = {
    "research_hub": SourcePolicy(source_id="research_hub", approved=True,
                                 classification_ceiling="internal"),
    "confidential_deals": SourcePolicy(source_id="confidential_deals", approved=True,
                                       classification_ceiling="confidential"),
    "unapproved_wiki": SourcePolicy(source_id="unapproved_wiki", approved=False),
}


def doc(source, doc_id, **kw) -> FederatedDoc:
    defaults = dict(source_id=source, doc_id=doc_id, title=f"doc {doc_id}",
                    retrieved_at=NOW - timedelta(minutes=5))
    defaults.update(kw)
    return FederatedDoc(**defaults)


def test_unapproved_and_unknown_sources_excluded():
    result = federated_query(
        [doc("research_hub", "ok"), doc("unapproved_wiki", "nope"), doc("mystery", "who")],
        POLICIES, user_scope_ids=set(), as_of=NOW)
    assert [d.doc_id for d in result.docs] == ["ok"]
    assert set(result.excluded_sources) == {"unapproved_wiki", "mystery"}


def test_classification_ceiling_enforced_before_return():
    result = federated_query(
        [doc("research_hub", "conf", classification="confidential"),
         doc("research_hub", "int", classification="internal")],
        POLICIES, user_scope_ids=set(), as_of=NOW)
    assert [d.doc_id for d in result.docs] == ["int"]  # ceiling internal blocks confidential
    assert result.redacted_count == 1


def test_scope_matching_redacts_other_peoples_docs():
    result = federated_query(
        [doc("confidential_deals", "mine", scope_owner="s1"),
         doc("confidential_deals", "theirs", scope_owner="s2")],
        POLICIES, user_scope_ids={"s1"}, as_of=NOW)
    assert [d.doc_id for d in result.docs] == ["mine"]
    assert result.redacted_count == 1


def test_stale_docs_age_out_by_source_sla():
    stale = doc("research_hub", "old", retrieved_at=NOW - timedelta(hours=3))
    result = federated_query([stale], POLICIES, user_scope_ids=set(), as_of=NOW)
    assert result.docs == []  # aged out, not returned stale (§14.3)


def test_every_returned_doc_carries_source_provenance():
    result = federated_query([doc("research_hub", "ok")], POLICIES, user_scope_ids=set(), as_of=NOW)
    assert result.docs[0].source_id == "research_hub"
