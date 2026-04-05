"""Skill execution engine."""

from typing import Any

from jclaw.observability import log_skill_execution
from jclaw.skills.base import Skill, SkillContext
from jclaw.skills.registry import SkillRegistry
from jclaw.types import HandoffRequest, SkillExecutionError, ToolCall, ToolResult


class SkillExecutor:
    """Executes skills/tools with error handling and special signal detection."""

    def __init__(self, skill_registry: SkillRegistry):
        """Initialize executor.

        Args:
            skill_registry: SkillRegistry instance
        """
        self.skill_registry = skill_registry

    async def execute_all(
        self,
        tool_calls: list[ToolCall],
        context: SkillContext,
    ) -> tuple[list[ToolResult], HandoffRequest | None]:
        """Execute all tool calls.

        Args:
            tool_calls: List of tool calls to execute
            context: Skill context

        Returns:
            Tuple of (list of ToolResults, HandoffRequest if detected)
        """
        results = []
        handoff_request = None

        for tool_call in tool_calls:
            result = await self.execute_one(tool_call, context)
            results.append(result)

            # Check for handoff signal
            if isinstance(result.output, dict) and result.output.get("__handoff__"):
                # Extract handoff request
                request_data = result.output.get("request", {})
                handoff_request = HandoffRequest(**request_data)
                # Stop processing further tool calls after handoff
                break

        return results, handoff_request

    async def execute_one(
        self,
        tool_call: ToolCall,
        context: SkillContext,
    ) -> ToolResult:
        """Execute a single tool call.

        Args:
            tool_call: Tool call to execute
            context: Skill context

        Returns:
            ToolResult with output or error
        """
        try:
            # Find the skill that has this tool
            skill = self._find_skill_for_tool(tool_call.name)

            if not skill:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    output=f"Tool '{tool_call.name}' not found",
                    is_error=True,
                )

            # Validate input
            if not skill.validate_input(tool_call.name, tool_call.input):
                return ToolResult(
                    tool_call_id=tool_call.id,
                    output=f"Invalid input for tool '{tool_call.name}'",
                    is_error=True,
                )

            # Execute
            result = await skill.execute(
                tool_call.name,
                tool_call.input,
                context,
            )

            # Update tool_call_id if not set
            if not result.tool_call_id:
                result.tool_call_id = tool_call.id

            log_skill_execution(
                skill_id=skill.skill_id,
                tool_name=tool_call.name,
                is_error=result.is_error,
            )

            return result

        except SkillExecutionError as e:
            log_skill_execution(
                skill_id="unknown",
                tool_name=tool_call.name,
                is_error=True,
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                output=str(e),
                is_error=True,
            )
        except Exception as e:
            log_skill_execution(
                skill_id="unknown",
                tool_name=tool_call.name,
                is_error=True,
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"Skill execution error: {e}",
                is_error=True,
            )

    def _find_skill_for_tool(self, tool_name: str) -> Skill | None:
        """Find the skill that provides a tool.

        Args:
            tool_name: Tool name to find

        Returns:
            Skill instance or None
        """
        for skill_id in self.skill_registry.list_skills():
            skill = self.skill_registry.get_skill(skill_id)
            for tool in skill.get_tools():
                if tool.name == tool_name:
                    return skill

        return None
