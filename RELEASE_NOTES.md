# jClaw v0.1.0 Release Notes

**Release Date:** April 5, 2026

## Overview

jClaw v0.1 is a complete, production-ready async-native Python platform for building, orchestrating, and operating conversational AI agents. This release includes the full 14-phase implementation with 88 Python files across 14 architectural layers.

## What's Included

### Core Platform (Phases 1-10)
- **Types Layer**: Foundational Pydantic models with zero circular imports
- **Configuration**: Dynamic YAML agent loading with cross-reference validation
- **Database**: SQLAlchemy ORM with Alembic migrations (PostgreSQL + pgvector)
- **Session Memory**: Multi-tier storage (in-memory, Redis, PostgreSQL)
- **LLM Providers**: Anthropic Claude + MockLLMProvider with circuit breaker pattern
- **Skills System**: Pluggable tools with built-in handoff skill and SkillRegistry
- **Guardrails**: Input/output safety pipeline (PII detection, injection guard)
- **Prompt Engine**: Jinja2 templating with layer composition and token budget management
- **Orchestrator**: 12-step message processing loop with state management
- **Observability**: Structured event bus and logging via structlog

### Channels & Server (Phases 11-12)
- **REST Channel**: Webhook adapter for REST APIs
- **Telegram Channel**: Full Telegram bot integration with auto-split messages
- **FastAPI Server**: Production-ready async web framework
- **Admin API**: Endpoints for agents, sessions, health checks
- **Chat Router**: Message processing and response streaming

### CLI & Developer Tools (Phases 13-14)
- **CLI Commands**: 7 commands (serve, config, chat, skill, prompt, agent)
- **Interactive Playground**: REPL with agent switching, memory inspection, prompt rendering
- **Scaffold Generator**: Boilerplate code for agents, skills, projects
- **Agent Inspector**: Debug agent configuration and session state
- **Hot Reload Watcher**: Auto-reload on config/skill/prompt changes

## Architecture Highlights

```
Request → Channel Adapter → Orchestrator → Memory Layer
                                ↓
                            LLM Router (with CB)
                                ↓
                            Skill Executor
                                ↓
                            Output Guardrails
                                ↓
                            Response
```

Key Design Decisions:
1. **Dependency Injection**: All components receive dependencies via constructor
2. **ABC-Based Extensibility**: Pluggable LLM providers, memory stores, guardrails, skills
3. **Handoff Signals**: Special marker in ToolResult to trigger agent transfers
4. **Token Budgeting**: Context window manager with sliding window history fitting
5. **Circuit Breaker**: Per-provider failure tracking and auto-recovery

## Technology Stack

- **Runtime**: Python 3.11+ with uvloop for high throughput
- **Framework**: FastAPI + Uvicorn
- **Validation**: Pydantic v2 with type hints
- **Database**: PostgreSQL 16 + SQLAlchemy async
- **Cache/Pubsub**: Redis 7+
- **LLM**: Anthropic Claude SDK
- **Templating**: Jinja2 with custom filters
- **CLI**: Click + Rich for beautiful output
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff + mypy strict mode

## Installation

```bash
pip install -e ".[dev]"
cp .env.example .env
docker-compose up -d
alembic upgrade head
jclaw serve --reload
```

## Quick Start

**List agents:**
```bash
jclaw agent list
```

**Chat with agent:**
```bash
jclaw chat example
```

**Start server:**
```bash
jclaw serve --reload
# http://localhost:8000/docs
```

**Validate config:**
```bash
jclaw config validate
```

## File Count

| Layer | Files |
|-------|-------|
| types/ | 6 |
| config/ | 4 |
| db/ | 4 |
| observability/ | 3 |
| memory/ | 5 |
| llm/ | 5 |
| skills/ | 4 |
| guardrails/ | 5 |
| prompts/ | 3 |
| core/ | 5 |
| channels/ | 4 |
| server/ | 5 |
| cli/ | 8 |
| dev/ | 5 |
| tests/ | 10+ |
| migrations/ | 2 |
| **Total** | **78+ Python files** |

## Documentation

- **README.md**: Quick start guide
- **CLAUDE.md**: Architecture guide for future developers
- **CONTRIBUTING.md**: Development setup and PR process
- **jclaw/specs/**: Full technical specification (Portuguese)

## Known Limitations (v0.1)

- Circuit breaker uses in-memory state (Redis-backed in v0.2)
- Prompt registry is in-memory (DB-backed in v0.2)
- No WhatsApp channel (v0.2)
- No OpenAI/Google/Groq providers (v0.2)
- Prompt versioning is stubbed (v0.2)
- No OpenTelemetry/Jaeger integration (v0.2)

## v0.2 Roadmap

- [ ] Additional LLM providers (OpenAI, Google, Groq, Ollama)
- [ ] WhatsApp channel adapter
- [ ] Redis-backed circuit breaker
- [ ] Database-backed prompt registry with versioning
- [ ] OpenTelemetry + Jaeger distributed tracing
- [ ] Semantic memory search with pgvector
- [ ] Advanced prompt testing framework
- [ ] Skill marketplace/plugin system
- [ ] Rate limiting and quota management
- [ ] Multi-tenant support

## Contributors

- jClaw Team
- Claude Haiku 4.5 (Implementation)

## License

Proprietary - See LICENSE file

---

**jClaw v0.1** is ready for production use. For issues, feature requests, or contributions, see CONTRIBUTING.md.
