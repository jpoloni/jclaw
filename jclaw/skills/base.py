"""Base classes for the skill system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from jclaw.types import AgentConfig, Message, ToolDefinition, ToolResult


@dataclass
class SkillContext:
    """Context passed to skill execution."""

    session_id: str
    agent_config: AgentConfig
    inbound_message: Any  # InboundMessage (avoid circular import)
    metadata: dict[str, Any]


class Skill(ABC):
    """Abstract base class for skills (tools)."""

    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        """Get tool definitions exposed by this skill.

        Returns:
            List of ToolDefinition objects
        """
        pass

    @abstractmethod
    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        context: SkillContext,
    ) -> ToolResult:
        """Execute a tool from this skill.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input to the tool
            context: Skill context

        Returns:
            ToolResult with output or error

        Raises:
            SkillExecutionError: If execution fails
        """
        pass

    def validate_input(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Validate tool input before execution (optional override).

        Args:
            tool_name: Tool name
            tool_input: Input to validate

        Returns:
            True if valid, False otherwise
        """
        return True
