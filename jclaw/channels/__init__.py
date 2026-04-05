"""Channel adapters for jClaw."""

from jclaw.channels.base import ChannelAdapter
from jclaw.channels.rest import RESTChannelAdapter
from jclaw.channels.telegram import TelegramChannelAdapter

__all__ = [
    "ChannelAdapter",
    "RESTChannelAdapter",
    "TelegramChannelAdapter",
]
