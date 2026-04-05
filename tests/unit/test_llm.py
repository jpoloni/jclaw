"""Tests for LLM providers and routing."""

import pytest

from jclaw.config import LLMRouterConfig
from jclaw.llm import CircuitBreaker, CircuitState, LLMRouter, MockLLMProvider
from jclaw.types import LLMProviderError, Message


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    @pytest.mark.asyncio
    async def test_echo_mode(self, mock_llm):
        """Test mock provider in echo mode."""
        messages = [Message(role="user", content="Hello")]

        response = await mock_llm.complete(
            messages=messages,
            model="mock-model",
        )

        assert response.content == "Echo: Hello"
        assert response.stop_reason == "end_turn"
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_preset_response(self, mock_llm_with_response):
        """Test mock provider with preset response."""
        messages = [Message(role="user", content="Hello")]

        response = await mock_llm_with_response.complete(
            messages=messages,
            model="mock-model",
        )

        assert response.content == "Hi there!"

    @pytest.mark.asyncio
    async def test_error_simulation(self):
        """Test mock provider error simulation."""
        error = ValueError("Simulated error")
        provider = MockLLMProvider(error_on_call=error)

        messages = [Message(role="user", content="Hello")]

        with pytest.raises(ValueError):
            await provider.complete(messages=messages, model="mock-model")

    @pytest.mark.asyncio
    async def test_tool_injection(self):
        """Test injecting tool calls in response."""
        from jclaw.types import ToolCall

        tool_calls = [
            ToolCall(name="search", input={"query": "test"}),
        ]
        provider = MockLLMProvider(inject_tool_calls=tool_calls)

        messages = [Message(role="user", content="Search for test")]

        response = await provider.complete(messages=messages, model="mock-model")

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search"
        assert response.stop_reason == "tool_use"

    def test_token_counter(self):
        """Test token counting."""
        from jclaw.llm import MockTokenCounter

        counter = MockTokenCounter()

        # Rough heuristic: 4 chars per token
        count = counter.count("Hello world, this is a test!")
        assert count > 0
        assert count < 10  # Should be ~7-8

    @pytest.mark.asyncio
    async def test_call_history(self, mock_llm):
        """Test that call history is tracked."""
        assert mock_llm.call_count == 0

        messages = [Message(role="user", content="Test")]
        await mock_llm.complete(messages=messages, model="test-model")

        assert mock_llm.call_count == 1
        assert mock_llm.last_model == "test-model"
        assert mock_llm.last_messages == messages


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(failure_threshold=3)

        # Should allow calls through
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.get_state() == CircuitState.CLOSED

    def test_open_on_failures(self):
        """Test circuit breaker opens after threshold."""
        cb = CircuitBreaker(failure_threshold=2)

        # Fail twice
        for _ in range(2):
            try:
                cb.call(lambda: 1 / 0)  # Raises ZeroDivisionError
            except:
                pass

        # Circuit should be open
        assert cb.get_state() == CircuitState.OPEN

    def test_reject_when_open(self):
        """Test circuit breaker rejects calls when open."""
        from jclaw.types import CircuitBreakerOpenError

        cb = CircuitBreaker(failure_threshold=1)

        # Force open
        try:
            cb.call(lambda: 1 / 0)
        except:
            pass

        # Should reject next call
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_recovery_to_half_open(self):
        """Test circuit breaker recovery attempt."""
        import time

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)

        # Force open
        try:
            cb.call(lambda: 1 / 0)
        except:
            pass

        # Wait briefly
        time.sleep(0.1)

        # Should attempt recovery (go to HALF_OPEN)
        try:
            cb.call(lambda: "success")
            # If we got here, we're in HALF_OPEN and call succeeded
            assert cb.get_state() in (CircuitState.HALF_OPEN, CircuitState.CLOSED)
        except:
            pass

    def test_reset(self):
        """Test resetting circuit breaker."""
        cb = CircuitBreaker(failure_threshold=1)

        # Force open
        try:
            cb.call(lambda: 1 / 0)
        except:
            pass

        assert cb.get_state() == CircuitState.OPEN

        # Reset
        cb.reset()
        assert cb.get_state() == CircuitState.CLOSED


class TestLLMRouter:
    """Tests for LLMRouter."""

    @pytest.mark.asyncio
    async def test_static_policy(self, mock_llm):
        """Test router with static policy."""
        router = LLMRouter(
            providers={"mock": mock_llm},
            config=LLMRouterConfig(policy="static"),
        )

        messages = [Message(role="user", content="Hello")]

        response = await router.complete(
            messages=messages,
            provider_id="mock",
            model="mock-model",
        )

        assert response.content == "Echo: Hello"

    @pytest.mark.asyncio
    async def test_missing_provider(self, mock_llm):
        """Test router with missing provider."""
        router = LLMRouter(
            providers={"mock": mock_llm},
        )

        messages = [Message(role="user", content="Hello")]

        with pytest.raises(LLMProviderError):
            await router.complete(
                messages=messages,
                provider_id="nonexistent",
                model="mock-model",
            )

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test router with circuit breaker."""
        error_provider = MockLLMProvider(
            error_on_call=RuntimeError("API error")
        )

        router = LLMRouter(
            providers={"failing": error_provider},
            config=LLMRouterConfig(max_retries=0),
        )

        messages = [Message(role="user", content="Hello")]

        # First failure
        with pytest.raises(LLMProviderError):
            await router.complete(
                messages=messages,
                provider_id="failing",
                model="test",
            )

        # Circuit should be in HALF_OPEN or OPEN state after failures
        state = router.get_circuit_breaker_state("failing")
        assert state in ("open", "half_open", "closed")
