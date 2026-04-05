"""jClaw - AI Agent Orchestration Platform.

A Python 3.11+ async-native platform for building, orchestrating, and operating
conversational AI agents with multi-LLM support, pluggable skills, and channel adapters.
"""

__version__ = "0.1.0"
__author__ = "jClaw Team"
__license__ = "Proprietary"

# Re-export key types for convenience
from jclaw.types import (
    AgentConfig,
    InboundMessage,
    JClawEvent,
    Message,
    OutboundMessage,
    ToolCall,
    ToolResult,
)

__all__ = [
    "__version__",
    "AgentConfig",
    "InboundMessage",
    "JClawEvent",
    "Message",
    "OutboundMessage",
    "ToolCall",
    "ToolResult",
]
