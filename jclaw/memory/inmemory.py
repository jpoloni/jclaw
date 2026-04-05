"""In-memory session memory implementation."""

import asyncio
from collections import defaultdict
from typing import Any
from datetime import datetime, timedelta, timezone

from jclaw.memory.base import SessionMemory
from jclaw.types import Message


class InMemorySessionMemory(SessionMemory):
    """In-memory session memory for development and testing.

    Stores messages and metadata in RAM using dictionaries. TTL is managed
    with asyncio tasks.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._messages: dict[str, list[Message]] = defaultdict(list)
        self._metadata: dict[str, dict[str, Any]] = defaultdict(dict)
        self._summaries: dict[str, str] = {}
        self._expiry_tasks: dict[str, asyncio.Task] = {}
        self._active_sessions: set[str] = set()

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Get messages for a session."""
        messages = self._messages.get(session_id, [])
        # Return in reverse order (most recent first)
        return list(reversed(messages))[offset : offset + limit]

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to the session."""
        self._messages[session_id].append(message)
        self._active_sessions.add(session_id)

        # Apply sliding window compaction if needed
        await self._apply_compaction(session_id)

    async def get_summary(self, session_id: str) -> str | None:
        """Get summary of old messages."""
        return self._summaries.get(session_id)

    async def set_metadata(self, session_id: str, key: str, value: Any) -> None:
        """Set a metadata value for the session."""
        self._metadata[session_id][key] = value

    async def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a metadata value for the session."""
        return self._metadata.get(session_id, {}).get(key, default)

    async def get_all_metadata(self, session_id: str) -> dict[str, Any]:
        """Get all metadata for a session."""
        return self._metadata.get(session_id, {}).copy()

    async def expire(self, session_id: str, ttl_seconds: int) -> None:
        """Set expiration time for a session."""
        # Cancel existing expiry task if any
        if session_id in self._expiry_tasks:
            self._expiry_tasks[session_id].cancel()

        # Create new expiry task
        task = asyncio.create_task(self._expire_after(session_id, ttl_seconds))
        self._expiry_tasks[session_id] = task

    async def get_active_sessions(self, agent_id: str | None = None) -> list[str]:
        """Get list of active session IDs."""
        sessions = list(self._active_sessions)
        if agent_id:
            # Filter by agent_id in metadata
            filtered = []
            for sid in sessions:
                agent = await self.get_metadata(sid, "active_agent_id")
                if agent == agent_id:
                    filtered.append(sid)
            return filtered
        return sessions

    async def clear(self) -> None:
        """Clear all data (useful for testing)."""
        self._messages.clear()
        self._metadata.clear()
        self._summaries.clear()
        self._active_sessions.clear()
        for task in self._expiry_tasks.values():
            task.cancel()
        self._expiry_tasks.clear()

    async def _apply_compaction(self, session_id: str) -> None:
        """Apply sliding window compaction to messages.

        Keeps the last 100 messages, discards older ones.
        """
        messages = self._messages[session_id]
        max_messages = 100

        if len(messages) > max_messages:
            # Keep only the last max_messages
            self._messages[session_id] = messages[-max_messages:]

    async def _expire_after(self, session_id: str, ttl_seconds: int) -> None:
        """Expire a session after TTL."""
        try:
            await asyncio.sleep(ttl_seconds)
            # Remove session data
            self._messages.pop(session_id, None)
            self._metadata.pop(session_id, None)
            self._summaries.pop(session_id, None)
            self._active_sessions.discard(session_id)
            self._expiry_tasks.pop(session_id, None)
        except asyncio.CancelledError:
            pass
