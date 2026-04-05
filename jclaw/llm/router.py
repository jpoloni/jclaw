"""LLM router for multi-provider support with circuit breaker and retries."""

import asyncio
from typing import AsyncIterator

from jclaw.config import CircuitBreakerConfig, LLMRouterConfig
from jclaw.llm.base import LLMProvider
from jclaw.llm.circuit_breaker import CircuitBreaker
from jclaw.types import (
    LLMProviderError,
    LLMResponse,
    LLMTimeoutError,
    Message,
    StreamChunk,
    ToolDefinition,
)


class LLMRouter:
    """Routes LLM requests to providers with fallback, retries, and circuit breaker.

    Supports:
    - Multiple providers with fallback chain
    - Per-provider circuit breaker
    - Automatic retries with exponential backoff
    - Request timeout enforcement
    """

    def __init__(
        self,
        providers: dict[str, LLMProvider],
        config: LLMRouterConfig | None = None,
    ):
        """Initialize router.

        Args:
            providers: Dict mapping provider_id to LLMProvider instance
            config: Router configuration (default: static policy)
        """
        self.providers = providers
        self.config = config or LLMRouterConfig()

        # Initialize circuit breakers for each provider
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        for provider_id in providers:
            self._circuit_breakers[provider_id] = CircuitBreaker(
                failure_threshold=self.config.circuit_breaker.failure_threshold,
                recovery_timeout=self.config.circuit_breaker.recovery_timeout,
                half_open_max_calls=self.config.circuit_breaker.half_open_max_calls,
            )

    async def complete(
        self,
        messages: list[Message],
        provider_id: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        """Get completion from LLM provider with retries and fallback.

        Args:
            messages: Conversation messages
            provider_id: Primary provider ID
            model: Model identifier
            temperature: Temperature setting
            max_tokens: Maximum response tokens
            tools: Optional tools
            stop_sequences: Optional stop sequences

        Returns:
            LLM response

        Raises:
            LLMProviderError: If all providers fail
            LLMTimeoutError: If request times out
        """
        # Build provider chain based on policy
        provider_chain = self._get_provider_chain(provider_id)

        last_error: Exception | None = None

        for prov_id in provider_chain:
            provider = self.providers.get(prov_id)
            if not provider:
                continue

            for attempt in range(1, self.config.max_retries + 2):
                try:
                    # Execute with circuit breaker
                    circuit_breaker = self._circuit_breakers[prov_id]

                    response = await asyncio.wait_for(
                        circuit_breaker.acall(
                            provider.complete,
                            messages=messages,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            tools=tools,
                            stop_sequences=stop_sequences,
                        ),
                        timeout=self.config.timeout_seconds,
                    )

                    return response

                except asyncio.TimeoutError:
                    last_error = LLMTimeoutError(f"Request to {prov_id} timed out after {self.config.timeout_seconds}s")
                    if attempt < self.config.max_retries + 1:
                        # Wait before retry with exponential backoff
                        await asyncio.sleep(self.config.retry_delay_seconds ** (attempt - 1))
                    else:
                        break

                except Exception as e:
                    last_error = e
                    if attempt < self.config.max_retries + 1:
                        # Wait before retry
                        await asyncio.sleep(self.config.retry_delay_seconds ** (attempt - 1))
                    else:
                        break

        # All providers failed
        if last_error:
            raise LLMProviderError(f"All LLM providers failed. Last error: {last_error}")

        raise LLMProviderError("No LLM providers available")

    async def stream(
        self,
        messages: list[Message],
        provider_id: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from LLM provider.

        Args:
            messages: Conversation messages
            provider_id: Primary provider ID
            model: Model identifier
            temperature: Temperature setting
            max_tokens: Maximum response tokens
            tools: Optional tools
            stop_sequences: Optional stop sequences

        Yields:
            Stream chunks

        Raises:
            LLMProviderError: If provider fails
            LLMTimeoutError: If request times out
        """
        provider = self.providers.get(provider_id)
        if not provider:
            raise LLMProviderError(f"Provider {provider_id} not found")

        circuit_breaker = self._circuit_breakers[provider_id]

        try:
            async for chunk in await asyncio.wait_for(
                circuit_breaker.acall(
                    provider.stream,
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    stop_sequences=stop_sequences,
                ),
                timeout=self.config.timeout_seconds,
            ):
                yield chunk

        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"Stream from {provider_id} timed out")

    def _get_provider_chain(self, primary_provider_id: str) -> list[str]:
        """Get provider chain based on routing policy.

        Args:
            primary_provider_id: Primary provider ID

        Returns:
            List of provider IDs to try in order
        """
        if self.config.policy == "static":
            return [primary_provider_id]

        elif self.config.policy == "fallback_chain":
            # Return fallback chain from config
            chain = [primary_provider_id]
            for pair in self.config.fallback_chain:
                if pair.provider not in chain:
                    chain.append(pair.provider)
            return chain

        elif self.config.policy in ("cost_optimized", "latency_optimized"):
            # For v0.1, fall back to static
            # TODO v0.2: Implement cost/latency-based routing
            return [primary_provider_id]

        else:
            return [primary_provider_id]

    def get_circuit_breaker_state(self, provider_id: str) -> str:
        """Get circuit breaker state for a provider.

        Args:
            provider_id: Provider ID

        Returns:
            State name (closed, open, half_open)
        """
        if provider_id not in self._circuit_breakers:
            return "unknown"
        return self._circuit_breakers[provider_id].get_state().value
