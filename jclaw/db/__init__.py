"""Database module for jClaw."""

from jclaw.db.engine import AsyncSessionLocal, cleanup_db, engine, get_db, init_db
from jclaw.db.models import (
    Base,
    HandoffLog,
    MemoryFact,
    MessageRecord,
    PromptAnalytics,
    PromptTemplate,
    Session,
)
from jclaw.db.repositories import (
    HandoffLogRepository,
    MemoryFactRepository,
    MessageRepository,
    PromptAnalyticsRepository,
    PromptTemplateRepository,
    SessionRepository,
)

__all__ = [
    # Engine
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "cleanup_db",
    # Models
    "Base",
    "Session",
    "MessageRecord",
    "MemoryFact",
    "HandoffLog",
    "PromptTemplate",
    "PromptAnalytics",
    # Repositories
    "SessionRepository",
    "MessageRepository",
    "MemoryFactRepository",
    "HandoffLogRepository",
    "PromptTemplateRepository",
    "PromptAnalyticsRepository",
]
