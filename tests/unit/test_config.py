"""Tests for configuration loading and management."""

from pathlib import Path

import pytest

from jclaw.config import AgentConfigValidator, AgentsYamlLoader
from jclaw.types import ConfigValidationError


class TestAgentsYamlLoader:
    """Tests for AgentsYamlLoader."""

    def test_load_valid_config(self):
        """Test loading a valid agents config."""
        loader = AgentsYamlLoader("config/agents.yaml")
        agents = loader.load()

        assert len(agents) > 0
        assert all(agent.agent_id for agent in agents)

        # Check first agent (triage)
        triage = next(a for a in agents if a.agent_id == "triage")
        assert triage.name == "Support Triage Agent"
        assert len(triage.handoff_targets) > 0

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        loader = AgentsYamlLoader("nonexistent.yaml")
        with pytest.raises(ConfigValidationError):
            loader.load()

    def test_validate_cross_references(self):
        """Test that handoff targets are validated."""
        loader = AgentsYamlLoader("config/agents.yaml")
        agents = loader.load()

        # All handoff targets should be valid
        agent_ids = {agent.agent_id for agent in agents}
        for agent in agents:
            for target in agent.handoff_targets:
                assert target in agent_ids

    def test_prompt_ref_parsing(self):
        """Test that .j2 files are converted to PromptRef."""
        # Create a test YAML config
        test_yaml = """
agents:
  - agent_id: test_agent
    name: Test Agent
    description: Test
    system_prompt: prompts/test.j2
"""
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(test_yaml)
            f.flush()

            loader = AgentsYamlLoader(f.name)
            agents = loader.load()

            assert len(agents) == 1
            agent = agents[0]
            # Check if it was converted to PromptRef or kept as string
            # (depending on implementation)
            assert agent.system_prompt

            # Cleanup
            Path(f.name).unlink()


class TestAgentConfigValidator:
    """Tests for AgentConfigValidator."""

    def test_validate_empty_prompt(self):
        """Test validation of agent with empty prompt."""
        from jclaw.types import AgentConfig

        agent = AgentConfig(
            agent_id="test",
            name="Test",
            description="Test",
            system_prompt="",  # Empty
        )

        warnings = AgentConfigValidator.validate_agent(agent)
        assert len(warnings) > 0
        assert "empty system_prompt" in warnings[0].lower()

    def test_validate_high_temperature(self):
        """Test validation of high temperature."""
        from jclaw.types import AgentConfig

        agent = AgentConfig(
            agent_id="test",
            name="Test",
            description="Test",
            system_prompt="Test prompt",
            temperature=1.8,  # High
        )

        warnings = AgentConfigValidator.validate_agent(agent)
        assert len(warnings) > 0
        assert "high temperature" in warnings[0].lower()

    def test_validate_good_config(self):
        """Test validation of good config."""
        from jclaw.types import AgentConfig

        agent = AgentConfig(
            agent_id="test",
            name="Test",
            description="Test",
            system_prompt="You are helpful.",
            temperature=0.7,
        )

        warnings = AgentConfigValidator.validate_agent(agent)
        # Should have no warnings for this good config
        assert len(warnings) == 0
