# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

### Installation & Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Copy environment template (required)
cp .env.example .env
```

### Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_orchestrator.py -v

# Run with coverage report
pytest tests/ --cov=jclaw --cov-report=html

# Lint and format check
ruff check jclaw/ tests/
ruff format jclaw/ tests/ --check

# Type checking
mypy jclaw/

# Start development server
jclaw serve --reload

# View agent configuration
jclaw agent list

# Inspect a single agent
jclaw agent inspect example

# Interactive chat playground
jclaw chat example

# Validate configuration
jclaw config validate
```

## Architecture Overview

### Core Concepts

**jClaw** is an async-native agent orchestration platform with these key abstractions:

1. **Agents** — Configured entities with LLM models, skills, guardrails, and handoff targets
2. **Sessions** — Persistent conversation state tied to `{channel}:{chat_id}`
3. **Message Processing Loop** — 12-step orchestrator that handles input guardrails → prompt rendering → LLM calls → skill execution → output guardrails → persistence
4. **Skills** — Pluggable tools with automatic discovery; handoff is a built-in skill
5. **Guardrails** — Input/output safety pipeline (PII detection, injection guard, content filtering)
6. **Prompts** — Jinja2-based templating engine with context injection and token budget enforcement
7. **Memory** — Multi-tier session storage: in-memory → Redis → PostgreSQL (v0.1 uses in-memory)
8. **Channels** — Adapters for different communication platforms (REST, Telegram)
9. **LLM Providers** — Pluggable with built-in Anthropic + Mock providers, circuit breaker pattern

### Layered Architecture

```
jclaw/
├── types/            # Shared Pydantic models (zero internal imports)
├── config/           # Settings, loaders, YAML parsing
├── db/              # SQLAlchemy ORM + Alembic migrations
├── observability/   # Event bus, structured logging
├── memory/          # SessionMemory ABC + implementations
├── llm/             # LLM providers, routing, circuit breaker
├── skills/          # Skill ABC + registry + executor
├── guardrails/      # Guardrail ABC + builtin rules + registry
├── prompts/         # Prompt engine with Jinja2 + context
├── core/            # Orchestrator, agent registry, handoff router
├── channels/        # Channel adapters (REST, Telegram)
├── server/          # FastAPI app factory + routers
├── dev/             # Developer tools (playground, inspector, etc)
└── cli/             # Click commands
```

## Key Design Patterns

### 1. Dependency Injection

All components receive dependencies via constructor, never instantiate internally. This ensures:
- Full testability with mocks
- Loose coupling between modules
- Clear dependency graphs

Example:
```python
orchestrator = Orchestrator(
    agent_registry=agent_registry,
    memory=memory,
    llm_router=llm_router,
    # ... other injected dependencies
)
```

### 2. ABC-Based Extensibility

Core abstractions (Skill, Guardrail, ChannelAdapter, LLMProvider, SessionMemory) are ABCs enabling pluggable implementations:
- **Skill**: Create custom tools by subclassing and registering in `SkillRegistry`
- **Guardrail**: Add safety rules by implementing guardrail pipeline
- **LLMProvider**: Add new LLM backends (OpenAI, etc) via `LLMProvider` ABC
- **SessionMemory**: Switch storage (Redis, PostgreSQL) without changing orchestrator

### 3. 12-Step Orchestrator Loop

The core message processing pipeline in `core/orchestrator.py`:
1. Acquire distributed lock (no-op in v0.1)
2. Load session, identify active agent
3. Input guardrail pipeline
4. Render prompt via `PromptEngine`
5. Build context window (token budget management)
6. Tool loop (max 10 iterations):
   - Call LLM via `LLMRouter`
   - Execute skills if tool_use
   - Detect handoff signal (`__handoff__` marker in ToolResult)
   - Repeat or break
7. Output guardrail pipeline
8. Persist messages to `SessionMemory`
9. Return `OutboundMessage`

### 4. Handoff Signal Detection

