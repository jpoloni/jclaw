"""Context window and token budget management."""

from dataclasses import dataclass

from jclaw.llm import TokenCounter
from jclaw.types import AgentConfig, Message, ToolDefinition


@dataclass
class PromptPayload:
    """Payload ready for LLM."""

    system: str
    messages: list[Message]
    tools: list[ToolDefinition]
    input_tokens: int
    output_tokens_budget: int
    history_tokens_budget: int


class ContextWindowManager:
    """Manages token budget across system prompt, history, and response."""

    # Safety margin to avoid truncation
    SAFETY_MARGIN = 500

    def __init__(self, agent_config: AgentConfig, token_counter: TokenCounter):
        """Initialize manager.

        Args:
            agent_config: Agent configuration
            token_counter: Token counter
        """
        self.agent_config = agent_config
        self.token_counter = token_counter
        self.max_context = agent_config.context_window
        self.max_response = agent_config.max_tokens

    def build_payload(
        self,
        system_prompt: str,
        messages: list[Message],
        tools: list[ToolDefinition],
    ) -> PromptPayload:
        """Build prompt payload with token budget enforcement.

        Args:
            system_prompt: System prompt text
            messages: Conversation messages
            tools: Available tools

        Returns:
            PromptPayload ready for LLM
        """
        # Calculate budget regions
        # budget = context_window - max_response - safety_margin
        budget = self.max_context - self.max_response - self.SAFETY_MARGIN

        # Count tokens for fixed parts
        system_tokens = self.token_counter.count(system_prompt)
        tools_tokens = self.token_counter.count_tools(tools) if tools else 0

        fixed_tokens = system_tokens + tools_tokens
        remaining_budget = budget - fixed_tokens

        # Allocate: memory (20%), history (80%)
        memory_tokens = int(remaining_budget * 0.2)
        history_tokens = remaining_budget - memory_tokens

        # Fit messages into history budget by trimming old messages
        fitted_messages = self._fit_messages(messages, history_tokens)

        # Count actual input tokens
        input_tokens = system_tokens + tools_tokens + self.token_counter.count_messages(fitted_messages)

        return PromptPayload(
            system=system_prompt,
            messages=fitted_messages,
            tools=tools,
            input_tokens=input_tokens,
            output_tokens_budget=self.max_response,
            history_tokens_budget=history_tokens,
        )

    def _fit_messages(self, messages: list[Message], budget: int) -> list[Message]:
        """Trim messages to fit in token budget (keep most recent).

        Args:
            messages: Messages to fit
            budget: Token budget

        Returns:
            Trimmed messages
        """
        if not messages:
            return []

        # Keep messages from most recent backwards
        fitted = []
        tokens_used = 0

        for msg in reversed(messages):
            msg_tokens = self.token_counter.count(msg.content)

            if tokens_used + msg_tokens <= budget:
                fitted.insert(0, msg)
                tokens_used += msg_tokens
            else:
                # Stop when budget exceeded
                break

        return fitted
