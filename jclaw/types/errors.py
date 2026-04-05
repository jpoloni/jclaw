"""Exception hierarchy for jClaw."""


class JClawError(Exception):
    """Base exception for all jClaw errors."""
    pass


# Configuration errors
class ConfigValidationError(JClawError):
    """Raised when configuration validation fails."""
    pass


class AgentNotFoundError(JClawError):
    """Raised when an agent ID is not found."""
    pass


# Memory errors
class SessionMemoryError(JClawError):
    """Base exception for session memory errors."""
    pass


class SessionNotFoundError(SessionMemoryError):
    """Raised when a session is not found."""
    pass


# LLM errors
class LLMProviderError(JClawError):
    """Base exception for LLM provider errors."""
    pass


class LLMProviderNotAvailableError(LLMProviderError):
    """Raised when an LLM provider is not available."""
    pass


class LLMAPIError(LLMProviderError):
    """Raised when an LLM API call fails."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM call times out."""
    pass


class CircuitBreakerOpenError(LLMProviderError):
    """Raised when circuit breaker is open for a provider."""
    pass


# Skill errors
class SkillNotFoundError(JClawError):
    """Raised when a skill is not found."""
    pass


class SkillExecutionError(JClawError):
    """Raised when skill execution fails."""
    pass


# Guardrail errors
class GuardrailBlockedError(JClawError):
    """Raised when content is blocked by a guardrail."""
    pass


# Handoff errors
class HandoffNotAllowedError(JClawError):
    """Raised when a handoff is not allowed (not in handoff_targets)."""
    pass


class HandoffFailedError(JClawError):
    """Raised when a handoff operation fails."""
    pass


# Prompt errors
class PromptRenderError(JClawError):
    """Raised when prompt rendering fails."""
    pass


class PromptTemplateNotFoundError(JClawError):
    """Raised when a prompt template is not found."""
    pass


class VariableResolutionError(JClawError):
    """Raised when a prompt variable cannot be resolved."""
    pass


# Channel errors
class ChannelError(JClawError):
    """Base exception for channel errors."""
    pass


class ChannelWebhookVerificationError(ChannelError):
    """Raised when webhook signature verification fails."""
    pass
