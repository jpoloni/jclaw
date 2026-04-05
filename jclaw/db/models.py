"""SQLAlchemy ORM models for jClaw."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Session(Base):
    """Represents a user session."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    channel: Mapped[str] = mapped_column(String(50))
    chat_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(255))
    active_agent_id: Mapped[str] = mapped_column(String(100))
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("channel", "chat_id", name="uq_channel_chat"),
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, channel={self.channel}, user_id={self.user_id})>"


class MessageRecord(Base):
    """Represents a single message in a session."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False))
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_calls: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_results: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    agent_id: Mapped[str] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<MessageRecord(id={self.id}, role={self.role}, agent_id={self.agent_id})>"


class MemoryFact(Base):
    """Represents a long-term memory fact about a user."""

    __tablename__ = "memory_facts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(255))
    fact_key: Mapped[str] = mapped_column(String(255))
    fact_value: Mapped[str] = mapped_column(Text)
    # Note: pgvector support would add: embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)
    source_session_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "fact_key", name="uq_user_fact_key"),
    )

    def __repr__(self) -> str:
        return f"<MemoryFact(id={self.id}, user_id={self.user_id}, fact_key={self.fact_key})>"


class HandoffLog(Base):
    """Log of agent handoffs."""

    __tablename__ = "handoff_log"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False))
    source_agent_id: Mapped[str] = mapped_column(String(100))
    target_agent_id: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(20))  # transfer, delegate, escalate
    reason: Mapped[str] = mapped_column(Text)
    context_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<HandoffLog(id={self.id}, {self.source_agent_id} → {self.target_agent_id})>"


class PromptTemplate(Base):
    """Stores prompt templates with versioning."""

    __tablename__ = "prompt_templates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    template_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(50), default="jinja2")
    variables: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    parent_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_template_version"),
    )

    def __repr__(self) -> str:
        return f"<PromptTemplate(id={self.template_id}, v={self.version})>"


class PromptAnalytics(Base):
    """Analytics for prompt rendering and testing."""

    __tablename__ = "prompt_analytics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    template_id: Mapped[str] = mapped_column(String(255))
    agent_id: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    token_count: Mapped[int] = mapped_column(default=0)
    render_time_ms: Mapped[float] = mapped_column(default=0.0)
    variables_resolved: Mapped[int] = mapped_column(default=0)
    variables_failed: Mapped[int] = mapped_column(default=0)
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<PromptAnalytics(template={self.template_id}, tokens={self.token_count})>"
