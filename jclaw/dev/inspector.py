"""Inspector for debugging agents and sessions."""

from dataclasses import dataclass
from typing import Any

from jclaw.config import AgentsYamlLoader
from jclaw.core import AgentRegistry
from jclaw.memory import SessionMemory
from jclaw.types import AgentConfig, Message


@dataclass
class AgentInspection:
    """Inspection result for an agent."""

    agent_id: str
    name: str
    description: str
    model: str
    provider: str
    temperature: float
    max_tokens: int
    context_window: int
    skills: list[str]
    handoff_targets: list[str]
    guardrails: dict[str, Any]


@dataclass
class SessionInspection:
    """Inspection result for a session."""

    session_id: str
    active_agent_id: str | None
    message_count: int
    messages: list[Message]
    metadata: dict[str, Any]


class AgentInspector:
    """Inspector for agents and sessions."""

    def __init__(self, agents_yaml: str = "config/agents.yaml"):
        """Initialize inspector.

        Args:
            agents_yaml: Path to agents configuration
        """
        self.agents_yaml = agents_yaml
        self.loader = AgentsYamlLoader(agents_yaml)
        self.registry = AgentRegistry(self.loader)

    async def inspect_agent(self, agent_id: str) -> AgentInspection:
        """Inspect agent configuration.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentInspection with full agent details
        """
        await self.registry.load()
        agent_config = self.registry.get_agent(agent_id)

        return AgentInspection(
            agent_id=agent_config.agent_id,
            name=agent_config.name,
            description=agent_config.description,
            model=agent_config.llm_model,
            provider=agent_config.llm_provider,
            temperature=agent_config.temperature,
            max_tokens=agent_config.max_tokens,
            context_window=agent_config.context_window,
            skills=agent_config.skills,
            handoff_targets=agent_config.handoff_targets,
            guardrails=agent_config.guardrails.model_dump() if agent_config.guardrails else {},
        )

    async def inspect_session(
        self, session_id: str, memory: SessionMemory
    ) -> SessionInspection:
        """Inspect session state.

        Args:
            session_id: Session identifier
            memory: Session memory implementation

        Returns:
            SessionInspection with session details
        """
        messages = await memory.get_messages(session_id)
        metadata = await memory.get_all_metadata(session_id)
        active_agent_id = metadata.get("active_agent_id")

        return SessionInspection(
            session_id=session_id,
            active_agent_id=active_agent_id,
            message_count=len(messages),
            messages=messages,
            metadata=metadata,
        )

    async def list_agents(self) -> list[AgentInspection]:
        """List all agents.

        Returns:
            List of AgentInspection for all configured agents
        """
        await self.registry.load()
        agents = self.registry.list_agents()

        inspections = []
        for agent_config in agents:
            inspections.append(
                AgentInspection(
                    agent_id=agent_config.agent_id,
                    name=agent_config.name,
                    description=agent_config.description,
                    model=agent_config.llm_model,
                    provider=agent_config.llm_provider,
                    temperature=agent_config.temperature,
                    max_tokens=agent_config.max_tokens,
                    context_window=agent_config.context_window,
                    skills=agent_config.skills,
                    handoff_targets=agent_config.handoff_targets,
                    guardrails=agent_config.guardrails.model_dump() if agent_config.guardrails else {},
                )
            )

        return inspections
