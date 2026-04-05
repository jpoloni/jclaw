"""Interactive chat playground."""

import asyncio
import time
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from jclaw.channels import RESTChannelAdapter
from jclaw.config import AgentsYamlLoader, get_settings
from jclaw.core import AgentRegistry, Orchestrator
from jclaw.guardrails import GuardrailRegistry
from jclaw.llm import AnthropicProvider, LLMRouter, MockLLMProvider
from jclaw.memory import InMemorySessionMemory
from jclaw.observability import configure_logging
from jclaw.prompts import PromptContext, PromptEngine
from jclaw.skills import SkillExecutor, SkillRegistry
from jclaw.types import InboundMessage
from jclaw.llm import MockTokenCounter


@click.command()
@click.argument("agent_id", required=False, default="example")
@click.option("--channel", default="playground", help="Channel name")
@click.option("--user-id", default="cli_user", help="User ID")
def chat(agent_id: str, channel: str, user_id: str):
    """Interactive chat with an agent (playground)."""
    asyncio.run(_run_chat(agent_id, channel, user_id))


async def _run_chat(agent_id: str, channel: str, user_id: str):
    """Run interactive chat session."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level)

    # Setup orchestrator
    try:
        loader = AgentsYamlLoader("config/agents.yaml")
        agent_registry = AgentRegistry(loader)
        await agent_registry.load()
    except Exception:
        click.echo(click.style("✗ Failed to load agents.yaml", fg="red"))
        return

    try:
        agent_registry.get_agent(agent_id)
    except Exception:
        click.echo(click.style(f"✗ Agent '{agent_id}' not found", fg="red"))
        return

    memory = InMemorySessionMemory()
    providers = {
        "anthropic": AnthropicProvider(api_key=settings.anthropic_api_key or ""),
        "mock": MockLLMProvider(echo_mode=True),
    }
    llm_router = LLMRouter(providers)
    skill_registry = SkillRegistry()
    skill_executor = SkillExecutor(skill_registry)
    guardrail_registry = GuardrailRegistry()
    prompt_engine = PromptEngine(MockTokenCounter())

    orchestrator = Orchestrator(
        agent_registry=agent_registry,
        memory=memory,
        llm_router=llm_router,
        skill_executor=skill_executor,
        prompt_engine=prompt_engine,
        guardrail_registry=guardrail_registry,
        token_counter=MockTokenCounter(),
    )

    # Setup session
    session_id = f"{channel}:playground"
    await memory.set_metadata(session_id, "active_agent_id", agent_id)
    chat_id = "playground"

    # Setup prompt history
    history_file = Path.home() / ".jclaw_chat_history"
    session = PromptSession(history=FileHistory(str(history_file)))

    click.echo(click.style(f"\n🤖 jClaw Chat Playground", bold=True))
    click.echo(f"Agent: {click.style(agent_id, fg='blue')}")
    click.echo(f"Channel: {channel}")
    click.echo(click.style("Commands: /switch /reset /memory /trace /prompt /q", fg="cyan"))
    click.echo("-" * 60 + "\n")

    while True:
        try:
            text = await session.prompt_async("You: ")

            if not text.strip():
                continue

            # Handle commands
            if text.startswith("/"):
                await _handle_command(text, agent_id, memory, session_id, prompt_engine, agent_registry, orchestrator)
                continue

            # Process message
            start = time.time()
            inbound = InboundMessage(
                message_id=str(time.time()),
                text=text,
                user_id=user_id,
                chat_id=chat_id,
                channel=channel,
            )

            try:
                outbound = await orchestrator.process(inbound)
                elapsed = time.time() - start

                click.echo(f"\n{click.style('Agent:', fg='blue')} {outbound.text}")
                click.echo(f"{click.style('⏱', fg='cyan')} {elapsed:.2f}s\n")
            except Exception as e:
                click.echo(click.style(f"✗ Error: {e}", fg="red"))

        except KeyboardInterrupt:
            click.echo("\nGoodbye! 👋")
            break
        except EOFError:
            click.echo("\nGoodbye! 👋")
            break


async def _handle_command(
    text: str,
    current_agent: str,
    memory,
    session_id: str,
    prompt_engine,
    agent_registry,
    orchestrator,
):
    """Handle playground commands."""
    parts = text.split(maxsplit=1)
    cmd = parts[0]

    if cmd == "/q":
        click.echo("Goodbye! 👋")
        raise EOFError

    elif cmd == "/reset":
        await memory.expire(session_id)
        click.echo(click.style("✓ Session reset", fg="green") + "\n")

    elif cmd == "/memory":
        messages = await memory.get_messages(session_id)
        metadata = await memory.get_all_metadata(session_id)
        click.echo(click.style("\n📋 Session Memory:", bold=True))
        click.echo(f"Messages: {len(messages)}")
        click.echo(f"Metadata: {metadata}")
        click.echo()

    elif cmd == "/trace":
        click.echo(click.style("\n📊 Last Turn Trace:", bold=True))
        click.echo("(Full tracing dashboard in v0.2)")
        click.echo()

    elif cmd == "/prompt":
        try:
            agent_config = agent_registry.get_agent(current_agent)
            context = PromptContext(
                agent_id=current_agent,
                session_id=session_id,
                user_id="cli_user",
                channel="playground",
                memory_facts=[],
                active_skills=agent_config.skills,
                metadata={},
            )
            rendered = await prompt_engine.render(agent_config, context)
            click.echo(click.style("\n📝 System Prompt:", bold=True))
            click.echo(rendered.content)
            click.echo(click.style(f"\nTokens: {rendered.token_count}", fg="cyan") + "\n")
        except Exception as e:
            click.echo(click.style(f"✗ Error: {e}", fg="red") + "\n")

    elif cmd == "/switch":
        if len(parts) < 2:
            click.echo(click.style("Usage: /switch <agent_id>", fg="yellow") + "\n")
            return
        new_agent = parts[1]
        try:
            agent_registry.get_agent(new_agent)
            await memory.set_metadata(session_id, "active_agent_id", new_agent)
            click.echo(click.style(f"✓ Switched to {new_agent}", fg="green") + "\n")
        except Exception:
            click.echo(click.style(f"✗ Agent '{new_agent}' not found", fg="red") + "\n")

    else:
        click.echo(click.style(f"Unknown command: {cmd}", fg="yellow") + "\n")
