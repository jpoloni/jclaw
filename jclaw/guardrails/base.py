"""Base classes for guardrail system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class GuardrailResult:
    """Result of running a guardrail check."""

    action: Literal["pass", "warn", "block"]
    reason: str | None = None
    modified_content: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class GuardrailContext:
    """Context for guardrail execution."""

    session_id: str
    agent_id: str
    user_id: str
    channel: str


class Guardrail(ABC):
    """Abstract base class for guardrails."""

    guardrail_id: str
    name: str
    description: str

    @abstractmethod
    async def check_input(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check input text.

        Args:
            text: Text to check
            context: Guardrail context

        Returns:
            GuardrailResult
        """
        pass

    @abstractmethod
    async def check_output(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check output text.

        Args:
            text: Text to check
            context: Guardrail context

        Returns:
            GuardrailResult
        """
        pass


class GuardrailPipeline:
    """Pipeline that runs multiple guardrails sequentially."""

    def __init__(self, guardrails: list[Guardrail]):
        """Initialize pipeline.

        Args:
            guardrails: List of guardrails to run
        """
        self.guardrails = guardrails

    async def check_input(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Run input guardrails.

        Short-circuits on "block".
        """
        for guardrail in self.guardrails:
            result = await guardrail.check_input(text, context)

            if result.action == "block":
                return result

            # Apply modifications if any
            if result.modified_content:
                text = result.modified_content

        return GuardrailResult(action="pass")

    async def check_output(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Run output guardrails.

        Short-circuits on "block".
        """
        for guardrail in self.guardrails:
            result = await guardrail.check_output(text, context)

            if result.action == "block":
                return result

            # Apply modifications if any
            if result.modified_content:
                text = result.modified_content

        return GuardrailResult(action="pass")
