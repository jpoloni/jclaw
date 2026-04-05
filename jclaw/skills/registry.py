"""Skill registry and discovery."""

from typing import Any

from jclaw.skills.base import Skill
from jclaw.skills.builtin import HandoffSkill
from jclaw.types import AgentConfig, SkillNotFoundError, ToolDefinition


class SkillRegistry:
    """Registry for managing skills."""

    def __init__(self):
        """Initialize registry with built-in skills."""
        self._skills: dict[str, Skill] = {}

        # Register built-in skills
        self.register(HandoffSkill())

    def register(self, skill: Skill) -> None:
        """Register a skill.

        Args:
            skill: Skill instance to register

        Raises:
            ValueError: If skill ID already registered
        """
        if skill.skill_id in self._skills:
            raise ValueError(f"Skill '{skill.skill_id}' already registered")

        self._skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> Skill:
        """Get a skill by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill instance

        Raises:
            SkillNotFoundError: If skill not found
        """
        if skill_id not in self._skills:
            raise SkillNotFoundError(f"Skill '{skill_id}' not found")

        return self._skills[skill_id]

    def get_tools_for_agent(self, agent_config: AgentConfig) -> list[ToolDefinition]:
        """Get all tools available for an agent.

        Args:
            agent_config: Agent configuration

        Returns:
            List of ToolDefinition objects
        """
        tools = []

        # For each skill in the agent's skills list
        for skill_id in agent_config.skills:
            try:
                skill = self.get_skill(skill_id)
                tools.extend(skill.get_tools())
            except SkillNotFoundError:
                # Log warning but continue
                pass

        # Always include handoff tool
        handoff_skill = self.get_skill("handoff_to_agent")
        tools.extend(handoff_skill.get_tools())

        return tools

    def list_skills(self) -> list[str]:
        """Get list of registered skill IDs.

        Returns:
            List of skill IDs
        """
        return list(self._skills.keys())

    def discover_plugins(self) -> None:
        """Discover and load skills from entry points.

        This is called at startup to load third-party skills installed
        via entry_points in pyproject.toml.

        For v0.1, this is a stub. TODO v0.2: Implement entry_points discovery.
        """
        # TODO: Use importlib.metadata.entry_points("jclaw.skills")
        pass
