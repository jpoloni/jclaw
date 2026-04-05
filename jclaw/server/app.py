"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from jclaw.channels import RESTChannelAdapter, TelegramChannelAdapter
from jclaw.config import get_settings
from jclaw.core import AgentRegistry, HandoffRouter, Orchestrator
from jclaw.db import init_db
from jclaw.guardrails import GuardrailRegistry
from jclaw.llm import AnthropicProvider, LLMRouter, MockLLMProvider
from jclaw.memory import InMemorySessionMemory
from jclaw.observability import configure_logging
from jclaw.prompts import PromptEngine
from jclaw.skills import SkillExecutor, SkillRegistry
from jclaw.config import AgentsYamlLoader


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI application instance
    """
    settings = get_settings()

    # Configure logging
    configure_logging(log_level=settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan - startup and shutdown."""
        # Startup
        await init_db()

        # Initialize memory
        memory = InMemorySessionMemory()

        # Initialize LLM providers
        providers = {
            "anthropic": AnthropicProvider(api_key=settings.anthropic_api_key),
            "mock": MockLLMProvider(echo_mode=True),
        }
        llm_router = LLMRouter(providers)

        # Initialize skill registry and executor
        skill_registry = SkillRegistry()
        skill_executor = SkillExecutor(skill_registry)

        # Initialize guardrail registry
        guardrail_registry = GuardrailRegistry()

        # Initialize prompt engine
        from jclaw.llm import MockTokenCounter

        prompt_engine = PromptEngine(MockTokenCounter())

        # Initialize agent registry
        loader = AgentsYamlLoader("config/agents.yaml")
        agent_registry = AgentRegistry(loader)
        try:
            await agent_registry.load()
        except Exception:
            # If no agents.yaml, create empty registry
            pass

        # Initialize orchestrator
        orchestrator = Orchestrator(
            agent_registry=agent_registry,
            memory=memory,
            llm_router=llm_router,
            skill_executor=skill_executor,
            prompt_engine=prompt_engine,
            guardrail_registry=guardrail_registry,
            token_counter=MockTokenCounter(),
            handoff_router=HandoffRouter(),
        )

        # Store in app state
        app.state.orchestrator = orchestrator
        app.state.memory = memory
        app.state.agent_registry = agent_registry
        app.state.rest_channel = RESTChannelAdapter()
        app.state.telegram_channel = TelegramChannelAdapter(
            bot_token=settings.telegram_bot_token or "test_token",
            webhook_secret=settings.telegram_webhook_secret or "",
        )

        yield

        # Shutdown
        pass

    app = FastAPI(
        title="jClaw",
        description="AI Agent Orchestration Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Import and register routers
    from jclaw.server.routers import admin, chat, webhooks

    app.include_router(chat.router)
    app.include_router(webhooks.router)
    app.include_router(admin.router)

    return app
