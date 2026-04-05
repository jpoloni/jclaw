"""Skill management commands."""

import click
from jclaw.skills import SkillRegistry


@click.group()
def skill():
    """Skill commands."""
    pass


@skill.command()
def list():
    """List available skills."""
    registry = SkillRegistry()

    click.echo(click.style("\nAvailable Skills:", bold=True))
    click.echo("-" * 60)

    # Built-in skills
    builtin_skills = [
        ("handoff_to_agent", "Transfer conversation to another agent"),
    ]

    for skill_id, description in builtin_skills:
        click.echo(f"  {click.style(skill_id, fg='blue')} — {description}")

    click.echo()
    click.echo(f"Total: {len(builtin_skills)} skills")
    click.echo(click.style("\n💡 Tip: Use 'jclaw skill create' to build custom skills", fg="cyan"))


@skill.command()
@click.argument("skill_id")
def create(skill_id: str):
    """Create a new skill scaffold."""
    import os
    from pathlib import Path

    # Create skill directory
    skill_dir = Path(f"jclaw/skills/builtin/{skill_id}")
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create skill file
    skill_file = skill_dir / "skill.py"
    if skill_file.exists():
        click.echo(click.style(f"✗ Skill '{skill_id}' already exists", fg="red"))
        return

    skill_code = f'''"""{{skill_id}} skill."""

from jclaw.skills import Skill, SkillContext
from jclaw.types import ToolDefinition, ToolResult


class {_to_class_name(skill_id)}Skill(Skill):
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

    with open(skill_file, "w") as f:
        f.write(skill_code)

    click.echo(click.style(f"✓ Skill scaffold created: {skill_file}", fg="green"))
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Edit {skill_file}")
    click.echo(f"  2. Add skill to agent config: skills: [{skill_id}]")
    click.echo(f"  3. Register in pyproject.toml entry-points")


def _to_class_name(snake_str: str) -> str:
    """Convert snake_case to CamelCase."""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)
