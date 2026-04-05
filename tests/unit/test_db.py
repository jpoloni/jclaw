"""Tests for database models and repositories."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from jclaw.db import Base
from jclaw.db.models import Session as SessionModel, MessageRecord, MemoryFact, HandoffLog
from jclaw.db.repositories import (
    SessionRepository,
    MessageRepository,
    MemoryFactRepository,
    HandoffLogRepository,
)
from jclaw.types import Message


@pytest.fixture
async def async_db():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite with asyncio support for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


class TestSessionRepository:
    """Tests for SessionRepository."""

    @pytest.mark.asyncio
    async def test_create_session(self, async_db: AsyncSession):
        """Test creating a session."""
        repo = SessionRepository(async_db)

        session = await repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        assert session.id is not None
        assert session.channel == "telegram"
        assert session.chat_id == "12345"

    @pytest.mark.asyncio
    async def test_get_session(self, async_db: AsyncSession):
        """Test getting a session."""
        repo = SessionRepository(async_db)

        # Create
        created = await repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        # Get
        retrieved = await repo.get(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.chat_id == "12345"

    @pytest.mark.asyncio
    async def test_get_by_channel_chat(self, async_db: AsyncSession):
        """Test getting session by channel and chat ID."""
        repo = SessionRepository(async_db)

        created = await repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        retrieved = await repo.get_by_channel_chat("telegram", "12345")
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_update_session(self, async_db: AsyncSession):
        """Test updating a session."""
        repo = SessionRepository(async_db)

        session = await repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        updated = await repo.update(session.id, active_agent_id="support")
        assert updated is not None
        assert updated.active_agent_id == "support"


class TestMessageRepository:
    """Tests for MessageRepository."""

    @pytest.mark.asyncio
    async def test_create_message(self, async_db: AsyncSession):
        """Test creating a message record."""
        # First create a session
        session_repo = SessionRepository(async_db)
        session = await session_repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        # Create message
        msg_repo = MessageRepository(async_db)
        message = Message(role="user", content="Hello")
        record = await msg_repo.create(
            session_id=session.id,
            message=message,
            agent_id="triage",
            tokens_used=10,
        )

        assert record.id is not None
        assert record.role == "user"
        assert record.content == "Hello"
        assert record.tokens_used == 10

    @pytest.mark.asyncio
    async def test_get_session_messages(self, async_db: AsyncSession):
        """Test getting all messages for a session."""
        # Setup
        session_repo = SessionRepository(async_db)
        session = await session_repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        msg_repo = MessageRepository(async_db)

        # Create multiple messages
        for i in range(3):
            msg = Message(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")
            await msg_repo.create(
                session_id=session.id,
                message=msg,
                agent_id="triage",
            )

        # Get all messages
        messages = await msg_repo.get_session_messages(session.id)
        assert len(messages) == 3

    @pytest.mark.asyncio
    async def test_count_session_messages(self, async_db: AsyncSession):
        """Test counting messages in a session."""
        session_repo = SessionRepository(async_db)
        session = await session_repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        msg_repo = MessageRepository(async_db)

        # Create 5 messages
        for i in range(5):
            msg = Message(role="user", content=f"Message {i}")
            await msg_repo.create(session_id=session.id, message=msg, agent_id="triage")

        count = await msg_repo.count_session_messages(session.id)
        assert count == 5


class TestMemoryFactRepository:
    """Tests for MemoryFactRepository."""

    @pytest.mark.asyncio
    async def test_create_or_update_fact(self, async_db: AsyncSession):
        """Test creating and updating a memory fact."""
        repo = MemoryFactRepository(async_db)

        # Create
        fact1 = await repo.create_or_update(
            user_id="user1",
            fact_key="name",
            fact_value="John Doe",
        )
        assert fact1.fact_value == "John Doe"

        # Update
        fact2 = await repo.create_or_update(
            user_id="user1",
            fact_key="name",
            fact_value="Jane Doe",
        )
        assert fact2.id == fact1.id
        assert fact2.fact_value == "Jane Doe"

    @pytest.mark.asyncio
    async def test_get_user_facts(self, async_db: AsyncSession):
        """Test getting all facts for a user."""
        repo = MemoryFactRepository(async_db)

        # Create facts
        await repo.create_or_update("user1", "name", "John")
        await repo.create_or_update("user1", "age", "30")
        await repo.create_or_update("user2", "name", "Jane")

        # Get user1 facts
        facts = await repo.get_user_facts("user1")
        assert len(facts) == 2


class TestHandoffLogRepository:
    """Tests for HandoffLogRepository."""

    @pytest.mark.asyncio
    async def test_create_handoff_log(self, async_db: AsyncSession):
        """Test creating a handoff log entry."""
        session_repo = SessionRepository(async_db)
        session = await session_repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        repo = HandoffLogRepository(async_db)
        log = await repo.create(
            session_id=session.id,
            source_agent_id="triage",
            target_agent_id="support",
            mode="transfer",
            reason="User needs support",
        )

        assert log.id is not None
        assert log.source_agent_id == "triage"
        assert log.target_agent_id == "support"
        assert log.success is True

    @pytest.mark.asyncio
    async def test_get_session_handoffs(self, async_db: AsyncSession):
        """Test getting all handoffs for a session."""
        session_repo = SessionRepository(async_db)
        session = await session_repo.create(
            channel="telegram",
            chat_id="12345",
            user_id="user1",
            active_agent_id="triage",
        )

        handoff_repo = HandoffLogRepository(async_db)

        # Create handoffs
        await handoff_repo.create(
            session_id=session.id,
            source_agent_id="triage",
            target_agent_id="support",
            mode="transfer",
            reason="Reason 1",
        )
        await handoff_repo.create(
            session_id=session.id,
            source_agent_id="support",
            target_agent_id="billing",
            mode="transfer",
            reason="Reason 2",
        )

        # Get all handoffs
        handoffs = await handoff_repo.get_session_handoffs(session.id)
        assert len(handoffs) == 2
