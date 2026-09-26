"""News-source ingestion adapters (Phase 2 'expanded market-intelligence sources').

Adapters per §8.4: licensed feeds, approved web sources, configured subscriptions.
Rights are enforced AT INGESTION: items from sources without AI-summarization
rights are excluded, and everything carries rights metadata. Syndicated stories
are deduplicated by SimHash clustering with a canonical member.
External content remains untrusted input (T-06): nothing here executes or
instructs — text is data only.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from enum import Enum

from pydantic import BaseModel


class Rights(str, Enum):
    FULL = "full"                      # licensed: retrieval + summarization + retention
    RETRIEVAL_ONLY = "retrieval_only"  # link/quote only; excluded from AI summarization
    DENIED = "denied"                  # not licensed for this deployment


class SourcePolicy(BaseModel):
    source_id: str
    license: Rights = Rights.RETRIEVAL_ONLY
    retention_days: int = 90
    geography_allow: bool = True       # geography rules (§8.4 controls)


class RawNewsItem(BaseModel):
    source_id: str
    external_id: str
    title: str
    published_at: str
    url: str
    body: str


class IngestedNews(BaseModel):
    news_id: str
    source_id: str
    external_id: str
    title: str
    published_at: str
    url: str
    rights: Rights
    retained_until: str
    simhash: str
    cluster_id: str


class NewsAdapter:
    """Adapter interface — one subclass per source family (RSS, licensed API, webhook)."""

    def fetch(self) -> list[RawNewsItem]:
        raise NotImplementedError


class RssAdapter(NewsAdapter):
    """RSS/Atom feed adapter (stdlib parsing; feed content is untrusted data)."""

    def __init__(self, source_id: str, xml_text: str) -> None:
        self.source_id = source_id
        self.xml_text = xml_text

    def fetch(self) -> list[RawNewsItem]:
        root = ET.fromstring(self.xml_text)
        items: list[RawNewsItem] = []
        for item in root.iter():
            tag = item.tag.rsplit("}", 1)[-1]
            if tag not in ("item", "entry"):
                continue
            fields: dict[str, str] = {}
            for child in item:
                ctag = child.tag.rsplit("}", 1)[-1]
                if ctag in ("title", "pubDate", "published", "updated", "link", "guid", "id", "description", "summary", "content"):
                    if ctag == "link" and child.get("href"):
                        fields.setdefault("link", str(child.get("href")))
                    elif ctag in ("description", "summary", "content"):
                        fields["body"] = (fields.get("body") or "") + " " + (child.text or "")
                    else:
                        fields[ctag] = child.text or ""
            url = fields.get("link") or fields.get("guid") or fields.get("id") or ""
            items.append(RawNewsItem(
                source_id=self.source_id,
                external_id=fields.get("guid") or fields.get("id") or url,
                title=fields.get("title", ""),
                published_at=fields.get("pubDate") or fields.get("published") or fields.get("updated") or "",
                url=url, body=fields.get("body", "").strip()))
        return items


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def simhash(text: str, bits: int = 64) -> str:
    """Deterministic SimHash for near-duplicate clustering of syndicated stories (§8.4)."""
    v = [0] * bits
    for tok in _tokens(text):
        h = int.from_bytes(hashlib.sha256(tok.encode()).digest()[:8], "big")
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= 1 << i
    return f"{fingerprint:016x}"


def hamming(a_hex: str, b_hex: str) -> int:
    return bin(int(a_hex, 16) ^ int(b_hex, 16)).count("1")


def cluster_id_for(item: RawNewsItem, existing: list[IngestedNews], distance: int = 12) -> str:
    """Joins the nearest existing cluster within Hamming distance, else starts one."""
    h = simhash(f"{item.title} {item.body}")
    for e in existing:
        if hamming(h, e.simhash) <= distance:
            return e.cluster_id
    return f"cluster_{h[:12]}"


def ingest(items: list[RawNewsItem], policies: dict[str, SourcePolicy],
           existing: list[IngestedNews] | None = None) -> tuple[list[IngestedNews], list[str]]:
    """Rights-enforcing ingestion: returns (ingested, excluded_with_reason)."""
    existing = existing or []
    excluded: list[str] = []
    out: list[IngestedNews] = []
    for item in items:
        policy = policies.get(item.source_id)
        if policy is None or policy.license is Rights.DENIED or not policy.geography_allow:
            excluded.append(f"{item.source_id}/{item.external_id}:unlicensed_or_denied")
            continue
        if policy.license is not Rights.RETRIEVAL_ONLY and policy.license is not Rights.FULL:
            excluded.append(f"{item.source_id}/{item.external_id}:unknown_rights")
            continue
        if policy.license is Rights.RETRIEVAL_ONLY:
            excluded.append(f"{item.source_id}/{item.external_id}:retrieval_only_no_summarization")
            # Link/quote metadata may still be stored without body; simplified here to exclusion.
            continue
        h = simhash(f"{item.title} {item.body}")
        out.append(IngestedNews(
            news_id=f"news_{h[:12]}{len(out)}",
            source_id=item.source_id, external_id=item.external_id,
            title=item.title, published_at=item.published_at, url=item.url,
            rights=policy.license, retained_until=f"+{policy.retention_days}d",
            simhash=h, cluster_id=cluster_id_for(item, existing + out)))
    return out, excluded
