"""Configuration schemas (Pydantic models for settings-specific configs)."""

from typing import Literal

from pydantic import BaseModel, Field


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = Field(5, ge=1)  # Failures before opening
    recovery_timeout: int = Field(60, ge=1)  # Seconds before half-open
    half_open_max_calls: int = Field(2, ge=1)  # Test calls in half-open state


class ProviderModelPair(BaseModel):
    """Pair of provider and model for fallback chains."""

    provider: str
    model: str


class LLMRouterConfig(BaseModel):
    """Configuration for LLM routing."""

    policy: Literal[
        "static", "cost_optimized", "latency_optimized", "fallback_chain"
    ] = "static"
    fallback_chain: list[ProviderModelPair] = Field(default_factory=list)
    timeout_seconds: float = Field(30.0, gt=0)
    max_retries: int = Field(2, ge=0)
    retry_delay_seconds: float = Field(1.0, gt=0)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)


class TelegramConfig(BaseModel):
    """Configuration for Telegram channel."""

    bot_token: str
    webhook_url: str
    webhook_secret: str
    allowed_updates: list[str] = Field(default_factory=lambda: ["message", "callback_query"])
    parse_mode: str = "MarkdownV2"
    max_message_length: int = 4096


class WhatsAppConfig(BaseModel):
    """Configuration for WhatsApp channel."""

    phone_number_id: str
    access_token: str
    verify_token: str
    webhook_url: str
    api_version: str = "v21.0"
    business_account_id: str
    max_message_length: int = 4096
    template_namespace: str | None = None  # For HSMs
