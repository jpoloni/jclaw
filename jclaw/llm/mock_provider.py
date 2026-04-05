"""Mock LLM provider for testing."""

import asyncio
from typing import AsyncIterator

from jclaw.llm.base import LLMProvider, TokenCounter
from jclaw.types import LLMResponse, Message, StreamChunk, ToolCall, ToolDefinition, TokenUsage


class MockTokenCounter(TokenCounter):
    """Simple token counter: len(text) / 4."""

    def count(self, text: str) -> int:
        """Count tokens (heuristic: 1 token ≈ 4 characters)."""
        return max(1, len(text) // 4)

    def count_messages(self, messages: list[Message]) -> int:
        """Count tokens in messages."""
        return sum(self.count(msg.content) for msg in messages)

    def count_tools(self, tools: list[ToolDefinition]) -> int:
        """Count tokens in tool definitions."""
        total = 0
        for tool in tools:
            total += self.count(tool.name)
            total += self.count(tool.description)
            # Rough estimate for JSON schema
            total += 50
        return total


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and development.

    Supports:
    - Echo mode: returns user message as assistant response
    - Deterministic responses: preset responses for testing
    - Tool call injection: return predefined tool calls
    - Error simulation: raise errors on demand
    - Latency simulation: add artificial delay
    """

    provider_id = "mock"

    def __init__(
        self,
        echo_mode: bool = True,
        latency_ms: float = 0.0,
        preset_responses: dict[str, str] | None = None,
        inject_tool_calls: list[ToolCall] | None = None,
        error_on_call: Exception | None = None,
    ):
        """Initialize mock provider.

        Args:
            echo_mode: If True, return user message as response
            latency_ms: Artificial latency in milliseconds
            preset_responses: Dict mapping message content to response
            inject_tool_calls: Tool calls to inject in response
            error_on_call: Exception to raise on complete()
        """
        self.echo_mode = echo_mode
        self.latency_ms = latency_ms
        self.preset_responses = preset_responses or {}
        self.inject_tool_calls = inject_tool_calls or []
        self.error_on_call = error_on_call
        self.call_count = 0
        self.last_messages: list[Message] | None = None
        self.last_model: str | None = None
        self._token_counter = MockTokenCounter()

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Get mock completion."""
        # Store call history for inspection
        self.call_count += 1
        self.last_messages = messages
        self.last_model = model

        # Add latency if configured
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000.0)

        # Raise error if configured
        if self.error_on_call:
            raise self.error_on_call

        # Get the user's last message
        last_user_message = next(
            (m for m in reversed(messages) if m.role == "user"),
            None,
        )
        user_text = last_user_message.content if last_user_message else ""

        # Check for preset response
        response_text = self.preset_responses.get(user_text)

        # Default to echo mode
        if response_text is None:
            if self.echo_mode:
                response_text = f"Echo: {user_text}"
            else:
                response_text = "Mock response"

        # Count tokens
        input_tokens = self._token_counter.count_messages(messages)
        output_tokens = self._token_counter.count(response_text)

        return LLMResponse(
            content=response_text,
            tool_calls=self.inject_tool_calls,
            stop_reason="tool_use" if self.inject_tool_calls else "end_turn",
            model=model,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                estimated_cost_usd=None,
            ),
            latency_ms=self.latency_ms,
        )

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream mock completion."""
        # Get complete response first
        response = await self.complete(
            messages, model, temperature, max_tokens, tools, stop_sequences
        )

        # Yield in chunks
        for char in response.content or "":
            await asyncio.sleep(0.01)  # Simulate streaming delay
            yield StreamChunk(delta=char, chunk_type="text")

        # Yield tool calls if any
        for tool_call in response.tool_calls:
            yield StreamChunk(delta="", chunk_type="tool_call", tool_call=tool_call)

        # Yield stop
        yield StreamChunk(
            delta="",
            chunk_type="stop",
            stop_reason=response.stop_reason,
        )

    def get_token_counter(self) -> TokenCounter:
        """Get token counter."""
        return self._token_counter

    def set_preset_response(self, input_text: str, output_text: str) -> None:
        """Set a preset response for testing."""
        self.preset_responses[input_text] = output_text

    def reset(self) -> None:
        """Reset call history."""
        self.call_count = 0
        self.last_messages = None
        self.last_model = None
