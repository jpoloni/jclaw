"""Pydantic Settings for jClaw configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class JClawSettings(BaseSettings):
    """Main configuration for jClaw."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="JCLAW_",
        case_sensitive=False,
    )

    # Core
    env: str = "development"  # development | staging | production
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite+aiosqlite:///jclaw.db"
    database_echo: bool = False  # SQL query logging

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Paths
    base_dir: Path = Path(".").resolve()
    prompts_dir: Path = Path("./prompts/templates")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # LLM Providers (Anthropic required, others optional)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    groq_api_key: str = ""

    # Telegram Channel
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""

    # WhatsApp Channel (Future)
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_webhook_url: str = ""
    whatsapp_business_account_id: str = ""

    # Feature flags
    enable_hot_reload: bool = False
    max_tool_iterations: int = 10

    def __init__(self, **kwargs):
        """Initialize settings and resolve relative paths."""
        super().__init__(**kwargs)
        # Resolve paths relative to base_dir
        if not self.prompts_dir.is_absolute():
            self.prompts_dir = self.base_dir / self.prompts_dir

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.env == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.env == "testing"


def get_settings() -> JClawSettings:
    """Get the current settings instance."""
    return JClawSettings()
