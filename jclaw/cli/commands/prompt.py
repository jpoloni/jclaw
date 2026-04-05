"""Prompt management commands."""

import json

import click
from jclaw.config import AgentsYamlLoader
from jclaw.core import AgentRegistry
from jclaw.llm import MockTokenCounter
from jclaw.prompts import PromptContext, PromptEngine


@click.group()
def prompt():
    """Prompt commands."""
    pass


@prompt.command()
@click.argument("agent_id")
@click.option(
    "--channel",
    default="rest",
    help="Target channel (rest, telegram, whatsapp)",
)
@click.option("--vars", default="{}", help="JSON context variables")
def render(agent_id: str, channel: str, vars: str):
    """Render final system prompt for an agent."""
    try:
        loader = AgentsYamlLoader("config/agents.yaml")
        registry = AgentRegistry(loader)

        agent_config = registry.get_agent(agent_id)
        click.echo(click.style(f"\nAgent: {agent_config.name}", bold=True))
        click.echo("-" * 60)

        # Parse context vars
        try:
            context_vars = json.loads(vars)
        except json.JSONDecodeError:
            context_vars = {}

        # Render prompt
        engine = PromptEngine(MockTokenCounter())
        context = PromptContext(
            agent_id=agent_id,
            session_id="cli:render",
            user_id="cli_user",
            channel=channel,
            memory_facts=[],
            active_skills=[],
            metadata=context_vars,
        )

        rendered = None
        try:
            import asyncio

            rendered = asyncio.run(engine.render(agent_config, context))
        except Exception as e:
            click.echo(click.style(f"✗ Render failed: {e}", fg="red"))
            return

        click.echo(f"Model: {agent_config.llm_model}")
        click.echo(f"Context Window: {agent_config.context_window} tokens")
        click.echo()

        click.echo(click.style("System Prompt:", bold=True))
        click.echo("-" * 60)
        click.echo(rendered.content)
        click.echo()
        click.echo(click.style(f"Tokens: {rendered.token_count}", fg="cyan"))

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))


@prompt.command()
@click.argument("agent_id")
def diff(agent_id: str):
    """Show diff between prompt versions (stub in v0.1)."""
    click.echo(click.style("ℹ Prompt versioning is a v0.2 feature", fg="yellow"))
    click.echo("Store prompts in version control for now.")


@prompt.command()
@click.option("--suite", help="Path to test suite YAML file")
def test(suite: str):
    """Run prompt test suite (stub in v0.1)."""
    click.echo(click.style("ℹ Prompt testing framework is a v0.2 feature", fg="yellow"))
    click.echo("Create test assertions in tests/prompts/ directory")
