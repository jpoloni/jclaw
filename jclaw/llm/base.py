"""Abstract base classes for LLM providers and token counting."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from jclaw.types import LLMResponse, Message, StreamChunk, ToolDefinition


class TokenCounter(ABC):
    """Abstract base class for token counting."""

    @abstractmethod
    def count(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def count_messages(self, messages: list[Message]) -> int:
        """Count tokens in a list of messages.

        Args:
            messages: Messages to count

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def count_tools(self, tools: list[ToolDefinition]) -> int:
        """Count tokens in tool definitions.

        Args:
            tools: Tool definitions to count

        Returns:
            Number of tokens
        """
        pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_id: str

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Get completion from LLM.

        Args:
            messages: Conversation messages
            model: Model identifier
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            tools: Optional tool definitions
            stop_sequences: Optional stop sequences

        Returns:
            LLM response with content, tool calls, stop reason, usage

        Raises:
            LLMAPIError: If API call fails
            LLMTimeoutError: If call times out
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from LLM.

        Args:
            messages: Conversation messages
            model: Model identifier
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            tools: Optional tool definitions
            stop_sequences: Optional stop sequences

        Yields:
            Stream chunks with delta, chunk_type, optional tool_call

        Raises:
            LLMAPIError: If API call fails
            LLMTimeoutError: If call times out
        """
        pass

    @abstractmethod
    def get_token_counter(self) -> TokenCounter:
        """Get token counter for this provider.

        Returns:
            TokenCounter instance
        """
        pass
