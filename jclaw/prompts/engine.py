"""Prompt rendering engine with layer support."""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from jclaw.config import get_settings
from jclaw.llm import TokenCounter
from jclaw.prompts.models import RenderedPrompt
from jclaw.types import AgentConfig


class PromptContext:
    """Context for prompt rendering."""

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        channel: str,
        user_id: str,
        **kwargs: Any,
    ):
        """Initialize context."""
        self.session_id = session_id
        self.agent_id = agent_id
        self.channel = channel
        self.user_id = user_id
        self.extra = kwargs


class PromptEngine:
    """Renders prompts with layer-based composition."""

    def __init__(self, token_counter: TokenCounter):
        """Initialize engine.

        Args:
            token_counter: Token counter for budget management
        """
        self.token_counter = token_counter
        settings = get_settings()

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(settings.prompts_dir)),
            strict_undefined=StrictUndefined,
        )

    async def render(
        self,
        agent_config: AgentConfig,
        context: PromptContext,
    ) -> RenderedPrompt:
        """Render a prompt for an agent.

        Args:
            agent_config: Agent configuration
            context: Rendering context

        Returns:
            RenderedPrompt with content and metadata
        """
        prompt_text = ""

        # If system_prompt is a string, use it directly
        if isinstance(agent_config.system_prompt, str):
            prompt_text = agent_config.system_prompt
        # Otherwise it's a PromptRef - load from file
        else:
            try:
                template = self.jinja_env.get_template(agent_config.system_prompt.path)
                prompt_text = template.render(
                    agent_id=agent_config.agent_id,
                    channel=context.channel,
                    user_id=context.user_id,
                )
            except Exception:
                # Fallback to default
                prompt_text = f"You are {agent_config.agent_id}."

        # Count tokens
        token_count = self.token_counter.count(prompt_text)

        return RenderedPrompt(
            content=prompt_text,
            token_count=token_count,
            layers_used=["system"],
            template_version="1.0.0",
            rendered_at=datetime.utcnow(),
        )

    def invalidate_cache(self, path: str) -> None:
        """Invalidate template cache (for hot reload).

        Args:
            path: Template path that changed
        """
        if path in self.jinja_env.cache:
            del self.jinja_env.cache[path]
