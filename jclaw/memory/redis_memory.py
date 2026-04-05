"""Redis-backed session memory implementation."""

import json
from typing import Any

import redis.asyncio

from jclaw.memory.base import SessionMemory
from jclaw.types import Message


class RedisSessionMemory(SessionMemory):
    """Redis-backed session memory for production use.

    Stores messages and metadata in Redis with configurable TTL.
    Uses JSON serialization for message storage.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis session memory.

        Args:
            redis_url: Redis connection URL
        """
        self.redis: redis.asyncio.Redis | None = None
        self.redis_url = redis_url
        self._message_key_prefix = "session:messages:"
        self._metadata_key_prefix = "session:metadata:"
        self._summary_key_prefix = "session:summary:"

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await redis.asyncio.from_url(self.redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Get messages for a session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        key = f"{self._message_key_prefix}{session_id}"

        # Get messages from Redis list (most recent at index 0)
        messages_json = await self.redis.lrange(key, offset, offset + limit - 1)

        messages = []
        for msg_json in reversed(messages_json):
            try:
                msg_dict = json.loads(msg_json)
                messages.append(Message(**msg_dict))
            except (json.JSONDecodeError, ValueError):
                # Skip invalid messages
                pass

        return messages

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to the session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        key = f"{self._message_key_prefix}{session_id}"
        msg_json = message.model_dump_json()

        # Push to Redis list (LPUSH = most recent at left)
        await self.redis.lpush(key, msg_json)

        # Trim to keep only 100 most recent messages
        await self.redis.ltrim(key, 0, 99)

    async def get_summary(self, session_id: str) -> str | None:
        """Get summary of old messages."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        key = f"{self._summary_key_prefix}{session_id}"
        summary = await self.redis.get(key)

        return summary.decode() if summary else None

    async def set_metadata(self, session_id: str, key: str, value: Any) -> None:
        """Set a metadata value for the session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        hash_key = f"{self._metadata_key_prefix}{session_id}"

        # Serialize value to JSON
        value_json = json.dumps(value, default=str)

        # Store in Redis hash
        await self.redis.hset(hash_key, key, value_json)

    async def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a metadata value for the session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        hash_key = f"{self._metadata_key_prefix}{session_id}"
        value_json = await self.redis.hget(hash_key, key)

        if value_json is None:
            return default

        try:
            return json.loads(value_json)
        except json.JSONDecodeError:
            return default

    async def get_all_metadata(self, session_id: str) -> dict[str, Any]:
        """Get all metadata for a session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        hash_key = f"{self._metadata_key_prefix}{session_id}"
        data = await self.redis.hgetall(hash_key)

        result = {}
        for k, v_json in data.items():
            key_str = k.decode() if isinstance(k, bytes) else k
            try:
                value_str = v_json.decode() if isinstance(v_json, bytes) else v_json
                result[key_str] = json.loads(value_str)
            except (json.JSONDecodeError, AttributeError):
                pass

        return result

    async def expire(self, session_id: str, ttl_seconds: int) -> None:
        """Set expiration time for a session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Set TTL on all keys related to this session
        keys = [
            f"{self._message_key_prefix}{session_id}",
            f"{self._metadata_key_prefix}{session_id}",
            f"{self._summary_key_prefix}{session_id}",
        ]

        for key in keys:
            await self.redis.expire(key, ttl_seconds)

    async def get_active_sessions(self, agent_id: str | None = None) -> list[str]:
        """Get list of active session IDs."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        # Scan for all session keys
        pattern = f"{self._metadata_key_prefix}*"
        cursor = 0
        sessions = []

        async for key in self.redis.scan_iter(match=pattern):
            # Extract session ID from key
            session_id = key.decode().replace(self._metadata_key_prefix, "")

            if agent_id:
                # Filter by agent_id in metadata
                agent = await self.get_metadata(session_id, "active_agent_id")
                if agent == agent_id:
                    sessions.append(session_id)
            else:
                sessions.append(session_id)

        return sessions
