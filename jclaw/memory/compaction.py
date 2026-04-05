"""Memory compaction strategies (future implementation)."""

from abc import ABC, abstractmethod
from typing import Any

from jclaw.types import Message


class CompactionStrategy(ABC):
    """Abstract base class for memory compaction strategies."""

    @abstractmethod
    async def compact(
        self,
        messages: list[Message],
        max_tokens: int,
    ) -> tuple[list[Message], str | None]:
        """Compact messages to fit within token budget.

        Args:
            messages: Messages to compact
            max_tokens: Maximum tokens allowed

        Returns:
            Tuple of (compacted_messages, summary_if_any)
        """
        pass


class SlidingWindowCompactor(CompactionStrategy):
    """Keep only the N most recent messages."""

    def __init__(self, max_messages: int = 100):
        """Initialize compactor.

        Args:
            max_messages: Maximum messages to keep
        """
        self.max_messages = max_messages

    async def compact(
        self,
        messages: list[Message],
        max_tokens: int,
    ) -> tuple[list[Message], str | None]:
        """Keep only recent messages."""
        if len(messages) > self.max_messages:
            # Keep only the last max_messages
            return messages[-self.max_messages:], None
        return messages, None


class SummarizeAndTrimCompactor(CompactionStrategy):
    """Summarize old messages and keep only recent ones (future)."""

    def __init__(self, summary_model: str = "claude-haiku-4-5-20251001"):
        """Initialize compactor.

        Args:
            summary_model: Model to use for summarization
        """
        self.summary_model = summary_model

    async def compact(
        self,
        messages: list[Message],
        max_tokens: int,
    ) -> tuple[list[Message], str | None]:
        """Summarize old messages (stub for v0.1)."""
        # TODO: Implement LLM-based summarization in v0.2
        return messages, None
