"""Playbook selection engine (Phase 3, §24.4).

Loads the governed catalog (data/playbooks/catalog.yaml) and deterministically
matches deal attributes (signals + stage) to plays. A play is a RECOMMENDATION
with provenance — never an executed action (§8.7, §33 posture).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "playbooks" / "catalog.yaml"

VALID_STAGES = frozenset({"early", "middle", "late", "closed_won", "closed_lost"})


class PlayMatch(BaseModel):
    play_id: str
    name: str
    methodology: str
    version: int
    matched_signals: list[str]
    recommendation: str
    evidence_basis: str


class PlaybookCatalog(BaseModel):
    catalog_version: int
    plays: list[dict] = Field(default_factory=list)


def load_catalog(path: Path = CATALOG_PATH) -> PlaybookCatalog:
    doc = yaml.safe_load(path.read_text())
    for play in doc.get("plays", []):
        for stage in play["match"].get("stages", []):
            if stage not in VALID_STAGES:
                raise ValueError(f"play {play['play_id']}: unknown stage {stage!r}")
    return PlaybookCatalog(catalog_version=doc["catalog_version"], plays=doc["plays"])


def select_plays(catalog: PlaybookCatalog, signals: list[str], stage: str,
                 max_plays: int = 3) -> list[PlayMatch]:
    out: list[PlayMatch] = []
    for play in catalog.plays:
        m = play["match"]
        matched = sorted(set(signals) & set(m.get("signals", [])))
        stage_ok = stage in m.get("stages", [])
        if stage_ok and len(matched) >= int(m.get("min_signals", 1)):
            out.append(PlayMatch(
                play_id=play["play_id"], name=play["name"], methodology=play["methodology"],
                version=play["version"], matched_signals=matched,
                recommendation=play["recommendation"], evidence_basis=play["evidence_basis"]))
    out.sort(key=lambda p: (-len(p.matched_signals), p.play_id))
    return out[:max_plays]
