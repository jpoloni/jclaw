"""Agent registry and management."""

from jclaw.config import AgentsYamlLoader
from jclaw.types import AgentConfig, AgentNotFoundError


class AgentRegistry:
    """Registry for managing agents."""

    def __init__(self, loader: AgentsYamlLoader):
        """Initialize registry.

        Args:
            loader: AgentsYamlLoader instance
        """
        self.loader = loader
        self._agents: dict[str, AgentConfig] = {}
        self._loaded = False

    async def load(self) -> None:
        """Load agents from configuration."""
        agents = self.loader.load()
        self._agents = {agent.agent_id: agent for agent in agents}
        self._loaded = True

    async def reload(self) -> None:
        """Reload agents from configuration."""
        await self.load()

    def get_agent(self, agent_id: str) -> AgentConfig:
        """Get agent configuration.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentConfig

        Raises:
            AgentNotFoundError: If agent not found
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        return self._agents[agent_id]

    def list_agents(self) -> list[AgentConfig]:
        """Get all agents.

        Returns:
            List of AgentConfig
        """
        return list(self._agents.values())

    def list_agent_ids(self) -> list[str]:
        """Get all agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())

    def get_first_agent(self) -> AgentConfig | None:
        """Get first agent (entry point).

        Returns:
            First agent or None
        """
        agents = self.list_agents()
        return agents[0] if agents else None
