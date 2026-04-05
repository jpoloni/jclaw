"""Code scaffold generator."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeneratedFile:
    """Generated file with content."""

    path: str
    content: str


class ScaffoldGenerator:
    """Generate boilerplate code for agents, skills, and projects."""

    @staticmethod
    def agent_scaffold(agent_id: str) -> list[GeneratedFile]:
        """Generate agent scaffold.

        Args:
            agent_id: Agent identifier

        Returns:
            List of GeneratedFile with agent boilerplate
        """
        # YAML config
        yaml_content = f"""
# Agent: {agent_id}
agents:
  - agent_id: {agent_id}
    name: {agent_id.replace('_', ' ').title()}
    description: "TODO: Describe this agent"
    llm_model: claude-3-5-sonnet-20241022
    llm_provider: anthropic
    temperature: 0.7
    max_tokens: 1024
    context_window: 8000
    skills: [handoff_to_agent]
    handoff_targets: []
    system_prompt: "prompts/{agent_id}/system.j2"
    guardrails:
      input: [pii_detector, injection_guard]
      output: [length_limiter]
""".strip()

        # System prompt template
        prompt_content = """# System Prompt for {{ agent_id }}

You are {{ agent_name }}.

## Role
TODO: Describe your role and responsibilities

## Skills
You have access to these tools:
{% for skill in active_skills %}
- {{ skill }}
{% endfor %}

## Instructions
TODO: Add specific instructions
"""

        return [
            GeneratedFile(
                path=f"config/{agent_id}.yaml",
                content=yaml_content,
            ),
            GeneratedFile(
                path=f"prompts/{agent_id}/system.j2",
                content=prompt_content,
            ),
        ]

    @staticmethod
    def skill_scaffold(skill_id: str) -> GeneratedFile:
        """Generate skill scaffold.

        Args:
            skill_id: Skill identifier

        Returns:
            GeneratedFile with skill boilerplate
        """
        class_name = "".join(x.title() for x in skill_id.split("_"))

        content = f'''"""{{skill_id}} skill."""

from jclaw.skills import Skill, SkillContext
from jclaw.types import ToolDefinition, ToolResult


class {class_name}Skill(Skill):
    """{{skill_id}} skill."""

    async def get_tools(self, ctx: SkillContext) -> list[ToolDefinition]:
        """Define available tools."""
        return [
            ToolDefinition(
                name="{skill_id}",
                description="TODO: Add description",
                input_schema={{
                    "type": "object",
                    "properties": {{}},
                    "required": [],
                }},
            )
        ]

    async def execute(
        self, tool_name: str, tool_input: dict, ctx: SkillContext
    ) -> ToolResult:
        """Execute the tool."""
        if tool_name == "{skill_id}":
            # TODO: Implement tool logic
            return ToolResult(output={{"result": "TODO"}})

        return ToolResult(output={{}}, is_error=True, error="Unknown tool")
'''

        return GeneratedFile(
            path=f"jclaw/skills/builtin/{skill_id}/skill.py",
            content=content,
        )

    @staticmethod
    def project_scaffold(project_name: str) -> list[GeneratedFile]:
        """Generate complete project structure.

        Args:
            project_name: Project name

        Returns:
            List of GeneratedFile for project setup
        """
        files = [
            GeneratedFile(
                path=".env.example",
                content="""JCLAW_ENV=development
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/jclaw_dev
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=
LOG_LEVEL=INFO
""",
            ),
            GeneratedFile(
                path="docker-compose.yaml",
                content="""version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: jclaw_dev
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
""",
            ),
            GeneratedFile(
                path="config/agents.yaml",
                content="""# Agent definitions
agents:
  - agent_id: example
    name: Example Agent
    description: An example agent for testing
    llm_model: claude-3-5-sonnet-20241022
    llm_provider: anthropic
    temperature: 0.7
    max_tokens: 1024
    context_window: 8000
    skills: [handoff_to_agent]
    handoff_targets: []
    system_prompt: "prompts/example/system.j2"
    guardrails:
      input: [pii_detector, injection_guard]
      output: [length_limiter]
""",
            ),
            GeneratedFile(
                path="prompts/example/system.j2",
                content="""You are a helpful AI assistant.

You have access to the following tools:
{% for skill in active_skills %}
- {{ skill }}
{% endfor %}

Be concise, helpful, and accurate in your responses.
""",
            ),
            GeneratedFile(
                path="README.md",
                content=f"""# {project_name}

AI Agent Orchestration project built with jClaw.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Setup environment
cp .env.example .env

# Run development server
jclaw serve --reload
```

## Commands

- `jclaw agent list` — List agents
- `jclaw chat example` — Interactive chat
- `jclaw config validate` — Validate config

## Documentation

See CLAUDE.md for architecture guide.
""",
            ),
        ]

        return files
