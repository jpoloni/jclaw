"""Guardrail registry."""

from jclaw.guardrails.base import Guardrail, GuardrailPipeline, GuardrailContext
from jclaw.guardrails.builtin import InjectionGuard, PIIDetector
from jclaw.types import GuardrailConfig


class GuardrailRegistry:
    """Registry for managing guardrails."""

    def __init__(self):
        """Initialize with built-in guardrails."""
        self._guardrails: dict[str, Guardrail] = {
            "pii_detector": PIIDetector(),
            "injection_guard": InjectionGuard(),
        }

    def register(self, guardrail: Guardrail) -> None:
        """Register a guardrail."""
        self._guardrails[guardrail.guardrail_id] = guardrail

    def get_guardrail(self, guardrail_id: str) -> Guardrail:
        """Get a guardrail by ID."""
        return self._guardrails[guardrail_id]

    def build_input_pipeline(self, config: GuardrailConfig) -> GuardrailPipeline:
        """Build input guardrail pipeline."""
        guardrails = []
        for gid in config.input_guardrails:
            if gid in self._guardrails:
                guardrails.append(self._guardrails[gid])
        return GuardrailPipeline(guardrails)

    def build_output_pipeline(self, config: GuardrailConfig) -> GuardrailPipeline:
        """Build output guardrail pipeline."""
        guardrails = []
        for gid in config.output_guardrails:
            if gid in self._guardrails:
                guardrails.append(self._guardrails[gid])
        return GuardrailPipeline(guardrails)
