"""Playground for interactive agent development and testing."""

import time
from dataclasses import dataclass, field
from typing import Any

from jclaw.channels import RESTChannelAdapter
from jclaw.config import AgentsYamlLoader
from jclaw.core import AgentRegistry, Orchestrator
from jclaw.guardrails import GuardrailRegistry
from jclaw.llm import LLMRouter, MockTokenCounter, MockLLMProvider
from jclaw.memory import InMemorySessionMemory
from jclaw.prompts import PromptEngine
from jclaw.skills import SkillExecutor, SkillRegistry
from jclaw.types import InboundMessage, OutboundMessage


@dataclass
class PlaygroundResponse:
    """Response from playground turn."""

    text: str
    agent_id: str
    latency_ms: float
    message_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Playground:
    """Playground for testing agents without external services."""

    def __init__(self, agents_yaml: str = "config/agents.yaml"):
        """Initialize playground.

        Args:
            agents_yaml: Path to agents configuration file
        """
        self.agents_yaml = agents_yaml
        self.orchestrator: Orchestrator | None = None
        self.agent_registry: AgentRegistry | None = None
        self.memory: InMemorySessionMemory | None = None
        self.session_id = "playground:session"
        self.user_id = "playground_user"
        self.chat_id = "playground"
        self.channel = "playground"

    async def initialize(self):
        """Initialize playground components."""
        # Load agents
        loader = AgentsYamlLoader(self.agents_yaml)
        self.agent_registry = AgentRegistry(loader)
        await self.agent_registry.load()

        # Setup memory
        self.memory = InMemorySessionMemory()
        first_agent = self.agent_registry.get_first_agent()
        if first_agent:
            await self.memory.set_metadata(self.session_id, "active_agent_id", first_agent.agent_id)

        # Setup LLM providers
        providers = {
            "mock": MockLLMProvider(echo_mode=True),
        }
        llm_router = LLMRouter(providers)

        # Setup skills
        skill_registry = SkillRegistry()
        skill_executor = SkillExecutor(skill_registry)

        # Setup guardrails
        guardrail_registry = GuardrailRegistry()

        # Setup prompts
        prompt_engine = PromptEngine(MockTokenCounter())

        # Create orchestrator
        from jclaw.core import HandoffRouter

        self.orchestrator = Orchestrator(
            agent_registry=self.agent_registry,
            memory=self.memory,
            llm_router=llm_router,
            skill_executor=skill_executor,
            prompt_engine=prompt_engine,
            guardrail_registry=guardrail_registry,
            token_counter=MockTokenCounter(),
            handoff_router=HandoffRouter(),
        )

    async def send_message(self, text: str, agent_id: str | None = None) -> PlaygroundResponse:
        """Send message to agent.

        Args:
            text: User message
            agent_id: Target agent (uses active if not specified)

        Returns:
            PlaygroundResponse with agent response
        """
        if not self.orchestrator or not self.memory:
            await self.initialize()

        start = time.time()
        message_id = f"msg_{start}"

        # Set active agent if specified
        if agent_id:
            await self.memory.set_metadata(self.session_id, "active_agent_id", agent_id)
        else:
            agent_id = await self.memory.get_metadata(self.session_id, "active_agent_id")

        # Process message
        inbound = InboundMessage(
            message_id=message_id,
            text=text,
            user_id=self.user_id,
            chat_id=self.chat_id,
            channel=self.channel,
        )

        try:
            outbound = await self.orchestrator.process(inbound)
            elapsed = time.time() - start

            return PlaygroundResponse(
                text=outbound.text or "",
                agent_id=agent_id,
                latency_ms=elapsed * 1000,
                message_id=message_id,
                error=None,
            )
        except Exception as e:
            elapsed = time.time() - start
            return PlaygroundResponse(
                text="",
                agent_id=agent_id,
                latency_ms=elapsed * 1000,
                message_id=message_id,
                error=str(e),
            )

    async def reset(self):
        """Reset session state."""
        if self.memory:
            await self.memory.expire(self.session_id)

    async def get_memory(self) -> dict[str, Any]:
        """Get current session memory state."""
        if not self.memory:
            return {}

        messages = await self.memory.get_messages(self.session_id)
        metadata = await self.memory.get_all_metadata(self.session_id)

        return {
            "message_count": len(messages),
            "messages": [
                {"role": m.role, "text": m.text[:100]} for m in messages
            ],
            "metadata": metadata,
        }

    async def switch_agent(self, agent_id: str):
        """Switch active agent."""
        if not self.agent_registry:
            await self.initialize()

        self.agent_registry.get_agent(agent_id)  # Validate
        await self.memory.set_metadata(self.session_id, "active_agent_id", agent_id)
