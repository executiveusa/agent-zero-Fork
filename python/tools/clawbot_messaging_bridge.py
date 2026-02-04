"""
ClawBot + Agent Zero Messaging Bridge

This module bridges the gap between ClawBot's multi-platform messaging
and Agent Zero's core AI engine, converting messages to a unified format
that Agent Zero can process and respond to across all platforms.

Status: Framework implementation
Next: Full integration with ClawBot modules
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported messaging platforms"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    TEAMS = "teams"
    SIGNAL = "signal"
    IMESSAGE = "imessage"
    VOICE = "voice"
    DIRECT = "direct"  # Direct API calls


class MessageType(Enum):
    """Types of messages"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    COMMAND = "command"
    REACTION = "reaction"


@dataclass
class MediaAttachment:
    """Media attachment in a message"""
    type: str  # 'image', 'audio', 'video', 'file'
    url: Optional[str] = None
    local_path: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[float] = None  # For audio/video

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UnifiedMessage:
    """
    Unified message format across all platforms.

    This standard format allows Agent Zero to process messages
    from any platform uniformly.
    """
    # Core identifiers
    message_id: str
    platform: Platform
    user_id: str
    user_name: str

    # Content
    content: str
    message_type: MessageType = MessageType.TEXT
    media: List[MediaAttachment] = field(default_factory=list)

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Platform-specific metadata
    platform_metadata: Dict[str, Any] = field(default_factory=dict)

    # Agent Zero context
    context: Dict[str, Any] = field(default_factory=dict)

    # Conversation tracking
    conversation_id: Optional[str] = None
    reply_to: Optional[str] = None

    # Channel/Group info
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    is_group: bool = False
    group_name: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = {
            "message_id": self.message_id,
            "platform": self.platform.value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "platform_metadata": self.platform_metadata,
            "context": self.context,
            "conversation_id": self.conversation_id,
            "reply_to": self.reply_to,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "is_group": self.is_group,
            "group_name": self.group_name,
            "media": [m.to_dict() for m in self.media],
        }
        return data

    def to_agent_input(self) -> Dict:
        """
        Convert to Agent Zero input format.

        This format is what Agent Zero's message processing expects.
        """
        return {
            "source": f"{self.platform.value}:{self.user_id}",
            "source_name": f"{self.user_name}",
            "message": self.content,
            "type": self.message_type.value,
            "metadata": {
                "platform": self.platform.value,
                "message_id": self.message_id,
                "timestamp": self.timestamp.isoformat(),
                "conversation_id": self.conversation_id,
                "is_group": self.is_group,
                "group_name": self.group_name,
                **self.platform_metadata
            },
            "media": [m.to_dict() for m in self.media] if self.media else None,
            "context": self.context
        }

    def to_memory_entry(self) -> Dict:
        """Convert to format for memory storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "platform": self.platform.value,
            "user": self.user_name,
            "message": self.content,
            "message_id": self.message_id,
            "type": self.message_type.value,
            "media_count": len(self.media),
        }


class MessagingBridge:
    """
    Main bridge for converting between platform formats and unified format.

    Handles bi-directional conversion:
    - Platform Message → UnifiedMessage → Agent Zero Input
    - Agent Zero Response → UnifiedMessage → Platform Message
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.converters = {
            Platform.WHATSAPP: self._whatsapp_converter,
            Platform.TELEGRAM: self._telegram_converter,
            Platform.DISCORD: self._discord_converter,
            Platform.SLACK: self._slack_converter,
            Platform.TEAMS: self._teams_converter,
            Platform.VOICE: self._voice_converter,
        }

    async def incoming_message(self, platform: Platform, raw_message: Dict) -> UnifiedMessage:
        """
        Convert incoming platform message to unified format.

        Args:
            platform: Source platform
            raw_message: Platform-specific message dict

        Returns:
            UnifiedMessage ready for Agent Zero processing
        """
        try:
            converter = self.converters.get(platform)
            if not converter:
                self.logger.error(f"No converter for platform: {platform}")
                raise ValueError(f"Unsupported platform: {platform}")

            unified = await converter.to_unified(raw_message)
            self.logger.info(f"Converted {platform.value} message: {unified.message_id}")
            return unified

        except Exception as e:
            self.logger.error(f"Error converting message: {e}")
            raise

    async def outgoing_response(self,
                               unified_message: UnifiedMessage,
                               response_text: str,
                               metadata: Dict = None) -> Dict:
        """
        Convert Agent Zero response to platform-specific format.

        Args:
            unified_message: Original message (for context)
            response_text: Agent Zero's response
            metadata: Additional response metadata

        Returns:
            Platform-specific message dict ready to send
        """
        try:
            converter = self.converters.get(unified_message.platform)
            if not converter:
                self.logger.error(f"No converter for platform: {unified_message.platform}")
                raise ValueError(f"Unsupported platform: {unified_message.platform}")

            platform_response = await converter.to_platform(
                unified_message, response_text, metadata
            )
            self.logger.info(f"Converted response for {unified_message.platform.value}")
            return platform_response

        except Exception as e:
            self.logger.error(f"Error converting response: {e}")
            raise

    # Placeholder converter implementations
    # In real implementation, these would handle actual platform APIs

    class WhatsAppConverter:
        """WhatsApp message converter"""
        async def to_unified(self, raw_message: Dict) -> UnifiedMessage:
            # Parse WhatsApp message format
            return UnifiedMessage(
                message_id=raw_message.get("id"),
                platform=Platform.WHATSAPP,
                user_id=raw_message.get("from"),
                user_name=raw_message.get("sender_name", "User"),
                content=raw_message.get("body", ""),
                message_type=MessageType.TEXT,
            )

        async def to_platform(self, unified: UnifiedMessage,
                             response: str, metadata: Dict = None) -> Dict:
            # Convert to WhatsApp API format
            return {
                "messaging_product": "whatsapp",
                "to": unified.user_id,
                "type": "text",
                "text": {"body": response},
            }

    class TelegramConverter:
        """Telegram message converter"""
        async def to_unified(self, raw_message: Dict) -> UnifiedMessage:
            # Parse Telegram message format
            return UnifiedMessage(
                message_id=str(raw_message.get("message_id")),
                platform=Platform.TELEGRAM,
                user_id=str(raw_message.get("from", {}).get("id")),
                user_name=raw_message.get("from", {}).get("first_name", "User"),
                content=raw_message.get("text", ""),
                message_type=MessageType.TEXT,
                is_group=raw_message.get("chat", {}).get("type") in ["group", "supergroup"],
                group_name=raw_message.get("chat", {}).get("title"),
            )

        async def to_platform(self, unified: UnifiedMessage,
                             response: str, metadata: Dict = None) -> Dict:
            # Convert to Telegram API format
            return {
                "chat_id": unified.user_id,
                "text": response,
                "parse_mode": "Markdown",
            }

    class VoiceConverter:
        """Voice message converter"""
        async def to_unified(self, raw_message: Dict) -> UnifiedMessage:
            # Parse voice input
            return UnifiedMessage(
                message_id=raw_message.get("id"),
                platform=Platform.VOICE,
                user_id=raw_message.get("user_id", "voice_user"),
                user_name=raw_message.get("user_name", "Voice User"),
                content=raw_message.get("text", ""),  # Transcribed from audio
                message_type=MessageType.AUDIO,
                media=[MediaAttachment(
                    type="audio",
                    url=raw_message.get("audio_url"),
                    duration=raw_message.get("duration"),
                )],
            )

        async def to_platform(self, unified: UnifiedMessage,
                             response: str, metadata: Dict = None) -> Dict:
            # Convert to voice output format
            return {
                "user_id": unified.user_id,
                "text": response,
                "audio_format": "mp3",
                "voice_id": metadata.get("voice_id", "default") if metadata else "default",
            }

    # Set up converters
    _whatsapp_converter = WhatsAppConverter()
    _telegram_converter = TelegramConverter()
    _discord_converter = WhatsAppConverter()  # Placeholder
    _slack_converter = WhatsAppConverter()    # Placeholder
    _teams_converter = WhatsAppConverter()    # Placeholder
    _voice_converter = VoiceConverter()


# Example usage and testing
async def example_usage():
    """Demonstrate messaging bridge usage"""

    bridge = MessagingBridge()

    # Example: WhatsApp message incoming
    whatsapp_raw = {
        "id": "wamid.abc123",
        "from": "1234567890",
        "sender_name": "Alice",
        "body": "What's the weather today?"
    }

    unified = await bridge.incoming_message(Platform.WHATSAPP, whatsapp_raw)
    print("Unified message:")
    print(json.dumps(unified.to_dict(), indent=2))

    # Example: Agent Zero response
    agent_response = "The weather today is sunny with a high of 72°F."

    platform_response = await bridge.outgoing_response(unified, agent_response)
    print("\nPlatform response:")
    print(json.dumps(platform_response, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())
