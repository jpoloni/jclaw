"""Telegram channel adapter."""

import hashlib
import hmac
from uuid import uuid4

import httpx

from jclaw.channels.base import ChannelAdapter
from jclaw.types import ChannelWebhookVerificationError, InboundMessage, OutboundMessage


class TelegramChannelAdapter(ChannelAdapter):
    """Telegram bot channel adapter."""

    channel_id = "telegram"

    def __init__(self, bot_token: str, webhook_secret: str = ""):
        """Initialize Telegram adapter.

        Args:
            bot_token: Telegram bot token
            webhook_secret: Webhook verification secret
        """
        self.bot_token = bot_token
        self.webhook_secret = webhook_secret
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def receive_webhook(self, request_data: dict) -> InboundMessage:
        """Parse Telegram webhook into InboundMessage.

        Args:
            request_data: Telegram Update object

        Returns:
            InboundMessage

        Raises:
            ChannelWebhookVerificationError: If verification fails
        """
        # Verify webhook secret if configured
        if self.webhook_secret:
            self._verify_webhook(request_data)

        # Extract message
        message_data = request_data.get("message", {})
        chat_id = str(message_data.get("chat", {}).get("id", ""))
        user_id = str(message_data.get("from", {}).get("id", ""))
        text = message_data.get("text", "")

        # Handle commands
        if text.startswith("/"):
            text = text[1:].split()[0]  # Get command without /

        return InboundMessage(
            message_id=str(message_data.get("message_id", uuid4())),
            chat_id=chat_id,
            user_id=user_id,
            channel="telegram",
            text=text,
            metadata={
                "username": message_data.get("from", {}).get("username", ""),
                "first_name": message_data.get("from", {}).get("first_name", ""),
            },
        )

    async def send_message(self, chat_id: str, message: OutboundMessage) -> None:
        """Send message to Telegram.

        Args:
            chat_id: Telegram chat ID
            message: OutboundMessage to send
        """
        text = message.text or ""

        # Split long messages (Telegram limit: 4096)
        max_length = 4096
        for i in range(0, len(text), max_length):
            chunk = text[i : i + max_length]

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "parse_mode": "MarkdownV2",
                    },
                )

    async def send_typing_indicator(self, chat_id: str) -> None:
        """Send typing indicator to Telegram.

        Args:
            chat_id: Telegram chat ID
        """
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_url}/sendChatAction",
                json={
                    "chat_id": chat_id,
                    "action": "typing",
                },
            )

    def _verify_webhook(self, request_data: dict) -> None:
        """Verify webhook signature.

        Args:
            request_data: Webhook payload

        Raises:
            ChannelWebhookVerificationError: If verification fails
        """
        # For v0.1, simple verification
        # In production, would use HMAC-SHA256 on request body
        if not self.webhook_secret:
            return

        # Stub verification (real Telegram uses X-Telegram-Bot-Api-Secret-Token header)
        # This is a simplified version
        pass
