"""Event structures for observability and event-driven features."""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# Event type literals
EventType = Literal[
    "message.received",
    "message.sent",
    "llm.request",
    "llm.response",
    "llm.error",
    "llm.stream_start",
    "llm.stream_chunk",
    "llm.stream_end",
    "handoff.requested",
    "handoff.completed",
    "handoff.failed",
    "skill.executing",
    "skill.executed",
    "skill.error",
    "guardrail.triggered",
    "guardrail.blocked",
    "session.created",
    "session.expired",
    "session.resumed",
    "memory.compacted",
    "memory.fact_extracted",
    "memory.summary_generated",
    "prompt.rendered",
    "prompt.version_changed",
    "prompt.test_passed",
    "prompt.test_failed",
    "circuit_breaker.opened",
    "circuit_breaker.closed",
    "circuit_breaker.half_open",
]


class JClawEvent(BaseModel):
    """Base event structure for all jClaw events."""
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str | None = None
    agent_id: str | None = None
    trace_id: str | None = None
    user_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class MessageReceivedEvent(JClawEvent):
    """Event emitted when a message is received from a channel."""
    event_type: Literal["message.received"] = "message.received"
    channel: str = ""
    message_id: str = ""


class MessageSentEvent(JClawEvent):
    """Event emitted when a message is sent to a channel."""
    event_type: Literal["message.sent"] = "message.sent"
    channel: str = ""
    message_id: str = ""


class LLMRequestEvent(JClawEvent):
    """Event emitted when calling an LLM."""
    event_type: Literal["llm.request"] = "llm.request"
    model: str = ""
    provider: str = ""
    input_tokens: int | None = None


class LLMResponseEvent(JClawEvent):
    """Event emitted when receiving an LLM response."""
    event_type: Literal["llm.response"] = "llm.response"
    model: str = ""
    provider: str = ""
    output_tokens: int | None = None
    latency_ms: float = 0.0
    stop_reason: str = ""


class LLMErrorEvent(JClawEvent):
    """Event emitted on LLM error."""
    event_type: Literal["llm.error"] = "llm.error"
    model: str = ""
    provider: str = ""
    error_message: str = ""
    error_type: str = ""


class HandoffRequestedEvent(JClawEvent):
    """Event emitted when a handoff is requested."""
    event_type: Literal["handoff.requested"] = "handoff.requested"
    source_agent_id: str = ""
    target_agent_id: str = ""
    mode: str = "transfer"


class HandoffCompletedEvent(JClawEvent):
    """Event emitted when a handoff completes."""
    event_type: Literal["handoff.completed"] = "handoff.completed"
    source_agent_id: str = ""
    target_agent_id: str = ""
    mode: str = "transfer"


class SkillExecutedEvent(JClawEvent):
    """Event emitted when a skill is executed."""
    event_type: Literal["skill.executed"] = "skill.executed"
    skill_id: str = ""
    tool_name: str = ""
    latency_ms: float = 0.0
    is_error: bool = False


class GuardrailTriggeredEvent(JClawEvent):
    """Event emitted when a guardrail is triggered."""
    event_type: Literal["guardrail.triggered"] = "guardrail.triggered"
    guardrail_id: str = ""
    action: str = "warn"  # warn, block


class SessionCreatedEvent(JClawEvent):
    """Event emitted when a session is created."""
    event_type: Literal["session.created"] = "session.created"
    channel: str = ""


class PromptRenderedEvent(JClawEvent):
    """Event emitted when a prompt is rendered."""
    event_type: Literal["prompt.rendered"] = "prompt.rendered"
    template_id: str = ""
    version: str = ""
    token_count: int = 0
