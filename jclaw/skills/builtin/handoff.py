"""Built-in handoff skill for agent-to-agent transfers."""

from jclaw.skills.base import Skill, SkillContext
from jclaw.types import HandoffRequest, SkillExecutionError, ToolDefinition, ToolResult


class HandoffSkill(Skill):
    """Skill for handing off control from one agent to another."""

    skill_id = "handoff_to_agent"
    name = "Agent Handoff"
    description = "Transfer control to another agent"
    version = "1.0.0"

    def get_tools(self) -> list[ToolDefinition]:
        """Define the handoff_to_agent tool."""
        return [
            ToolDefinition(
                name="handoff_to_agent",
                description="Hand off to another agent to handle the conversation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "target_agent_id": {
                            "type": "string",
                            "description": "ID of the target agent",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the handoff",
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context to pass to the next agent",
                            "default": {},
                        },
                    },
                    "required": ["target_agent_id", "reason"],
                },
            )
        ]

    async def execute(
        self,
        tool_name: str,
        tool_input: dict,
        context: SkillContext,
    ) -> ToolResult:
        """Execute handoff.

        Returns a special ToolResult that the Orchestrator recognizes as a handoff.
        """
        if tool_name != "handoff_to_agent":
            raise SkillExecutionError(f"Unknown tool: {tool_name}")

        target_agent_id = tool_input.get("target_agent_id")
        reason = tool_input.get("reason", "")
        context_payload = tool_input.get("context", {})

        if not target_agent_id:
            raise SkillExecutionError("target_agent_id is required")

        # Create handoff request
        handoff_request = HandoffRequest(
            source_agent_id=context.agent_config.agent_id,
            target_agent_id=target_agent_id,
            reason=reason,
            context_payload=context_payload,
            preserve_history=True,
            mode="transfer",
        )

        # Return special ToolResult with handoff marker
        # The Orchestrator will recognize "__handoff__" and extract the request
        return ToolResult(
            tool_call_id="handoff_marker",
            output={
                "__handoff__": True,
                "request": handoff_request.model_dump(),
            },
            is_error=False,
        )