Handoffs don't use exceptions—`HandoffSkill.execute()` returns a `ToolResult` with special marker:
```python
output={"__handoff__": True, "request": HandoffRequest(...)}
```
The `SkillExecutor` detects this marker and returns a `HandoffRequest`, breaking the tool loop.

### 5. Token Budget Management

`ContextWindowManager` splits token budget:
- **Budget** = `context_window - max_tokens - 500` (safety margin)
- **Memory** = min(budget × 0.2, 2000 tokens)
- **History** = budget - memory_tokens

Messages are trimmed from tail to fit history budget (`_fit_messages()`).

### 6. Guardrail Pipeline

Guardrails execute sequentially with short-circuit on "block":
```
Input Guardrails → [PII Detector, Injection Guard, Topic Filter] → block?
                                                                    ↓
                                                              Output Guardrails
```
Blocked messages return early without LLM calls.

## Important Files & Patterns

### `types/` — Foundational Models

All other modules import from here. Zero circular imports.

- **messages.py**: `Message`, `InboundMessage`, `OutboundMessage`, `ToolCall`, `ToolResult`
- **agents.py**: `AgentConfig`, `GuardrailConfig`, `HandoffRequest`
- **events.py**: 20+ event types (MessageQueued, MessageSent, ToolCalled, etc.)
- **errors.py**: Exception hierarchy with custom error codes

### `config/loader.py` — YAML Configuration

`AgentsYamlLoader` parses `config/agents.yaml` with:
- `!include` tag support for splitting configs
- Cross-reference validation (handoff_targets exist)
- `PromptRef` conversion (string filename → PromptRef object)
- Pydantic validation on load

### `core/orchestrator.py` — Message Processing

12-step loop is here. Key methods:
- `async process(inbound: InboundMessage) -> OutboundMessage` — main entry point
- Inner method `_run_tool_loop()` — handles LLM + skill execution

### `prompts/engine.py` — Jinja2 Templating

- Supports both inline strings and file references
- Renders with context injection (memory facts, user info, etc.)
- Token budget per layer (configurable)

### `llm/circuit_breaker.py` — Fault Tolerance

Per-provider circuit breaker with states:
- **CLOSED** — normal operation
- **OPEN** — failures exceeded, fast-fail
- **HALF_OPEN** — limited retry attempts

Configuration in `LLMRouterConfig`.

### `skills/executor.py` — Tool Execution

`SkillExecutor.execute_all()` returns `(list[ToolResult], HandoffRequest | None)`:
- Filters tools by agent.skills list
- Detects handoff marker in results
- Captures errors as `ToolResult(is_error=True)`

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Tests for individual modules
│   ├── test_orchestrator.py
│   ├── test_memory.py
│   └── ...
└── integration/         # End-to-end scenario tests
    ├── test_full_turn.py
    └── ...
```

### Critical Fixtures (conftest.py)

- **agent_config** — Valid minimal AgentConfig
- **mock_llm** — MockLLMProvider with preset responses
- **inmemory_memory** — Fresh InMemorySessionMemory per test
- **skill_registry** — With HandoffSkill registered
- **orchestrator** — Fully wired with mocks

### Key Test Files

- **test_orchestrator.py** — Core 12-step loop, tool iteration, handoff detection
- **test_full_turn.py** — End-to-end scenarios: simple message, tool loop, guardrail block
- **test_llm_router.py** — Provider switching, fallback chains, circuit breaker
- **test_prompt_engine.py** — Context injection, token budgeting

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only (slower)
pytest tests/integration/ -v

# Specific marker
pytest -m "not slow" -v

# With coverage
pytest tests/ --cov=jclaw --cov-report=term-missing
```

## Database & Migrations

### Setup

Alembic migrations live in `migrations/versions/`. Current schema:

- **Session** — Conversation state, active agent, metadata
- **MessageRecord** — Persisted messages (optional in v0.1)
- **MemoryFact** — Vector embeddings for semantic search
- **HandoffLog** — Audit trail of agent transfers
- **PromptTemplate** — Cached/versioned prompts

### Running Migrations

