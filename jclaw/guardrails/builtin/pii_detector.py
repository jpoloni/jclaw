"""PII (Personally Identifiable Information) detection guardrail."""

import re

from jclaw.guardrails.base import Guardrail, GuardrailContext, GuardrailResult


class PIIDetector(Guardrail):
    """Detects and optionally redacts PII like emails, phone numbers, CPF."""

    guardrail_id = "pii_detector"
    name = "PII Detector"
    description = "Detects and optionally redacts personally identifiable information"

    # Patterns for common PII
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "cpf": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",  # XXX.XXX.XXX-XX
        "phone": r"\b(?:\+55|0)?[1-9]\d{9,10}\b",
        "creditcard": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    }

    async def check_input(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check input for PII."""
        return self._check_text(text)

    async def check_output(self, text: str, context: GuardrailContext) -> GuardrailResult:
        """Check output for PII."""
        return self._check_text(text)

    def _check_text(self, text: str) -> GuardrailResult:
        """Check text for PII matches."""
        found_pii = {}
        modified_text = text

        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                found_pii[pii_type] = matches
                # Redact in modified text
                modified_text = re.sub(pattern, f"[{pii_type.upper()}]", modified_text)

        if found_pii:
            return GuardrailResult(
                action="warn",
                reason=f"Found PII: {list(found_pii.keys())}",
                modified_content=modified_text,
                metadata={"pii_types": found_pii},
            )

        return GuardrailResult(action="pass")
