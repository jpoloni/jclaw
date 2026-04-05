"""Event bus for in-process pub/sub."""

import asyncio
import logging
from typing import Callable, Coroutine

from jclaw.types import EventType, JClawEvent

logger = logging.getLogger(__name__)


class EventBus:
    """In-process event bus using asyncio.Queue.

    Provides pub/sub interface that is compatible with future distributed
    implementations (Redis Streams, RabbitMQ, etc).
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: dict[EventType | str, list[Callable]] = {}
        self._queue: asyncio.Queue[JClawEvent] = asyncio.Queue()

    def subscribe(
        self,
        event_type: EventType | str,
        handler: Callable[[JClawEvent], Coroutine],
    ) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to (or "*" for all events)
            handler: Async callable that handles the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscriber registered for event type: {event_type}")

    def unsubscribe(
        self,
        event_type: EventType | str,
        handler: Callable[[JClawEvent], Coroutine],
    ) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Async callable to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
            logger.debug(f"Subscriber unregistered for event type: {event_type}")

    async def emit(self, event: JClawEvent) -> None:
        """Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        await self._queue.put(event)

    async def process_events(self) -> None:
        """Process events from the queue (should run in background).

        This should be started as a background task:
            asyncio.create_task(event_bus.process_events())
        """
        while True:
            try:
                event = await self._queue.get()
                await self._dispatch_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _dispatch_event(self, event: JClawEvent) -> None:
        """Dispatch event to all subscribers.

        Args:
            event: Event to dispatch
        """
        # Get handlers for this specific event type
        specific_handlers = self._subscribers.get(event.event_type, [])

        # Get handlers for all events
        all_handlers = self._subscribers.get("*", [])

        handlers = specific_handlers + all_handlers

        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type}")
            return

        # Run handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Handler {i} failed: {result}", exc_info=result)

    async def wait_for_event(self, event_type: EventType | str, timeout: float = 5.0) -> JClawEvent | None:
        """Wait for a specific event (useful for testing).

        Args:
            event_type: Event type to wait for
            timeout: Timeout in seconds

        Returns:
            Event if received, None if timeout
        """
        future: asyncio.Future[JClawEvent] = asyncio.Future()

        async def handler(event: JClawEvent):
            if not future.done():
                future.set_result(event)

        self.subscribe(event_type, handler)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self.unsubscribe(event_type, handler)

    def get_subscriber_count(self, event_type: EventType | str | None = None) -> int:
        """Get number of subscribers.

        Args:
            event_type: Specific event type or None for all

        Returns:
            Count of subscribers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self._subscribers.values())
        return len(self._subscribers.get(event_type, []))
