"""Tests for skill system."""

import pytest

from jclaw.skills import HandoffSkill, SkillContext, SkillExecutor, SkillRegistry
from jclaw.types import (
    AgentConfig,
    HandoffRequest,
    InboundMessage,
    SkillNotFoundError,
    ToolCall,
)


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def test_register_skill(self):
        """Test registering a skill."""
        registry = SkillRegistry()
        assert registry.get_skill("handoff_to_agent") is not None

    def test_get_nonexistent_skill(self):
        """Test getting a non-existent skill."""
        registry = SkillRegistry()

        with pytest.raises(SkillNotFoundError):
            registry.get_skill("nonexistent_skill")

    def test_duplicate_registration(self):
        """Test registering the same skill twice."""
        registry = SkillRegistry()

        with pytest.raises(ValueError):
            registry.register(HandoffSkill())

    def test_list_skills(self):
        """Test listing registered skills."""
        registry = SkillRegistry()
        skills = registry.list_skills()

        assert "handoff_to_agent" in skills

    def test_get_tools_for_agent(self, agent_config):
        """Test getting tools for an agent."""
        registry = SkillRegistry()
        tools = registry.get_tools_for_agent(agent_config)

        # Should at least have handoff tool
        tool_names = [t.name for t in tools]
        assert "handoff_to_agent" in tool_names


class TestHandoffSkill:
    """Tests for HandoffSkill."""

    @pytest.mark.asyncio
    async def test_handoff_execution(self, agent_config):
        """Test executing a handoff."""
        skill = HandoffSkill()
        context = SkillContext(
            session_id="session_1",
            agent_config=agent_config,
            inbound_message=InboundMessage(
                chat_id="chat1",
                user_id="user1",
                channel="test",
                text="Test",
            ),
            metadata={},
        )

        result = await skill.execute(
            "handoff_to_agent",
            {
                "target_agent_id": "support",
                "reason": "User needs support",
            },
            context,
        )

        # Should return special handoff result
        assert result.is_error is False
        assert isinstance(result.output, dict)
        assert result.output.get("__handoff__") is True
        assert "request" in result.output

    @pytest.mark.asyncio
    async def test_handoff_with_context(self, agent_config):
        """Test handoff with additional context."""
        skill = HandoffSkill()
        context = SkillContext(
            session_id="session_1",
            agent_config=agent_config,
            inbound_message=InboundMessage(
                chat_id="chat1",
                user_id="user1",
                channel="test",
                text="Test",
            ),
            metadata={},
        )

        result = await skill.execute(
            "handoff_to_agent",
            {
                "target_agent_id": "billing",
                "reason": "Billing inquiry",
                "context": {"issue": "invoice_dispute"},
            },
            context,
        )

        request_data = result.output["request"]
        assert request_data["context_payload"]["issue"] == "invoice_dispute"

    @pytest.mark.asyncio
    async def test_handoff_missing_target(self, agent_config):
        """Test handoff without target agent."""
        from jclaw.types import SkillExecutionError

        skill = HandoffSkill()
        context = SkillContext(
            session_id="session_1",
            agent_config=agent_config,
            inbound_message=InboundMessage(
                chat_id="chat1",
                user_id="user1",
                channel="test",
                text="Test",
            ),
            metadata={},
        )

        with pytest.raises(SkillExecutionError):
            await skill.execute(
                "handoff_to_agent",
                {"reason": "No target"},
                context,
            )


class TestSkillExecutor:
    """Tests for SkillExecutor."""

    @pytest.mark.asyncio
    async def test_execute_all_tools(self, agent_config):
        """Test executing multiple tool calls."""
        registry = SkillRegistry()
        executor = SkillExecutor(registry)

        context = SkillContext(
            session_id="session_1",
            agent_config=agent_config,
            inbound_message=InboundMessage(
                chat_id="chat1",
                user_id="user1",
                channel="test",
                text="Test",
            ),
            metadata={},
        )

        tool_calls = [
            ToolCall(id="1", name="handoff_to_agent", input={
                "target_agent_id": "support",
                "reason": "Test",
            }),
        ]

        results, handoff = await executor.execute_all(tool_calls, context)

        assert len(results) == 1
        assert results[0].is_error is False
        assert handoff is not None
        assert isinstance(handoff, HandoffRequest)
        assert handoff.target_agent_id == "support"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, agent_config):
        """Test executing an unknown tool."""
        registry = SkillRegistry()
        executor = SkillExecutor(registry)

        context = SkillContext(
            session_id="session_1",
            agent_config=agent_config,
            inbound_message=InboundMessage(
                chat_id="chat1",
                user_id="user1",
                channel="test",
                text="Test",
            ),
            metadata={},
        )

        tool_calls = [
            ToolCall(id="1", name="unknown_tool", input={}),
        ]

        results, handoff = await executor.execute_all(tool_calls, context)

        assert len(results) == 1
        assert results[0].is_error is True
        assert "not found" in results[0].output
        assert handoff is None
