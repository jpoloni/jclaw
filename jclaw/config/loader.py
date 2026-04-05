"""Configuration loader for agents.yaml files."""

from pathlib import Path
from typing import Any

import yaml

from jclaw.types import AgentConfig, ConfigValidationError, PromptRef


class AgentsYamlLoader:
    """Load and parse agents.yaml files."""

    def __init__(self, config_path: str | Path = "config/agents.yaml"):
        """Initialize loader.

        Args:
            config_path: Path to agents.yaml file
        """
        self.config_path = Path(config_path)

    def load(self) -> list[AgentConfig]:
        """Load agents from YAML file.

        Returns:
            List of parsed AgentConfig objects

        Raises:
            ConfigValidationError: If config is invalid
        """
        if not self.config_path.exists():
            raise ConfigValidationError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in {self.config_path}: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Error reading {self.config_path}: {e}")

        if not isinstance(data, dict) or "agents" not in data:
            raise ConfigValidationError("agents.yaml must have 'agents' root key")

        agents = data["agents"]
        if not isinstance(agents, list):
            raise ConfigValidationError("'agents' must be a list")

        parsed_agents = []
        for i, agent_data in enumerate(agents):
            try:
                agent_config = self._parse_agent(agent_data)
                parsed_agents.append(agent_config)
            except Exception as e:
                raise ConfigValidationError(
                    f"Error parsing agent {i}: {e}"
                )

        # Validate cross-references
        self._validate_cross_references(parsed_agents)

        return parsed_agents

    def _parse_agent(self, data: dict[str, Any]) -> AgentConfig:
        """Parse a single agent configuration.

        Args:
            data: Agent configuration dict

        Returns:
            Parsed AgentConfig

        Raises:
            ConfigValidationError: If agent config is invalid
        """
        # Convert system_prompt to PromptRef if it's a path
        system_prompt = data.get("system_prompt")
        if isinstance(system_prompt, str):
            if system_prompt.endswith(".j2"):
                system_prompt = PromptRef(path=system_prompt)

        data = {**data, "system_prompt": system_prompt}
        return AgentConfig(**data)

    def _validate_cross_references(self, agents: list[AgentConfig]) -> None:
        """Validate that all cross-references are valid.

        Args:
            agents: List of agents to validate

        Raises:
            ConfigValidationError: If cross-references are invalid
        """
        agent_ids = {agent.agent_id for agent in agents}

        for agent in agents:
            # Check handoff_targets exist
            for target in agent.handoff_targets:
                if target not in agent_ids:
                    raise ConfigValidationError(
                        f"Agent '{agent.agent_id}' references non-existent "
                        f"handoff target '{target}'"
                    )


class AgentConfigValidator:
    """Validate agent configurations."""

    @staticmethod
    def validate_agent(agent: AgentConfig) -> list[str]:
        """Validate an agent configuration.

        Args:
            agent: AgentConfig to validate

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        # Check if system prompt is empty
        if isinstance(agent.system_prompt, str) and not agent.system_prompt.strip():
            warnings.append(f"Agent '{agent.agent_id}' has empty system_prompt")

        # Check if at least one skill or no skills
        if agent.skills is None:
            warnings.append(f"Agent '{agent.agent_id}' has None skills (should be list)")

        # Check temperature is reasonable
        if agent.temperature > 1.5:
            warnings.append(
                f"Agent '{agent.agent_id}' has high temperature ({agent.temperature})"
            )

        return warnings
