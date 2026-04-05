# jClaw v0.1

AI Agent Orchestration Platform — Async-native Python framework for building, orchestrating, and operating conversational AI agents.

## Features

- **Multi-LLM Support**: Anthropic, OpenAI, Google, Groq, Ollama (pluggable)
- **Agent Orchestration**: 12-step message processing loop with state management
- **Session Memory**: Multi-tier (in-memory → Redis → PostgreSQL)
- **Skills System**: Pluggable tools with automatic tool discovery
- **Channel Adapters**: Telegram, WhatsApp, REST, WebSocket
- **Prompt Engine**: Jinja2-based 9-layer prompt composition
- **Guardrails**: Input/output safety checks (PII, injection, content)
- **Handoffs**: Agent-to-agent transfers with context preservation
- **Observability**: Structured logging + event system

## Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_types.py -v

# Run with coverage
pytest tests/ --cov=jclaw
```

### Start Development Server

```bash
# Server starts at http://localhost:8000
jclaw serve --reload
```

### Interactive Playground

```bash
# Chat with an agent
jclaw chat example --channel playground
```

## Project Structure

```
jclaw/
├── jclaw/
│   ├── types/           # Shared Pydantic models
│   ├── config/          # Configuration & settings
│   ├── db/              # Database models & migrations
│   ├── observability/   # Logging & events
│   ├── memory/          # Session memory implementations
│   ├── llm/             # LLM providers & routing
│   ├── skills/          # Skill system
│   ├── guardrails/      # Safety checks
│   ├── prompts/         # Prompt engine
│   ├── core/            # Orchestrator
│   ├── channels/        # Channel adapters
│   ├── server/          # FastAPI server
│   ├── dev/             # Developer tools
│   └── cli/             # Click CLI
├── tests/               # Test suite
├── migrations/          # Alembic database migrations
├── prompts/             # Jinja2 prompt templates
├── templates/           # Code generation templates
└── config/              # Agent configurations
```

## Documentation

- See `/home/jean/dev2/CLAUDE.md` for architecture overview
- See `jclaw/specs/jClaw_Especificacao_Tecnica.md` for full technical specification

## Version

**v0.1.0** (current implementation)

- Core orchestrator with 12-step message loop
- Anthropic + Mock LLM providers
- InMemory + Redis session memory
- REST + Telegram channels
- Complete prompt engine with layers
- Skill system with HandoffSkill
- Guardrails with PII/injection detection
- CLI with playground, scaffold generator
- Full test suite

## License

Proprietary
