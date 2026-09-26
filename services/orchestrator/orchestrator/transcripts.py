"""Call/transcript intelligence (Phase 3, §24.4).

Deterministic, PII-minimizing extraction over meeting transcripts: action items,
objections, and next steps as structured output. Transcripts are UNTRUSTED
content (§11.2 / T-06): they are quarantined like news before any processing,
and consent gates processing per DPIA — no content is stored by default.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .pipeline import scrub_retrieved


class Consent(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"


class MeetingInsight(BaseModel):
    meeting_ref: str
    action_items: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    next_step: str | None = None
    quarantined: bool = False
    content_retained: bool = False  # DPIA default: insights kept, transcript content dropped


ACTION_PATTERNS = ("will send", "will share", "will follow up", "i'll send", "action item", "to-do")
OBJECTION_PATTERNS = ("too expensive", "budget is tight", "not sure", "competitor", "delay", "next quarter",
                      "need to check with", "concern")
NEXT_STEP_PATTERNS = ("next step", "follow-up meeting", "demo on", "follow up with")


def extract_insights(transcript_text: str, meeting_ref: str, consent: Consent) -> MeetingInsight:
    """Rule-based MVP extraction; the LLM-assisted extractor replaces patterns behind
    the same interface at deploy time. Consent gates everything; injection scrubbing
    applies because transcripts are untrusted input."""
    if consent is not Consent.GRANTED:
        return MeetingInsight(meeting_ref=meeting_ref)  # no processing without consent (DPIA §2)
    scrubbed = scrub_retrieved(_Doc(doc_id=meeting_ref, text=transcript_text))
    quarantined = scrubbed.text.startswith("[content quarantined")

    def sentences() -> list[str]:
        return [s.strip(" .") for s in scrubbed.text.replace("\n", ". ").split(".") if s.strip()]

    actions = [s for s in sentences() if any(p in s.lower() for p in ACTION_PATTERNS)]
    objections = [s for s in sentences() if any(p in s.lower() for p in OBJECTION_PATTERNS)]
    next_step = next((s for s in sentences() if any(p in s.lower() for p in NEXT_STEP_PATTERNS)), None)
    return MeetingInsight(meeting_ref=meeting_ref, action_items=actions[:10],
                          objections=objections[:10], next_step=next_step, quarantined=quarantined)


class _Doc:
    """Minimal RetrievedDoc-compatible shim (doc_id + text) for scrub_retrieved."""

    def __init__(self, doc_id: str, text: str) -> None:
        self.doc_id = doc_id
        self.text = text
