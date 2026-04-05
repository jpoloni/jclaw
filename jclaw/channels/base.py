"""Base class for channel adapters."""

from abc import ABC, abstractmethod

from jclaw.types import InboundMessage, OutboundMessage


class ChannelAdapter(ABC):
    """Abstract base class for channel adapters."""

    channel_id: str

    @abstractmethod
    async def receive_webhook(self, request_data: dict) -> InboundMessage:
        """Parse webhook from channel into InboundMessage.

        Args:
            request_data: Webhook payload

        Returns:
            InboundMessage
        """
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, message: OutboundMessage) -> None:
        """Send message to channel.

        Args:
            chat_id: Chat/conversation ID
            message: OutboundMessage to send
        """
        pass

    @abstractmethod
    async def send_typing_indicator(self, chat_id: str) -> None:
        """Send typing indicator to channel.

        Args:
            chat_id: Chat ID
        """
        pass

    def get_session_id(self, inbound: InboundMessage) -> str:
        """Get session ID from inbound message.

        Args:
            inbound: InboundMessage

        Returns:
            Session ID
        """
        return f"{self.channel_id}:{inbound.chat_id}"
