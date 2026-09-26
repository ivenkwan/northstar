"""Repo-hygiene goldens: ADR inventory consistency (quarterly review automation)."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_adr_inventory_is_consistent():
    """Every ADR indexed, valid status, dense numbering from 021 — the quarterly
    board review starts from a verified inventory."""
    result = subprocess.run(
        [sys.executable, str(REPO / "tools" / "adr_review.py")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"adr_review findings:\n{result.stdout}"


def test_quarterly_review_checklist_exists():
    checklist = REPO / "docs" / "adr" / "quarterly-review.md"
    assert checklist.exists()
    for section in ("verification matrix", "decision items", "sign-off"):
        assert section in checklist.read_text().lower()
