"""REST channel adapter (synchronous, webhook-based)."""

from uuid import uuid4

from jclaw.channels.base import ChannelAdapter
from jclaw.types import InboundMessage, OutboundMessage


class RESTChannelAdapter(ChannelAdapter):
    """REST channel for synchronous REST API requests."""

    channel_id = "rest"

    def __init__(self):
        """Initialize REST channel."""
        self._last_response: OutboundMessage | None = None

    async def receive_webhook(self, request_data: dict) -> InboundMessage:
        """Parse REST request into InboundMessage.

        Expected body:
        {
            "message": "User message text",
            "chat_id": "optional-chat-id",
            "user_id": "optional-user-id"
        }
        """
        message = request_data.get("message", "")
        chat_id = request_data.get("chat_id", "rest_default")
        user_id = request_data.get("user_id", "rest_user")

        return InboundMessage(
            message_id=str(uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            channel="rest",
            text=message,
            metadata=request_data.get("metadata", {}),
        )

    async def send_message(self, chat_id: str, message: OutboundMessage) -> None:
        """Store message for synchronous response.

        Args:
            chat_id: Chat ID
            message: OutboundMessage
        """
        self._last_response = message

    async def send_typing_indicator(self, chat_id: str) -> None:
        """No-op for REST channel."""
        pass

    def get_last_response(self) -> OutboundMessage | None:
        """Get the last message sent (for synchronous REST response).

        Returns:
            OutboundMessage or None
        """
        return self._last_response
