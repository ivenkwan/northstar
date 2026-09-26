from connectors.news import (
    Rights,
    RssAdapter,
    SourcePolicy,
    cluster_id_for,
    hamming,
    ingest,
    simhash,
)
from knowledge_graph.entities import CanonicalEntity, EntityResolver

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Telco Wire</title>
<item><guid>n-1</guid><title>Acme expands APAC data-centre footprint</title>
<link>https://example.com/n1</link><pubDate>Fri, 25 Sep 2026 08:00:00 GMT</pubDate>
<description>Acme Corp announced a major expansion of its APAC data-centre capacity.</description></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Fintech Feed</title>
<entry><id>a-9</id><title>Regulator fines BetaSoft over disclosures</title>
<link href="https://example.com/a9" rel="alternate"/>
<published>2026-09-25T10:00:00Z</published>
<summary>BetaSoft was fined for late disclosures.</summary></entry>
</feed>"""


def item(iid, title, body, source="licensed_wire"):
    from connectors.news import RawNewsItem

    return RawNewsItem(source_id=source, external_id=iid, title=title,
                       published_at="2026-09-25T10:00:00Z", url=f"https://example.com/{iid}", body=body)


POLICIES = {
    "licensed_wire": SourcePolicy(source_id="licensed_wire", license=Rights.FULL, retention_days=90),
    "free_aggregator": SourcePolicy(source_id="free_aggregator", license=Rights.RETRIEVAL_ONLY),
    "banned_source": SourcePolicy(source_id="banned_source", license=Rights.DENIED),
}


# ------------------------------------------------------------------ adapters


def test_rss_adapter_parses_items():
    items = RssAdapter("licensed_wire", RSS).fetch()
    assert len(items) == 1
    assert items[0].title.startswith("Acme expands")
    assert items[0].url == "https://example.com/n1"


def test_atom_adapter_parses_entries():
    items = RssAdapter("licensed_wire", ATOM).fetch()
    assert len(items) == 1
    assert items[0].external_id == "a-9"
    assert "BetaSoft" in items[0].body


# ------------------------------------------------------------------ rights enforcement


def test_unlicensed_and_denied_sources_excluded_at_ingestion():
    ingested, excluded = ingest(
        [item("n1", "t", "b", source="free_aggregator"),
         item("n2", "t", "b", source="banned_source"),
         item("n3", "t", "b")],  # licensed_wire
        POLICIES)
    assert len(ingested) == 1 and ingested[0].rights is Rights.FULL
    assert any("retrieval_only" in e for e in excluded)
    assert any("unlicensed_or_denied" in e for e in excluded)


def test_retention_carries_license_schedule():
    ingested, _ = ingest([item("n1", "t", "b")], POLICIES)
    assert ingested[0].retained_until == "+90d"


# ------------------------------------------------------------------ dedup clustering (§8.4)


def test_simhash_stable_and_similar_for_syndicated_copies():
    a = simhash("Acme expands APAC data-centre footprint Acme Corp announced expansion")
    a2 = simhash("Acme expands APAC data-centre footprint Acme Corp announced expansion")
    assert a == a2
    syndicated = simhash("Acme expands APAC data-centre footprint — Acme Corp announced expansion")
    unrelated = simhash("Regulator fines fintech firm over disclosure failures")
    assert hamming(a, syndicated) < hamming(a, unrelated)


def test_syndicated_copy_joins_existing_cluster():
    first, _ = ingest([item("n1", "Acme expands APAC data centre footprint", "Acme Corp announced expansion")], POLICIES)
    copy = item("n2", "Acme expands APAC data centre footprint", "Acme Corp announced expansion")
    assert cluster_id_for(copy, first) == first[0].cluster_id


def test_distinct_stories_start_distinct_clusters():
    first, _ = ingest([item("n1", "Acme expands APAC data centre footprint", "Acme Corp announced expansion")], POLICIES)
    other = item("n2", "Regulator fines fintech firm", "A regulator fined a fintech firm for late disclosures")
    assert cluster_id_for(other, first) != first[0].cluster_id


# ------------------------------------------------------------------ entity resolution


def test_entity_resolution_exact_alias_and_abstain():
    resolver = EntityResolver([
        CanonicalEntity(entity_id="ent_acme", kind="organization", canonical_name="Acme Corp",
                        aliases=["Acme", "Acme Corporation"]),
        CanonicalEntity(entity_id="ent_beta", kind="organization", canonical_name="BetaSoft"),
    ])
    exact = resolver.resolve("Acme Corp")
    assert exact is not None and exact.entity_id == "ent_acme" and exact.confidence == 1.0
    alias = resolver.resolve("Acme Corporation")
    assert alias is not None and alias.confidence == 0.95 and alias.provenance == "alias_table"
    fuzzy = resolver.resolve("Acme Corp (APAC)")
    assert fuzzy is not None and fuzzy.confidence == 0.7
    assert resolver.resolve("Unmatched Startup Ltd") is None  # abstain, never guess (§8.4)


def test_resolve_many_dedupes_entities():
    resolver = EntityResolver([CanonicalEntity(entity_id="ent_acme", kind="organization",
                                               canonical_name="Acme Corp", aliases=["Acme"])])
    matches = resolver.resolve_many(["Acme Corp", "Acme", "Acme Corp (EU)"])
    assert len(matches) == 1 and matches[0].entity_id == "ent_acme"
