"""Pydantic models for prompt system."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RenderedPrompt(BaseModel):
    """Result of rendering a prompt."""

    content: str
    token_count: int
    layers_used: list[str] = Field(default_factory=list)
    variables_resolved: int = 0
    variables_failed: int = 0
    template_version: str = "1.0.0"
    rendered_at: datetime = Field(default_factory=datetime.utcnow)
