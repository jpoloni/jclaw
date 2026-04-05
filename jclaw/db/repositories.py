"""Database repositories for CRUD operations."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from jclaw.db.models import (
    HandoffLog,
    MemoryFact,
    MessageRecord,
    PromptAnalytics,
    PromptTemplate,
    Session,
)
from jclaw.types import Message


class SessionRepository:
    """Repository for managing sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        channel: str,
        chat_id: str,
        user_id: str,
        active_agent_id: str,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid4()),
            channel=channel,
            chat_id=chat_id,
            user_id=user_id,
            active_agent_id=active_agent_id,
            extras=metadata or {},
            expires_at=expires_at,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get(self, session_id: str) -> Session | None:
        """Get session by ID."""
        stmt = select(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_channel_chat(self, channel: str, chat_id: str) -> Session | None:
        """Get session by channel and chat ID."""
        stmt = select(Session).where(
            and_(Session.channel == channel, Session.chat_id == chat_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, session_id: str, **kwargs) -> Session | None:
        """Update session fields."""
        session = await self.get(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        return session

    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        session = await self.get(session_id)
        if session:
            await self.db.delete(session)
            await self.db.flush()
            return True
        return False


class MessageRepository:
    """Repository for managing messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str,
        message: Message,
        agent_id: str,
        tokens_used: int | None = None,
        model_used: str | None = None,
    ) -> MessageRecord:
        """Create a new message record."""
        record = MessageRecord(
            id=str(uuid4()),
            session_id=session_id,
            role=message.role,
            content=message.content,
            name=message.name,
            tool_call_id=message.tool_call_id,
            tool_calls=([tc.model_dump() for tc in message.tool_calls] if message.tool_calls else None),
            agent_id=agent_id,
            tokens_used=tokens_used,
            model_used=model_used,
            metadata=message.metadata,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get(self, message_id: str) -> MessageRecord | None:
        """Get message by ID."""
        stmt = select(MessageRecord).where(MessageRecord.id == message_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MessageRecord]:
        """Get all messages for a session."""
        stmt = (
            select(MessageRecord)
            .where(MessageRecord.session_id == session_id)
            .order_by(MessageRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_session_messages(self, session_id: str) -> int:
        """Count messages in a session."""
        stmt = select(func.count()).select_from(MessageRecord).where(MessageRecord.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0


class MemoryFactRepository:
    """Repository for managing memory facts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update(
        self,
        user_id: str,
        fact_key: str,
        fact_value: str,
        source_session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryFact:
        """Create or update a memory fact."""
        stmt = select(MemoryFact).where(
            and_(MemoryFact.user_id == user_id, MemoryFact.fact_key == fact_key)
        )
        result = await self.db.execute(stmt)
        fact = result.scalar_one_or_none()

        if fact:
            fact.fact_value = fact_value
            fact.source_session_id = source_session_id
            fact.metadata = metadata or {}
            fact.updated_at = datetime.now(timezone.utc)
        else:
            fact = MemoryFact(
                id=str(uuid4()),
                user_id=user_id,
                fact_key=fact_key,
                fact_value=fact_value,
                source_session_id=source_session_id,
                metadata=metadata or {},
            )
            self.db.add(fact)

        await self.db.flush()
        return fact

    async def get(self, user_id: str, fact_key: str) -> MemoryFact | None:
        """Get a memory fact."""
        stmt = select(MemoryFact).where(
            and_(MemoryFact.user_id == user_id, MemoryFact.fact_key == fact_key)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_facts(self, user_id: str) -> list[MemoryFact]:
        """Get all facts for a user."""
        stmt = select(MemoryFact).where(MemoryFact.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete(self, user_id: str, fact_key: str) -> bool:
        """Delete a memory fact."""
        fact = await self.get(user_id, fact_key)
        if fact:
            await self.db.delete(fact)
            await self.db.flush()
            return True
        return False


class HandoffLogRepository:
    """Repository for managing handoff logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str,
        source_agent_id: str,
        target_agent_id: str,
        mode: str,
        reason: str,
        context_payload: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> HandoffLog:
        """Create a handoff log entry."""
        log = HandoffLog(
            id=str(uuid4()),
            session_id=session_id,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            mode=mode,
            reason=reason,
            context_payload=context_payload or {},
            success=success,
            error_message=error_message,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_session_handoffs(self, session_id: str) -> list[HandoffLog]:
        """Get all handoffs for a session."""
        stmt = select(HandoffLog).where(HandoffLog.session_id == session_id).order_by(HandoffLog.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()


class PromptTemplateRepository:
    """Repository for managing prompt templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        template_id: str,
        name: str,
        version: str,
        content: str,
        description: str = "",
        variables: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        parent_id: str | None = None,
    ) -> PromptTemplate:
        """Create a prompt template."""
        template = PromptTemplate(
            id=str(uuid4()),
            template_id=template_id,
            name=name,
            version=version,
            content=content,
            description=description,
            variables=variables or [],
            metadata=metadata or {},
            tags=tags or [],
            parent_id=parent_id,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def get_latest(self, template_id: str) -> PromptTemplate | None:
        """Get latest version of a template."""
        stmt = (
            select(PromptTemplate)
            .where(PromptTemplate.template_id == template_id)
            .order_by(PromptTemplate.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version(self, template_id: str, version: str) -> PromptTemplate | None:
        """Get specific version of a template."""
        stmt = select(PromptTemplate).where(
            and_(PromptTemplate.template_id == template_id, PromptTemplate.version == version)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(self, template_id: str) -> list[PromptTemplate]:
        """List all versions of a template."""
        stmt = (
            select(PromptTemplate)
            .where(PromptTemplate.template_id == template_id)
            .order_by(PromptTemplate.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


class PromptAnalyticsRepository:
    """Repository for managing prompt analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        template_id: str,
        agent_id: str,
        version: str,
        token_count: int,
        render_time_ms: float,
        variables_resolved: int = 0,
        variables_failed: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> PromptAnalytics:
        """Record prompt analytics."""
        analytics = PromptAnalytics(
            id=str(uuid4()),
            template_id=template_id,
            agent_id=agent_id,
            version=version,
            token_count=token_count,
            render_time_ms=render_time_ms,
            variables_resolved=variables_resolved,
            variables_failed=variables_failed,
            metadata=metadata or {},
        )
        self.db.add(analytics)
        await self.db.flush()
        return analytics


# Import func from sqlalchemy for aggregation
from sqlalchemy import func
