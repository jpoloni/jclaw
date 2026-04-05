"""Pytest configuration and shared fixtures for jClaw tests."""

import asyncio
import logging
from typing import AsyncGenerator

import pytest
from redis.asyncio import Redis

from jclaw.llm import MockLLMProvider
from jclaw.types import AgentConfig, GuardrailConfig, MemoryConfig, PromptConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def agent_config() -> AgentConfig:
    """Minimal valid AgentConfig for testing."""
    return AgentConfig(
        agent_id="test_agent",
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a helpful assistant.",
        llm_provider="mock",
        llm_model="mock-model",
        temperature=0.7,
        max_tokens=4096,
        context_window=128000,
        skills=[],
        handoff_targets=[],
        guardrails=GuardrailConfig(),
        memory=MemoryConfig(),
    )


@pytest.fixture
def agent_config_with_handoff() -> AgentConfig:
    """AgentConfig that can handoff to other agents."""
    return AgentConfig(
        agent_id="agent_a",
        name="Agent A",
        description="Agent A with handoff",
        system_prompt="You are Agent A",
        handoff_targets=["agent_b", "agent_c"],
    )


@pytest.fixture
def guardrail_config() -> GuardrailConfig:
    """GuardrailConfig for testing."""
    return GuardrailConfig(
        input_guardrails=["pii_detector", "injection_guard"],
        output_guardrails=["length_limiter"],
        block_mode="message",
    )


@pytest.fixture
def prompt_config() -> PromptConfig:
    """PromptConfig for testing."""
    return PromptConfig(
        version="1.0.0",
        variables=[],
        layers=[],
    )


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    yield


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    """Mock LLM provider in echo mode for testing."""
    return MockLLMProvider(echo_mode=True, latency_ms=0)


@pytest.fixture
def mock_llm_with_response() -> MockLLMProvider:
    """Mock LLM provider with preset response."""
    provider = MockLLMProvider(echo_mode=False)
    provider.set_preset_response("Hello", "Hi there!")
    return provider
