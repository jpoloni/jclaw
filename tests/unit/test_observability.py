"""Tests for observability components."""

import asyncio

import pytest

from jclaw.observability import EventBus, configure_logging, get_logger, set_trace_id
from jclaw.types import JClawEvent, MessageSentEvent


class TestEventBus:
    """Tests for EventBus."""

    @pytest.mark.asyncio
    async def test_subscribe_and_emit(self):
        """Test basic subscribe and emit."""
        bus = EventBus()
        received_events = []

        async def handler(event: JClawEvent):
            received_events.append(event)

        bus.subscribe("message.sent", handler)

        event = MessageSentEvent(
            session_id="s1",
            channel="test",
            message_id="m1",
        )
        await bus.emit(event)

        # Process queue
        await bus.process_events()
        await asyncio.sleep(0.1)  # Allow async processing

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test subscribing to all events."""
        bus = EventBus()
        received_events = []

        async def handler(event: JClawEvent):
            received_events.append(event)

        bus.subscribe("*", handler)

        event = MessageSentEvent(
            session_id="s1",
            channel="test",
            message_id="m1",
        )
        await bus.emit(event)

        # Process queue
        await bus.process_events()
        await asyncio.sleep(0.1)

    def test_subscriber_count(self):
        """Test getting subscriber count."""
        bus = EventBus()

        async def handler(event: JClawEvent):
            pass

        bus.subscribe("message.sent", handler)
        bus.subscribe("message.sent", handler)

        assert bus.get_subscriber_count("message.sent") == 2
        assert bus.get_subscriber_count() == 2

    @pytest.mark.asyncio
    async def test_wait_for_event(self):
        """Test waiting for a specific event."""
        bus = EventBus()

        async def emit_later():
            await asyncio.sleep(0.1)
            event = MessageSentEvent(
                session_id="s1",
                channel="test",
                message_id="m1",
            )
            await bus.emit(event)

        # Start background tasks
        task = asyncio.create_task(emit_later())

        # Wait for event with timeout
        event = await bus.wait_for_event("message.sent", timeout=1.0)

        await task
        assert event is not None
        assert event.event_type == "message.sent"

    @pytest.mark.asyncio
    async def test_wait_for_event_timeout(self):
        """Test wait_for_event timeout."""
        bus = EventBus()

        event = await bus.wait_for_event("nonexistent.event", timeout=0.1)
        assert event is None


class TestLogging:
    """Tests for structured logging."""

    def test_configure_logging(self):
        """Test logging configuration."""
        configure_logging(log_level="INFO", json_mode=False)
        logger = get_logger()
        assert logger is not None

    def test_get_logger(self):
        """Test getting a logger."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is not None
        assert logger2 is not None

    def test_trace_id_context(self):
        """Test trace ID context variable."""
        set_trace_id("trace-123")
        from jclaw.observability import get_trace_id

        trace_id = get_trace_id()
        assert trace_id == "trace-123"

        set_trace_id(None)
        assert get_trace_id() is None
