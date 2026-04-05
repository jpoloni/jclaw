"""jClaw CLI - Command-line interface."""

import click

from jclaw.cli.commands import agent, chat, config, prompt, serve, skill


@click.group()
def cli():
    """jClaw - AI Agent Orchestration Platform."""
    pass


# Register command groups
cli.add_command(agent.agent)
cli.add_command(config.config)
cli.add_command(chat.chat)
cli.add_command(serve.serve)
cli.add_command(skill.skill)
cli.add_command(prompt.prompt)


if __name__ == "__main__":
    cli()
