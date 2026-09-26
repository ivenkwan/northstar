"""ADR repository review automation (Phase 3: quarterly architecture/ADR review).

Checks the ADR set for structural consistency so the quarterly board review
starts from a verified inventory:
  * every docs/adr/ADR-*.md file appears in the index table
  * statuses are from the allowed vocabulary
  * numbering is dense and monotonic from 021 (documented gap for 001-020)
  * superseded ADRs point at their successor
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parents[1] / "docs" / "adr"
INDEX = ADR_DIR / "README.md"
VALID_STATUS = {"Proposed", "Accepted", "Superseded"}
FIRST_NUMBER = 21  # 001-020 lived in the superseded pre-repo documents


def check() -> list[str]:
    problems: list[str] = []
    files = sorted(ADR_DIR.glob("ADR-*.md"))
    index_text = INDEX.read_text()

    numbers: list[int] = []
    for f in files:
        m = re.match(r"ADR-(\d+)-", f.name)
        if m is None:
            problems.append(f"{f.name}: filename does not match ADR-<number>-slug.md")
            continue
        numbers.append(int(m.group(1)))
        body = f.read_text()
        status_match = re.search(r"\*\*Status:?\*\*\s*\|?\s*(Proposed|Accepted|Superseded)", body)
        if status_match is None:
            problems.append(f"{f.name}: missing or invalid Status line")
        link = f"[ADR-{m.group(1)}]({f.name})"
        if link not in index_text:
            problems.append(f"{f.name}: not linked in docs/adr/README.md index")
        if "Superseded by" in body and "ADR-" not in body.split("Superseded by", 1)[1][:12]:
            problems.append(f"{f.name}: Superseded without successor reference")

    numbers.sort()
    if numbers and numbers[0] != FIRST_NUMBER:
        problems.append(f"numbering starts at {numbers[0]:03d}; expected {FIRST_NUMBER:03d}")
    for prev, nxt in zip(numbers, numbers[1:], strict=False):
        if nxt != prev + 1:
            problems.append(f"numbering gap between ADR-{prev:03d} and ADR-{nxt:03d}")
    return problems


if __name__ == "__main__":
    issues = check()
    for i in issues:
        print(f"ADR-REVIEW: {i}")
    sys.exit(1 if issues else 0)
