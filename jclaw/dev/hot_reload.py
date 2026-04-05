"""Hot reload watcher for development."""

from pathlib import Path

try:
    from watchfiles import awatch
except ImportError:
    awatch = None

from jclaw.core import AgentRegistry
from jclaw.skills import SkillRegistry


class HotReloadWatcher:
    """Watch files and reload agents/skills on changes."""

    def __init__(
        self,
        agent_registry: AgentRegistry | None = None,
        skill_registry: SkillRegistry | None = None,
        watch_paths: list[str] | None = None,
    ):
        """Initialize watcher.

        Args:
            agent_registry: Agent registry to reload
            skill_registry: Skill registry to reload
            watch_paths: Paths to watch (defaults to config/ and prompts/)
        """
        self.agent_registry = agent_registry
        self.skill_registry = skill_registry
        self.watch_paths = watch_paths or ["config/", "prompts/", "jclaw/skills/"]

    async def watch(self):
        """Watch files for changes and reload."""
        if not awatch:
            raise RuntimeError("watchfiles not installed: pip install watchfiles")

        print(f"👀 Watching: {', '.join(self.watch_paths)}")

        async for changes in awatch(*self.watch_paths, watch_filter=self._filter_changes):
            await self._on_change(changes)

    async def _on_change(self, changes):
        """Handle file changes.

        Args:
            changes: Set of (action, path) tuples
        """
        for action, path in changes:
            path_str = str(path)
            print(f"🔄 Changed: {path_str}")

            # Reload agents on config change
            if "config/" in path_str and path_str.endswith(".yaml"):
                if self.agent_registry:
                    try:
                        await self.agent_registry.load()
                        print("✓ Agents reloaded")
                    except Exception as e:
                        print(f"✗ Failed to reload agents: {e}")

            # Reload skills on skill file change
            if "skills/" in path_str and path_str.endswith(".py"):
                if self.skill_registry:
                    try:
                        self.skill_registry.reload()
                        print("✓ Skills reloaded")
                    except Exception as e:
                        print(f"✗ Failed to reload skills: {e}")

            # Invalidate prompt cache on prompt change
            if "prompts/" in path_str and path_str.endswith(".j2"):
                print("💬 Prompt cache invalidated")

    @staticmethod
    def _filter_changes(path_obj: Path) -> bool:
        """Filter which files to watch.

        Args:
            path_obj: Path object

        Returns:
            True if should watch, False otherwise
        """
        # Watch YAML, Jinja2, Python files
        return str(path_obj).endswith((".yaml", ".j2", ".py")) and ".git" not in str(path_obj)
