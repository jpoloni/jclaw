"""Tests for session memory implementations."""

import asyncio
import pytest
from jclaw.memory import InMemorySessionMemory, RedisSessionMemory
from jclaw.types import Message


class TestInMemorySessionMemory:
    """Tests for InMemorySessionMemory."""

    @pytest.fixture
    async def memory(self):
        """Create fresh memory for each test."""
        mem = InMemorySessionMemory()
        yield mem
        await mem.clear()

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, memory):
        """Test adding and retrieving messages."""
        session_id = "session_1"

        # Add messages
        msg1 = Message(role="user", content="Hello")
        msg2 = Message(role="assistant", content="Hi there")

        await memory.add_message(session_id, msg1)
        await memory.add_message(session_id, msg2)

        # Get messages (most recent first)
        messages = await memory.get_messages(session_id)
        assert len(messages) == 2
        assert messages[0].content == "Hi there"  # Most recent first
        assert messages[1].content == "Hello"

    @pytest.mark.asyncio
    async def test_message_limit(self, memory):
        """Test limit parameter in get_messages."""
        session_id = "session_1"

        # Add 5 messages
        for i in range(5):
            msg = Message(role="user", content=f"Message {i}")
            await memory.add_message(session_id, msg)

        # Get only 2 most recent
        messages = await memory.get_messages(session_id, limit=2)
        assert len(messages) == 2
        assert messages[0].content == "Message 4"
        assert messages[1].content == "Message 3"

    @pytest.mark.asyncio
    async def test_metadata(self, memory):
        """Test setting and getting metadata."""
        session_id = "session_1"

        # Set metadata
        await memory.set_metadata(session_id, "user_id", "user123")
        await memory.set_metadata(session_id, "active_agent", "triage")

        # Get individual metadata
        user_id = await memory.get_metadata(session_id, "user_id")
        assert user_id == "user123"

        # Get all metadata
        all_meta = await memory.get_all_metadata(session_id)
        assert all_meta["user_id"] == "user123"
        assert all_meta["active_agent"] == "triage"

    @pytest.mark.asyncio
    async def test_metadata_default(self, memory):
        """Test metadata default value."""
        session_id = "session_1"

        value = await memory.get_metadata(session_id, "nonexistent", default="default_value")
        assert value == "default_value"

    @pytest.mark.asyncio
    async def test_get_summary(self, memory):
        """Test getting summary (initially None)."""
        session_id = "session_1"

        summary = await memory.get_summary(session_id)
        assert summary is None

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, memory):
        """Test getting active sessions."""
        # Add messages to multiple sessions
        await memory.add_message("session_1", Message(role="user", content="Test"))
        await memory.add_message("session_2", Message(role="user", content="Test"))
        await memory.add_message("session_3", Message(role="user", content="Test"))

        sessions = await memory.get_active_sessions()
        assert len(sessions) == 3
        assert "session_1" in sessions
        assert "session_2" in sessions
        assert "session_3" in sessions

    @pytest.mark.asyncio
    async def test_get_active_sessions_by_agent(self, memory):
        """Test filtering active sessions by agent ID."""
        # Create sessions with different agents
        await memory.add_message("session_1", Message(role="user", content="Test"))
        await memory.set_metadata("session_1", "active_agent_id", "triage")

        await memory.add_message("session_2", Message(role="user", content="Test"))
        await memory.set_metadata("session_2", "active_agent_id", "support")

        await memory.add_message("session_3", Message(role="user", content="Test"))
        await memory.set_metadata("session_3", "active_agent_id", "triage")

        # Get only triage sessions
        triage_sessions = await memory.get_active_sessions(agent_id="triage")
        assert len(triage_sessions) == 2
        assert "session_1" in triage_sessions
        assert "session_3" in triage_sessions

    @pytest.mark.asyncio
    async def test_expire(self, memory):
        """Test session expiration."""
        session_id = "session_1"

        # Add message and metadata
        await memory.add_message(session_id, Message(role="user", content="Test"))
        await memory.set_metadata(session_id, "key", "value")

        # Set very short expiry
        await memory.expire(session_id, ttl_seconds=0.1)

        # Check it exists
        sessions = await memory.get_active_sessions()
        assert session_id in sessions

        # Wait for expiry
        await asyncio.sleep(0.2)

        # Session should be expired
        sessions = await memory.get_active_sessions()
        assert session_id not in sessions

    @pytest.mark.asyncio
    async def test_compaction(self, memory):
        """Test that messages are compacted (keep only 100)."""
        session_id = "session_1"

        # Add 150 messages
        for i in range(150):
            msg = Message(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}")
            await memory.add_message(session_id, msg)

        # Get all messages - should be limited to 100
        messages = await memory.get_messages(session_id, limit=1000)
        assert len(messages) == 100


class TestRedisSessionMemory:
    """Tests for RedisSessionMemory (requires Redis)."""

    @pytest.fixture
    async def memory(self):
        """Create fresh Redis memory for each test."""
        mem = RedisSessionMemory("redis://localhost:6379/0")
        try:
            await mem.connect()
            yield mem
        finally:
            # Cleanup: remove all test data
            if mem.redis:
                # Clear test keys
                cursor = 0
                async for key in mem.redis.scan_iter(match="session:*"):
                    await mem.redis.delete(key)
                await mem.disconnect()

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, memory):
        """Test adding and retrieving messages in Redis."""
        session_id = "redis_session_1"

        # Add messages
        msg1 = Message(role="user", content="Hello")
        msg2 = Message(role="assistant", content="Hi")

        await memory.add_message(session_id, msg1)
        await memory.add_message(session_id, msg2)

        # Get messages
        messages = await memory.get_messages(session_id)
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_redis_connection_required(self):
        """Test that operations fail without connection."""
        memory = RedisSessionMemory()

        with pytest.raises(RuntimeError, match="Redis not connected"):
            await memory.add_message("session", Message(role="user", content="Test"))
