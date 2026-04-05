"""Handoff routing between agents."""

from datetime import datetime

from jclaw.db import HandoffLogRepository
from jclaw.memory import SessionMemory
from jclaw.observability import log_handoff
from jclaw.types import AgentConfig, HandoffNotAllowedError, HandoffRequest, HandoffResult


class HandoffRouter:
    """Routes handoffs between agents."""

    def __init__(self, handoff_log_repo: HandoffLogRepository | None = None):
        """Initialize router.

        Args:
            handoff_log_repo: Optional repository for logging handoffs
        """
        self.handoff_log_repo = handoff_log_repo

    async def execute(
        self,
        request: HandoffRequest,
        session_memory: SessionMemory,
        source_agent: AgentConfig,
        target_agent: AgentConfig,
    ) -> HandoffResult:
        """Execute a handoff.

        Args:
            request: Handoff request
            session_memory: Session memory
            source_agent: Source agent config
            target_agent: Target agent config

        Returns:
            HandoffResult

        Raises:
            HandoffNotAllowedError: If handoff not permitted
        """
        # Validate handoff is allowed (target in handoff_targets list)
        self._validate_permission(source_agent, target_agent)

        try:
            # Update active agent in session
            await session_memory.set_metadata(
                request.source_agent_id,
                "active_agent_id",
                request.target_agent_id,
            )

            # Store handoff context
            await session_memory.set_metadata(
                request.source_agent_id,
                "last_handoff",
                request.model_dump(),
            )

            # Log handoff
            log_handoff(
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                mode=request.mode,
                reason=request.reason,
            )

            # Log to database if available
            if self.handoff_log_repo:
                await self.handoff_log_repo.create(
                    session_id=request.source_agent_id,
                    source_agent_id=request.source_agent_id,
                    target_agent_id=request.target_agent_id,
                    mode=request.mode,
                    reason=request.reason,
                    context_payload=request.context_payload,
                    success=True,
                )

            return HandoffResult(
                success=True,
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                mode=request.mode,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            # Log failure
            if self.handoff_log_repo:
                await self.handoff_log_repo.create(
                    session_id=request.source_agent_id,
                    source_agent_id=request.source_agent_id,
                    target_agent_id=request.target_agent_id,
                    mode=request.mode,
                    reason=request.reason,
                    context_payload=request.context_payload,
                    success=False,
                    error_message=str(e),
                )

            return HandoffResult(
                success=False,
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                mode=request.mode,
                timestamp=datetime.utcnow().isoformat(),
                error=str(e),
            )

    def _validate_permission(
        self,
        source_agent: AgentConfig,
        target_agent: AgentConfig,
    ) -> None:
        """Validate that handoff is permitted.

        Args:
            source_agent: Source agent
            target_agent: Target agent

        Raises:
            HandoffNotAllowedError: If not allowed
        """
        if target_agent.agent_id not in source_agent.handoff_targets:
            raise HandoffNotAllowedError(
                f"Agent '{source_agent.agent_id}' cannot handoff to "
                f"'{target_agent.agent_id}'. Allowed targets: {source_agent.handoff_targets}"
            )
