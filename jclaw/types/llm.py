"""LLM-related data structures."""

from typing import Any, Literal

from pydantic import BaseModel


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None = None


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    content: str | None = None
    tool_calls: list[Any] = []  # list[ToolCall] but avoiding circular imports
    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence"]
    model: str
    usage: TokenUsage
    latency_ms: float
