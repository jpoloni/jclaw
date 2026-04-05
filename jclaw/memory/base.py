"""Abstract base class for session memory."""

from abc import ABC, abstractmethod
from typing import Any

from jclaw.types import Message


class SessionMemory(ABC):
    """Abstract base class for session memory implementations.

    Provides multi-tier memory: short-term (current turn), session (24h),
    and long-term (permanent) via inheritance.
    """

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Get messages for a session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of Message objects, most recent first
        """
        pass

    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to the session.

        Args:
            session_id: Session identifier
            message: Message to add
        """
        pass

    @abstractmethod
    async def get_summary(self, session_id: str) -> str | None:
        """Get summary of old messages (if implemented).

        Args:
            session_id: Session identifier

        Returns:
            Summary text or None if not available
        """
        pass

    @abstractmethod
    async def set_metadata(self, session_id: str, key: str, value: Any) -> None:
        """Set a metadata value for the session.

        Args:
            session_id: Session identifier
            key: Metadata key
            value: Metadata value
        """
        pass

    @abstractmethod
    async def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a metadata value for the session.

        Args:
            session_id: Session identifier
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        pass

    @abstractmethod
    async def get_all_metadata(self, session_id: str) -> dict[str, Any]:
        """Get all metadata for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of all metadata
        """
        pass

    @abstractmethod
    async def expire(self, session_id: str, ttl_seconds: int) -> None:
        """Set expiration time for a session.

        Args:
            session_id: Session identifier
            ttl_seconds: Time to live in seconds
        """
        pass

    @abstractmethod
    async def get_active_sessions(self, agent_id: str | None = None) -> list[str]:
        """Get list of active session IDs.

        Args:
            agent_id: Optional filter by agent ID

        Returns:
            List of session IDs
        """
        pass
