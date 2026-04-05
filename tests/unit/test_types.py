"""Tests for jClaw type definitions."""

import pytest
from datetime import datetime

from jclaw.types import (
    AgentConfig,
    Button,
    HandoffRequest,
    InboundMessage,
    Message,
    OutboundMessage,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestMessages:
    """Tests for message types."""

    def test_message_creation(self):
        """Test creating a basic message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_tool_calls(self):
        """Test message with tool calls."""
        tool_call = ToolCall(name="search", input={"query": "test"})
        msg = Message(role="assistant", content="", tool_calls=[tool_call])
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "search"

    def test_inbound_message(self):
        """Test creating inbound message."""
        inbound = InboundMessage(
            chat_id="12345",
            user_id="user1",
            channel="telegram",
            text="Hello bot",
        )
        assert inbound.chat_id == "12345"
        assert inbound.user_id == "user1"
        assert inbound.channel == "telegram"
        assert inbound.text == "Hello bot"
        assert inbound.message_id is not None

    def test_outbound_message(self):
        """Test creating outbound message."""
        button = Button(label="Click me", action="postback", value="clicked")
        outbound = OutboundMessage(
            text="Here are your options:",
            buttons=[button],
        )
        assert outbound.text == "Here are your options:"
        assert len(outbound.buttons) == 1
        assert outbound.buttons[0].label == "Click me"

    def test_tool_definition(self):
        """Test tool definition."""
        tool = ToolDefinition(
            name="search",
            description="Search the web",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        )
        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert "properties" in tool.input_schema

    def test_tool_result(self):
        """Test tool result."""
        result = ToolResult(
            tool_call_id="call_1",
            output="Search results...",
        )
        assert result.tool_call_id == "call_1"
        assert result.output == "Search results..."
        assert result.is_error is False

    def test_tool_result_error(self):
        """Test tool result with error."""
        result = ToolResult(
            tool_call_id="call_1",
            output={"error": "Tool failed"},
            is_error=True,
        )
        assert result.is_error is True


class TestAgentConfig:
    """Tests for agent configuration."""

    def test_basic_agent_config(self):
        """Test creating basic agent config."""
        config = AgentConfig(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            system_prompt="You are helpful",
        )
        assert config.agent_id == "test_agent"
        assert config.name == "Test Agent"
        assert config.llm_provider == "anthropic"  # default
        assert config.llm_model == "claude-sonnet-4-20250514"  # default
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 4096  # default

    def test_agent_config_with_skills(self):
        """Test agent config with skills."""
        config = AgentConfig(
            agent_id="agent1",
            name="Agent 1",
            description="Agent with skills",
            system_prompt="You are helpful",
            skills=["web_search", "knowledge_base"],
            handoff_targets=["agent2", "agent3"],
        )
        assert config.skills == ["web_search", "knowledge_base"]
        assert config.handoff_targets == ["agent2", "agent3"]

    def test_agent_config_temperature_constraints(self):
        """Test temperature is constrained between 0 and 2."""
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                system_prompt="Test",
                temperature=-0.1,
            )

        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                system_prompt="Test",
                temperature=2.5,
            )

    def test_agent_config_positive_tokens(self):
        """Test max_tokens must be positive."""
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                system_prompt="Test",
                max_tokens=0,
            )

        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                system_prompt="Test",
                max_tokens=-100,
            )

    def test_agent_config_context_window_minimum(self):
        """Test context_window has minimum value."""
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                description="Test",
                system_prompt="Test",
                context_window=100,  # Less than minimum 1000
            )


class TestHandoffRequest:
    """Tests for handoff request."""

    def test_basic_handoff(self):
        """Test creating a handoff request."""
        handoff = HandoffRequest(
            source_agent_id="agent1",
            target_agent_id="agent2",
            reason="Customer needs billing support",
        )
        assert handoff.source_agent_id == "agent1"
        assert handoff.target_agent_id == "agent2"
        assert handoff.mode == "transfer"  # default
        assert handoff.preserve_history is True  # default

    def test_handoff_with_context(self):
        """Test handoff with context payload."""
        context = {"customer_id": "12345", "issue": "billing"}
        handoff = HandoffRequest(
            source_agent_id="sales",
            target_agent_id="support",
            reason="Escalating to billing support",
            context_payload=context,
        )
        assert handoff.context_payload == context

    def test_handoff_modes(self):
        """Test different handoff modes."""
        for mode in ["transfer", "delegate", "escalate"]:
            handoff = HandoffRequest(
                source_agent_id="a",
                target_agent_id="b",
                reason="Test",
                mode=mode,
            )
            assert handoff.mode == mode


class TestSerialization:
    """Tests for Pydantic serialization."""

    def test_message_json_serialization(self):
        """Test message can be serialized to JSON."""
        msg = Message(role="user", content="Test message")
        json_str = msg.model_dump_json()
        assert "user" in json_str
        assert "Test message" in json_str

    def test_agent_config_json_schema(self):
        """Test agent config generates valid JSON schema."""
        schema = AgentConfig.model_json_schema()
        assert "$defs" in schema or "definitions" in schema
        assert "properties" in schema
        assert "agent_id" in schema["properties"]
        assert "system_prompt" in schema["properties"]

    def test_message_deserialization(self):
        """Test message can be deserialized from dict."""
        data = {
            "role": "assistant",
            "content": "Hello there",
            "metadata": {"source": "llm"},
        }
        msg = Message(**data)
        assert msg.role == "assistant"
        assert msg.content == "Hello there"
        assert msg.metadata["source"] == "llm"
