"""Provider wire models (ADR-022): OpenAI Chat Completions and Anthropic Messages.

Deliberately SEPARATE models — never one merged optional-field interface
(PRD §17.6). Conformance fixtures validate against these shapes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ------------------------------------------------------------------ OpenAI (GW-01/03)


class OpenAIChoiceMessage(BaseModel):
    role: str
    content: str | None = None


class OpenAIChoice(BaseModel):
    index: int
    message: OpenAIChoiceMessage
    finish_reason: str | None = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: list[OpenAIChoice] = Field(min_length=1)
    usage: OpenAIUsage


# ------------------------------------------------------------------ Anthropic (GW-08)


class AnthropicTextBlock(BaseModel):
    type: str = "text"
    text: str


class AnthropicContentBlock(BaseModel):
    """Content blocks preserved end-to-end — no reinterpretation as OpenAI chunks."""

    type: str  # text | tool_use | tool_result
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict | None = None


class AnthropicUsage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnthropicMessage(BaseModel):
    id: str
    type: str = "message"
    role: str = "assistant"
    content: list[AnthropicContentBlock] = Field(min_length=1)
    stop_reason: str | None = None  # end_turn | tool_use | max_tokens | stop_sequence
    usage: AnthropicUsage


class AnthropicStreamEvent(BaseModel):
    type: str  # message_start | content_block_start | content_block_delta | content_block_stop | message_delta | message_stop


TERMINATOR_OPENAI = "[DONE]"
TERMINATOR_ANTHROPIC = "message_stop"


def parse_sse_events(raw: str) -> list[tuple[str, str]]:
    """Parses 'event:'/'data:' pairs from an SSE fixture stream."""
    events: list[tuple[str, str]] = []
    current_event = None
    for line in raw.splitlines():
        if line.startswith("event:"):
            current_event = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data = line.removeprefix("data:").strip()
            events.append((current_event or "message", data))
    return events
