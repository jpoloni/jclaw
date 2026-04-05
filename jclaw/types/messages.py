"""Message and communication data structures for jClaw."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types for messages."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"


class MediaType(str, Enum):
    """Media attachment types."""
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    VIDEO = "video"


class MediaAttachment(BaseModel):
    """Media file attachment."""
    url: str
    type: MediaType
    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None


class Button(BaseModel):
    """Interactive button for rich responses."""
    label: str
    action: Literal["postback", "url", "call"]
    value: str  # payload/URL/phone number


class Message(BaseModel):
    """A single message in the conversation history."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: str | None = None  # For system/tool messages
    tool_call_id: str | None = None  # If this message is a tool result
    tool_calls: list["ToolCall"] | None = None  # If assistant used tools
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """A single tool/function call made by the LLM."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    input: dict[str, Any]


class ToolResult(BaseModel):
    """Result of executing a tool."""
    tool_call_id: str
    output: str | dict[str, Any]
    is_error: bool = False


class ToolDefinition(BaseModel):
    """Definition of a tool available to an agent."""
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema


class StreamChunk(BaseModel):
    """Chunk of a streamed LLM response."""
    delta: str = ""
    chunk_type: Literal["text", "tool_call", "stop"]
    tool_call: ToolCall | None = None
    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence"] | None = None


class InboundMessage(BaseModel):
    """A message received from a channel (user input)."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    chat_id: str
    user_id: str
    channel: str  # "telegram", "whatsapp", "rest", "playground"
    content_type: ContentType = ContentType.TEXT
    text: str | None = None
    media_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutboundMessage(BaseModel):
    """A message to send back to a channel (bot response)."""
    text: str | None = None
    media: list[MediaAttachment] = Field(default_factory=list)
    buttons: list[Button] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
