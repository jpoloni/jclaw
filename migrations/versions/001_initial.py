"""Initial schema migration - creates all tables.

Revision ID: 001
Revises:
Create Date: 2026-04-05 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all initial tables."""

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("chat_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("active_agent_id", sa.String(100), nullable=False),
        sa.Column("extras", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "chat_id", name="uq_channel_chat"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("tool_call_id", sa.String(255), nullable=True),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_results", sa.JSON(), nullable=True),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("extras", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # Create memory_facts table
    op.create_table(
        "memory_facts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("fact_key", sa.String(255), nullable=False),
        sa.Column("fact_value", sa.Text(), nullable=False),
        sa.Column("source_session_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("extras", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "fact_key", name="uq_user_fact_key"),
    )
    op.create_index("ix_memory_facts_user_id", "memory_facts", ["user_id"])

    # Create handoff_log table
    op.create_table(
        "handoff_log",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("source_agent_id", sa.String(100), nullable=False),
        sa.Column("target_agent_id", sa.String(100), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("context_payload", sa.JSON(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_handoff_log_session_id", "handoff_log", ["session_id"])
    op.create_index("ix_handoff_log_created_at", "handoff_log", ["created_at"])

    # Create prompt_templates table
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("template_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("engine", sa.String(50), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column("extras", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version", name="uq_template_version"),
    )
    op.create_index("ix_prompt_templates_template_id", "prompt_templates", ["template_id"])

    # Create prompt_analytics table
    op.create_table(
        "prompt_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("template_id", sa.String(255), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("render_time_ms", sa.Float(), nullable=False),
        sa.Column("variables_resolved", sa.Integer(), nullable=False),
        sa.Column("variables_failed", sa.Integer(), nullable=False),
        sa.Column("extras", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prompt_analytics_template_id", "prompt_analytics", ["template_id"])
    op.create_index("ix_prompt_analytics_agent_id", "prompt_analytics", ["agent_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_prompt_analytics_agent_id", table_name="prompt_analytics")
    op.drop_index("ix_prompt_analytics_template_id", table_name="prompt_analytics")
    op.drop_table("prompt_analytics")

    op.drop_index("ix_prompt_templates_template_id", table_name="prompt_templates")
    op.drop_table("prompt_templates")

    op.drop_index("ix_handoff_log_created_at", table_name="handoff_log")
    op.drop_index("ix_handoff_log_session_id", table_name="handoff_log")
    op.drop_table("handoff_log")

    op.drop_index("ix_memory_facts_user_id", table_name="memory_facts")
    op.drop_table("memory_facts")

    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_session_id", table_name="messages")
    op.drop_table("messages")

    op.drop_table("sessions")
