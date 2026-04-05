"""Anthropic Claude LLM provider."""

import time
from typing import AsyncIterator

import anthropic

from jclaw.llm.base import LLMProvider, TokenCounter
from jclaw.types import (
    LLMAPIError,
    LLMResponse,
    LLMTimeoutError,
    Message,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    TokenUsage,
)


class AnthropicTokenCounter(TokenCounter):
    """Token counter using Anthropic's native API (fallback to heuristic)."""

    def __init__(self, client: anthropic.Anthropic | None = None):
        """Initialize counter.

        Args:
            client: Anthropic client instance (optional, for native counting)
        """
        self.client = client

    def count(self, text: str) -> int:
        """Count tokens in text.

        NOTE: v0.1 uses heuristic (len/4) for performance.
        TODO v0.2: Use client.beta.messages.count_tokens() for accuracy.
        """
        # Heuristic: ~4 characters per token
        return max(1, len(text) // 4)

    def count_messages(self, messages: list[Message]) -> int:
        """Count tokens in messages."""
        total = 0
        for msg in messages:
            total += self.count(msg.content)
            if msg.name:
                total += self.count(msg.name)
        return total

    def count_tools(self, tools: list[ToolDefinition]) -> int:
        """Count tokens in tool definitions."""
        total = 0
        for tool in tools:
            total += self.count(tool.name)
            total += self.count(tool.description)
            # Rough estimate for JSON schema
            total += 100
        return total


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    provider_id = "anthropic"

    def __init__(self, api_key: str | None = None):
        """Initialize provider.

        Args:
            api_key: Anthropic API key (from env if not provided)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self._token_counter = AnthropicTokenCounter(self.client)

    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Get completion from Claude."""
        try:
            # Convert messages to Anthropic format
            api_messages = self._convert_messages(messages)

            # Build request kwargs
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": api_messages,
                "temperature": temperature,
            }

            # Add tools if provided
            if tools:
                kwargs["tools"] = [self._convert_tool(tool) for tool in tools]

            # Add stop sequences if provided
            if stop_sequences:
                kwargs["stop_sequences"] = stop_sequences

            # Make request
            start_time = time.time()
            response = self.client.messages.create(**kwargs)
            latency_ms = (time.time() - start_time) * 1000

            # Extract content and tool calls
            content_text = ""
            tool_calls = []

            for block in response.content:
                if hasattr(block, "text"):
                    content_text = block.text
                elif hasattr(block, "type") and block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            input=block.input,
                        )
                    )

            # Map stop reason
            stop_reason = self._map_stop_reason(response.stop_reason)

            return LLMResponse(
                content=content_text,
                tool_calls=tool_calls,
                stop_reason=stop_reason,
                model=model,
                usage=TokenUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    estimated_cost_usd=self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens, model),
                ),
                latency_ms=latency_ms,
            )

        except anthropic.APIError as e:
            raise LLMAPIError(f"Anthropic API error: {e}")
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic API timeout: {e}")

    async def stream(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from Claude."""
        try:
            # Convert messages to Anthropic format
            api_messages = self._convert_messages(messages)

            # Build request kwargs
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": api_messages,
                "temperature": temperature,
            }

            if tools:
                kwargs["tools"] = [self._convert_tool(tool) for tool in tools]

            if stop_sequences:
                kwargs["stop_sequences"] = stop_sequences

            # Stream
            with self.client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if hasattr(event, "type") and event.type == "content_block_delta":
                        if hasattr(event.delta, "type") and event.delta.type == "text_delta":
                            yield StreamChunk(
                                delta=event.delta.text,
                                chunk_type="text",
                            )
                    elif hasattr(event, "type") and event.type == "content_block_start":
                        if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                            # Tool call starting
                            pass

        except anthropic.APIError as e:
            raise LLMAPIError(f"Anthropic API error: {e}")
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic API timeout: {e}")

    def get_token_counter(self) -> TokenCounter:
        """Get token counter."""
        return self._token_counter

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert jClaw messages to Anthropic format."""
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                # Skip system messages (handled separately)
                continue

            api_msg = {
                "role": msg.role,
                "content": msg.content,
            }
            api_messages.append(api_msg)

        return api_messages

    def _convert_tool(self, tool: ToolDefinition) -> dict:
        """Convert tool definition to Anthropic format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }

    def _map_stop_reason(self, anthropic_stop_reason: str) -> str:
        """Map Anthropic stop reason to jClaw format."""
        mapping = {
            "end_turn": "end_turn",
            "max_tokens": "max_tokens",
            "tool_use": "tool_use",
            "stop_sequence": "stop_sequence",
        }
        return mapping.get(anthropic_stop_reason, "end_turn")

    def _estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for the request.

        Pricing as of April 2026 (update as needed).
        """
        # Pricing per 1M tokens
        pricing = {
            "claude-opus-4": {"input": 15.0, "output": 75.0},
            "claude-sonnet-4": {"input": 3.0, "output": 15.0},
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
        }

        config = pricing.get(model, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1_000_000) * config["input"]
        output_cost = (output_tokens / 1_000_000) * config["output"]

        return input_cost + output_cost
