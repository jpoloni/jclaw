"""Circuit breaker for LLM provider reliability."""

import time
from enum import Enum
from typing import Any

from jclaw.types import CircuitBreakerOpenError


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker pattern for LLM providers.

    Tracks failures and prevents cascading failures by rejecting requests
    when a provider is unhealthy.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Provider failing, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 2,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening (default 5)
            recovery_timeout: Seconds before half-open attempt (default 60)
            half_open_max_calls: Test calls allowed in half-open (default 2)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None

    def call(self, func, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Callable to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self._state == CircuitState.OPEN:
            # Check if we should attempt recovery
            if self._should_attempt_recovery():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker is open for {self.recovery_timeout}s")

        try:
            result = func(*args, **kwargs)

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    # Recovery successful
                    self._close()

            return result

        except Exception as e:
            self._on_failure()
            raise

    async def acall(self, func, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker is open for {self.recovery_timeout}s")

        try:
            result = await func(*args, **kwargs)

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._close()

            return result

        except Exception as e:
            self._on_failure()
            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        if self._state == CircuitState.OPEN and self._should_attempt_recovery():
            return CircuitState.HALF_OPEN
        return self._state

    def _on_failure(self) -> None:
        """Handle failure."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._open()

    def _should_attempt_recovery(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if self._last_failure_time is None:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    def _open(self) -> None:
        """Open the circuit."""
        self._state = CircuitState.OPEN

    def _close(self) -> None:
        """Close the circuit."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None

    def reset(self) -> None:
        """Reset circuit breaker (for testing)."""
        self._close()
