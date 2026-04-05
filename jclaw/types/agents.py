"""Agent configuration and related data structures."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class PromptRef(BaseModel):
    """Reference to a prompt template file."""
    path: str  # Relative path to .j2 file
    template_id: str | None = None


class PromptVariable(BaseModel):
    """Definition of a prompt template variable."""
    name: str
    var_type: Literal["string", "int", "float", "bool", "list", "dict", "datetime", "json"] = "string"
    required: bool = True
    default: Any = None
    description: str = ""
    resolver: str | None = None
    validation: dict[str, Any] | None = None  # min_length, max_length, pattern, enum, max_tokens


class PromptLayer(BaseModel):
    """A composable layer of a prompt."""
    layer_id: str
    name: str
    priority: int = 0
    template: str | PromptRef
    condition: str | None = None  # e.g. "channel == 'whatsapp'"
    separator: str = "\n\n"
    required: bool = True
    max_tokens: int | None = None


class PromptConfig(BaseModel):
    """Configuration for multi-layer prompt rendering."""
    version: str = "1.0.0"
    variables: list[PromptVariable] = Field(default_factory=list)
    layers: list[PromptLayer] = Field(default_factory=list)
    pipeline: list[str] = Field(default_factory=list)  # Transformer names


class GuardrailConfig(BaseModel):
    """Configuration for input/output guardrails."""
    input_guardrails: list[str] = Field(default_factory=list)  # Guardrail IDs
    output_guardrails: list[str] = Field(default_factory=list)
    block_mode: Literal["exception", "message"] = "message"
    custom_block_message: str | None = None


class MemoryConfig(BaseModel):
    """Configuration for session memory behavior."""
    strategy: Literal["sliding_window", "summarize_and_trim", "semantic_pruning", "hybrid"] = "hybrid"
    max_messages: int = 100
    max_tokens: int = 8000
    summary_model: str = "claude-haiku-4-5-20251001"
    summary_max_tokens: int = 500
    ttl_seconds: int = 86400  # 24 hours
    persist_to_long_term: bool = True


class AgentConfig(BaseModel):
    """Complete configuration for an agent."""
    agent_id: str
    name: str
    description: str
    system_prompt: str | PromptRef
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4096, ge=1)
    context_window: int = Field(128000, ge=1000)
    skills: list[str] = Field(default_factory=list)
    handoff_targets: list[str] = Field(default_factory=list)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    prompt_config: PromptConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HandoffRequest(BaseModel):
    """Request to hand off control to another agent."""
    source_agent_id: str
    target_agent_id: str
    reason: str
    context_payload: dict[str, Any] = Field(default_factory=dict)
    preserve_history: bool = True
    mode: Literal["transfer", "delegate", "escalate"] = "transfer"


class HandoffResult(BaseModel):
    """Result of a handoff operation."""
    success: bool
    source_agent_id: str
    target_agent_id: str
    mode: str
    timestamp: str  # ISO format
    error: str | None = None
