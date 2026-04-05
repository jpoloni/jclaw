"""Prompt injection detection guardrail."""

from jclaw.guardrails.base import Guardrail, GuardrailContext, GuardrailResult


class InjectionGuard(Guardrail):
    """Detects and blocks common prompt injection attempts."""

    guardrail_id = "injection_guard"
    name = "Injection Guard"
    description = "Detects and blocks prompt injection attempts"

    # Suspicious patterns
    SUSPICIOUS_PATTERNS = [
        "ignore previous",
        "you are now",
        "pretend to be",
        "act as if",
        "from now on",
        "disregard",
        "override",
        "bypass",
        "forget everything",
        "new instructions",
        "system prompt",
        "developer mode",
        "jailbreak",
    ]

    async def check_input(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check input for injection attempts."""
        text_lower = text.lower()

        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in text_lower:
                return GuardrailResult(
                    action="block",
                    reason=f"Possible prompt injection detected: '{pattern}'",
                    metadata={"detected_pattern": pattern},
                )

        return GuardrailResult(action="pass")

    async def check_output(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check output (usually pass-through)."""
        return GuardrailResult(action="pass")
