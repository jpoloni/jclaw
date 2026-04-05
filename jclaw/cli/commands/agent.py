"""Agent management commands."""

import click

from jclaw.config import AgentsYamlLoader


@click.group()
def agent():
    """Agent commands."""
    pass


@agent.command()
def list():
    """List all registered agents."""
    try:
        loader = AgentsYamlLoader("config/agents.yaml")
        agents = loader.load()

        click.echo(click.style("\nRegistered Agents:", bold=True))
        click.echo("-" * 60)

        for agent in agents:
            click.echo(
                f"  {click.style(agent.agent_id, fg='blue')} - {agent.name}"
            )
            click.echo(f"    Model: {agent.llm_model}")
            click.echo(f"    Skills: {', '.join(agent.skills) or 'None'}")
            click.echo()

        click.echo(f"Total: {len(agents)} agents")

    except FileNotFoundError:
        click.echo(click.style("✗ config/agents.yaml not found", fg="red"))


@agent.command()
@click.argument("agent_id")
def inspect(agent_id: str):
    """Inspect an agent."""
    try:
        loader = AgentsYamlLoader("config/agents.yaml")
        agents = loader.load()
        agent = next((a for a in agents if a.agent_id == agent_id), None)

        if not agent:
            click.echo(click.style(f"✗ Agent '{agent_id}' not found", fg="red"))
            return

        click.echo(click.style(f"\nAgent: {agent.name}", bold=True))
        click.echo("-" * 60)
        click.echo(f"ID: {agent.agent_id}")
        click.echo(f"Description: {agent.description}")
        click.echo(f"Model: {agent.llm_model} ({agent.llm_provider})")
        click.echo(f"Temperature: {agent.temperature}")
        click.echo(f"Max Tokens: {agent.max_tokens}")
        click.echo(f"Skills: {', '.join(agent.skills) or 'None'}")
        click.echo(f"Handoff Targets: {', '.join(agent.handoff_targets) or 'None'}")
        click.echo()

    except FileNotFoundError:
        click.echo(click.style("✗ config/agents.yaml not found", fg="red"))