```bash
# Auto-generate migration (after model changes)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Configuration & Environment

### .env File

Required variables (see `.env.example`):

```
JCLAW_ENV=development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/jclaw_dev
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWxyz
LOG_LEVEL=INFO
```

### agents.yaml

Agent definitions in `config/agents.yaml`:

```yaml
agents:
  - agent_id: example
    name: Example Agent
    description: An example agent
    llm_model: claude-3-5-sonnet-20241022
    llm_provider: anthropic
    temperature: 0.7
    max_tokens: 1024
    context_window: 8000
    skills: [handoff_to_agent]
    handoff_targets: [other_agent]
    system_prompt: "prompts/example_system.j2"
    guardrails:
      input: [pii_detector, injection_guard]
      output: [length_limiter]
```

## Common Tasks

### Adding a New Skill

1. Create class in `jclaw/skills/builtin/my_skill.py` inheriting from `Skill`
2. Implement `get_tools()` and `execute(context, tool_name, **kwargs)`
3. Register in agent config under `skills: [my_skill_id]`
4. Optionally add entry point in `pyproject.toml` for auto-discovery

### Adding a New Guardrail

1. Create class inheriting from `Guardrail` in `jclaw/guardrails/builtin/my_rule.py`
2. Implement `async check_input()` or `check_output()`
3. Return `GuardrailResult(action="block"|"warn", reason="...")`
4. Register in `GuardrailRegistry`
5. Reference in agent config

### Adding a New LLM Provider

1. Create provider class inheriting from `LLMProvider` in `jclaw/llm/my_provider.py`
2. Implement `async complete()`, `estimate_cost()`, token counting
3. Add to providers dict in `server/app.py` lifespan
4. Configure routing policy in `config/schemas.py`

### Debugging Message Processing

Enable trace logging:
```python
from jclaw.observability import set_trace_id
set_trace_id("debug-message-id")
# Messages logged to stdout with trace context
```

Inspect session state:
```bash
jclaw chat example  # REPL provides /memory, /trace commands
```

## Code Standards

### Imports

- Group: stdlib → third-party → jclaw internal
- Types go in `from typing import ...` or `from types import ...`
- Use `TYPE_CHECKING` for circular import avoidance

### Type Hints

- Enforce mypy strict mode (`strict = true` in pyproject.toml)
- Use `X | None` over `Optional[X]` (Python 3.10+)
- Generics in function signatures

### Async Patterns

- Never block the event loop (no synchronous I/O, subprocess calls)
- Use `asyncio.wait_for()` for timeouts
- Prefer `asyncio.gather()` over manual task management

### Error Handling

- Raise custom exceptions from `types/errors.py`
- Log before raising (via `structlog`)
- Return early for validation failures (don't nest exceptions)

### Testing

- Use fixtures for setup, assertions for checks
- Mock external APIs (`MockLLMProvider`, `fakeredis`, `respx`)
- Integration tests use real in-memory implementations

## Troubleshooting

### Import Errors

If you see circular imports:
1. Check that `types/` has no internal imports
2. Use `TYPE_CHECKING` for forward references
3. Move circular dependency to parameter injection

### Token Budget Issues

If context is truncated unexpectedly:
1. Check `ContextWindowManager.build_prompt()` formulas
2. Verify agent config `context_window` and `max_tokens`
3. Enable trace logging to see fitted message count

### Handoff Not Triggering

1. Verify `handoff_targets` in agent config includes target agent
2. Check skill execution returns `__handoff__` marker
3. Confirm agent has `handoff_to_agent` in skills list
4. Review orchestrator tool loop logic (max iterations check)

### Database Connection Errors

1. Ensure PostgreSQL is running (`psql -U postgres`)
2. Check `DATABASE_URL` in `.env`
3. Run `alembic upgrade head` to initialize schema

## References

- **Full Specification**: `specs/jClaw_Especificacao_Tecnica.md`
- **Implementation Plan**: See git history for phase-by-phase breakdown
- **Test Suite**: Start with `tests/integration/test_full_turn.py` for end-to-end flow
- **API Docs**: Served at `/docs` when server running (`jclaw serve --reload`)
