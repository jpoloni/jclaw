"""Configuration management commands."""

import click
from jclaw.config import AgentsYamlLoader, get_settings


@click.group()
def config():
    """Configuration commands."""
    pass


@config.command()
def validate():
    """Validate agents.yaml and environment."""
    click.echo(click.style("\nValidating configuration...", bold=True))

    # Validate environment
    try:
        settings = get_settings()
        click.echo(click.style("✓", fg="green") + f" Environment settings loaded")
        click.echo(f"  ENV: {settings.jclaw_env}")
        click.echo(f"  LOG_LEVEL: {settings.log_level}")
        if settings.anthropic_api_key:
            click.echo(f"  ANTHROPIC_API_KEY: {'*' * 10}...")
        if settings.telegram_bot_token:
            click.echo(f"  TELEGRAM_BOT_TOKEN: {'*' * 10}...")
    except Exception as e:
        click.echo(click.style(f"✗ Environment validation failed: {e}", fg="red"))
        return

    # Validate agents.yaml
    try:
        loader = AgentsYamlLoader("config/agents.yaml")
        agents = loader.load()
        click.echo(click.style("✓", fg="green") + f" Agents configuration loaded ({len(agents)} agents)")

        # Validate cross-references
        agent_ids = {a.agent_id for a in agents}
        for agent in agents:
            for target in agent.handoff_targets:
                if target not in agent_ids:
                    click.echo(
                        click.style(f"✗ Agent '{agent.agent_id}' targets unknown agent '{target}'", fg="red")
                    )
                    return
            click.echo(f"  • {click.style(agent.agent_id, fg='blue')} → {', '.join(agent.handoff_targets) or 'none'}")

        click.echo(click.style("\n✓ Configuration is valid!", fg="green"))

    except FileNotFoundError:
        click.echo(click.style("✗ config/agents.yaml not found", fg="red"))
    except Exception as e:
        click.echo(click.style(f"✗ Configuration validation failed: {e}", fg="red"))
