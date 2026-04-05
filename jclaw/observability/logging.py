"""Structured logging configuration for jClaw."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for trace ID
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    """Get current trace ID from context."""
    return trace_id_var.get()


def set_trace_id(trace_id: str | None) -> None:
    """Set trace ID in context."""
    trace_id_var.set(trace_id)


def configure_logging(log_level: str = "INFO", json_mode: bool = True) -> None:
    """Configure structured logging for jClaw.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_mode: Whether to use JSON output (True) or text (False)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add trace_id if available
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.processors.add_log_level,
            # Process exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # JSON or text output
            (structlog.processors.JSONRenderer() if json_mode else structlog.dev.ConsoleRenderer()),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a structlog logger.

    Args:
        name: Logger name

    Returns:
        Bound logger instance
    """
    return structlog.get_logger(name)


# Helper functions for logging specific events

def log_llm_call(
    model: str,
    provider: str,
    input_tokens: int | None = None,
    **kwargs: Any,
) -> None:
    """Log LLM API call.

    Args:
        model: Model name
        provider: Provider name
        input_tokens: Number of input tokens
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        "llm_request",
        model=model,
        provider=provider,
        input_tokens=input_tokens,
        **kwargs,
    )


def log_llm_response(
    model: str,
    provider: str,
    output_tokens: int | None = None,
    latency_ms: float = 0.0,
    stop_reason: str = "",
    **kwargs: Any,
) -> None:
    """Log LLM API response.

    Args:
        model: Model name
        provider: Provider name
        output_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        stop_reason: Stop reason from LLM
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        "llm_response",
        model=model,
        provider=provider,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        stop_reason=stop_reason,
        **kwargs,
    )


def log_llm_error(
    model: str,
    provider: str,
    error: str,
    error_type: str = "",
    **kwargs: Any,
) -> None:
    """Log LLM API error.

    Args:
        model: Model name
        provider: Provider name
        error: Error message
        error_type: Error type/category
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.error(
        "llm_error",
        model=model,
        provider=provider,
        error=error,
        error_type=error_type,
        **kwargs,
    )


def log_handoff(
    source_agent_id: str,
    target_agent_id: str,
    mode: str = "transfer",
    reason: str = "",
    **kwargs: Any,
) -> None:
    """Log agent handoff.

    Args:
        source_agent_id: Source agent ID
        target_agent_id: Target agent ID
        mode: Handoff mode (transfer/delegate/escalate)
        reason: Handoff reason
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        "handoff_completed",
        source_agent_id=source_agent_id,
        target_agent_id=target_agent_id,
        mode=mode,
        reason=reason,
        **kwargs,
    )


def log_guardrail(
    guardrail_id: str,
    action: str = "warn",
    message: str = "",
    **kwargs: Any,
) -> None:
    """Log guardrail trigger.

    Args:
        guardrail_id: Guardrail identifier
        action: Action taken (warn/block)
        message: Additional message
        **kwargs: Additional context
    """
    logger = get_logger()
    logger.info(
        "guardrail_triggered",
        guardrail_id=guardrail_id,
        action=action,
        message=message,
        **kwargs,
    )


def log_skill_execution(
    skill_id: str,
    tool_name: str,
    latency_ms: float = 0.0,
    is_error: bool = False,
    **kwargs: Any,
) -> None:
    """Log skill execution.

    Args:
        skill_id: Skill identifier
        tool_name: Tool name
        latency_ms: Execution latency in milliseconds
        is_error: Whether execution resulted in error
        **kwargs: Additional context
    """
    logger = get_logger()
    log_level = "error" if is_error else "info"
    getattr(logger, log_level)(
        "skill_executed",
        skill_id=skill_id,
        tool_name=tool_name,
        latency_ms=latency_ms,
        is_error=is_error,
        **kwargs,
    )
