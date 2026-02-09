"""
BFF Channel Router — Agent Claw Multi-Channel Gateway

Normalizes inbound messages from all channels (WhatsApp, Telegram,
Discord, iMessage, Web Chat, Voice) into the internal Agent Claw
message protocol, routes to the appropriate agent, and formats
responses back to channel-specific formats.

Architecture:
  Channel → BFF Adapter → Normalized Message → Orchestrator → Agent
  Agent → Response → BFF Formatter → Channel-Specific Output
"""

import os
import json
import yaml
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class InboundMessage:
    """Normalized inbound message from any channel."""
    channel: str
    sender_id: str
    message_text: str
    message_type: str = "text"  # text, media, command, voice, system
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    conversation_id: str = ""
    priority: int = 5

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OutboundResponse:
    """Normalized outbound response to any channel."""
    channel: str
    recipient_id: str
    message_text: str
    rich_content: dict = field(default_factory=dict)
    media: list = field(default_factory=list)
    suggested_actions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Channel Priority Mapping ────────────────────────────────

CHANNEL_PRIORITIES = {
    "whatsapp": 0,
    "telegram": 0,
    "voice": 0,
    "web_chat": 1,
    "discord": 1,
    "imessage": 2,
    "email": 3,
}


def get_channel_priority(channel: str) -> int:
    """Get numeric priority for a channel (lower = higher priority)."""
    return CHANNEL_PRIORITIES.get(channel, 5)


# ─── BFF Config Loader ───────────────────────────────────────

_bff_config = None


def load_bff_config() -> dict:
    """Load BFF channel configuration from YAML."""
    global _bff_config
    if _bff_config is not None:
        return _bff_config

    config_path = os.path.join("conf", "bff_channels.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            _bff_config = yaml.safe_load(f)
    else:
        _bff_config = {"channels": {}, "routing": {"default_agent": "customer-service"}}

    return _bff_config


# ─── Message Normalization ───────────────────────────────────

def normalize_whatsapp(raw: dict) -> InboundMessage:
    """Normalize a Twilio WhatsApp webhook payload."""
    return InboundMessage(
        channel="whatsapp",
        sender_id=raw.get("From", "").replace("whatsapp:", ""),
        message_text=raw.get("Body", ""),
        message_type="media" if raw.get("NumMedia", "0") != "0" else "text",
        attachments=[
            {"url": raw.get(f"MediaUrl{i}", ""), "mime_type": raw.get(f"MediaContentType{i}", "")}
            for i in range(int(raw.get("NumMedia", "0")))
        ],
        metadata={"profile_name": raw.get("ProfileName", ""), "wa_id": raw.get("WaId", "")},
        priority=get_channel_priority("whatsapp"),
    )


def normalize_telegram(raw: dict) -> InboundMessage:
    """Normalize a Telegram Bot API update."""
    message = raw.get("message", {})
    sender = message.get("from", {})
    return InboundMessage(
        channel="telegram",
        sender_id=str(sender.get("id", "")),
        message_text=message.get("text", ""),
        message_type="command" if message.get("text", "").startswith("/") else "text",
        metadata={
            "chat_id": message.get("chat", {}).get("id"),
            "username": sender.get("username", ""),
            "first_name": sender.get("first_name", ""),
        },
        priority=get_channel_priority("telegram"),
    )


def normalize_discord(raw: dict) -> InboundMessage:
    """Normalize a Discord message event."""
    return InboundMessage(
        channel="discord",
        sender_id=raw.get("author", {}).get("id", ""),
        message_text=raw.get("content", ""),
        message_type="command" if raw.get("content", "").startswith("/") else "text",
        metadata={
            "guild_id": raw.get("guild_id", ""),
            "channel_id": raw.get("channel_id", ""),
            "username": raw.get("author", {}).get("username", ""),
        },
        priority=get_channel_priority("discord"),
    )


def normalize_web_chat(raw: dict) -> InboundMessage:
    """Normalize a web chat message."""
    return InboundMessage(
        channel="web_chat",
        sender_id=raw.get("session_id", raw.get("user_id", "")),
        message_text=raw.get("message", raw.get("text", "")),
        message_type=raw.get("type", "text"),
        attachments=raw.get("attachments", []),
        metadata=raw.get("metadata", {}),
        conversation_id=raw.get("conversation_id", ""),
        priority=get_channel_priority("web_chat"),
    )


def normalize_voice(raw: dict) -> InboundMessage:
    """Normalize a Twilio voice/STT payload."""
    return InboundMessage(
        channel="voice",
        sender_id=raw.get("From", raw.get("Caller", "")),
        message_text=raw.get("SpeechResult", raw.get("TranscriptionText", "")),
        message_type="voice",
        metadata={
            "call_sid": raw.get("CallSid", ""),
            "call_status": raw.get("CallStatus", ""),
            "direction": raw.get("Direction", ""),
        },
        priority=get_channel_priority("voice"),
    )


# ─── Response Formatting ─────────────────────────────────────

def format_for_whatsapp(response: OutboundResponse) -> dict:
    """Format response for Twilio WhatsApp API."""
    return {
        "To": f"whatsapp:{response.recipient_id}",
        "Body": response.message_text,
        "MediaUrl": [m["url"] for m in response.media] if response.media else None,
    }


def format_for_telegram(response: OutboundResponse) -> dict:
    """Format response for Telegram Bot API."""
    result = {
        "chat_id": response.recipient_id,
        "text": response.message_text,
        "parse_mode": "Markdown",
    }
    if response.suggested_actions:
        result["reply_markup"] = {
            "inline_keyboard": [
                [{"text": a["label"], "callback_data": a["action"]}]
                for a in response.suggested_actions
            ]
        }
    return result


def format_for_discord(response: OutboundResponse) -> dict:
    """Format response for Discord API."""
    result = {"content": response.message_text}
    if response.rich_content:
        result["embeds"] = [response.rich_content]
    return result


def format_for_web_chat(response: OutboundResponse) -> dict:
    """Format response for web chat widget."""
    return {
        "message": response.message_text,
        "type": "agent",
        "suggested_actions": response.suggested_actions,
        "media": response.media,
    }


def format_for_voice(response: OutboundResponse) -> str:
    """Format response as TwiML for Twilio voice."""
    # Truncate for TTS
    text = response.message_text[:500]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="Polly.Joanna">{text}</Say>'
        '<Gather input="speech" timeout="5" speechTimeout="auto" action="/webhook/voice">'
        '<Say voice="Polly.Joanna">Is there anything else I can help you with?</Say>'
        "</Gather>"
        "</Response>"
    )


# ─── Router ──────────────────────────────────────────────────

NORMALIZERS = {
    "whatsapp": normalize_whatsapp,
    "telegram": normalize_telegram,
    "discord": normalize_discord,
    "web_chat": normalize_web_chat,
    "voice": normalize_voice,
}

FORMATTERS = {
    "whatsapp": format_for_whatsapp,
    "telegram": format_for_telegram,
    "discord": format_for_discord,
    "web_chat": format_for_web_chat,
    "voice": format_for_voice,
}


def route_inbound(channel: str, raw_payload: dict) -> InboundMessage:
    """
    Normalize an inbound message from any supported channel.
    Returns a unified InboundMessage ready for the orchestrator.
    """
    normalizer = NORMALIZERS.get(channel)
    if not normalizer:
        return InboundMessage(
            channel=channel,
            sender_id=raw_payload.get("sender_id", "unknown"),
            message_text=raw_payload.get("message", str(raw_payload)),
            priority=get_channel_priority(channel),
        )
    return normalizer(raw_payload)


def format_outbound(channel: str, response: OutboundResponse):
    """
    Format an outbound response for the target channel.
    Returns channel-specific payload.
    """
    formatter = FORMATTERS.get(channel)
    if not formatter:
        return response.to_dict()
    return formatter(response)


def get_default_agent(channel: str) -> str:
    """Get the default agent for a channel."""
    config = load_bff_config()
    routing = config.get("routing", {})
    
    # Check channel-specific override
    overrides = routing.get("overrides", {})
    if channel in overrides:
        return overrides[channel].get("default_agent", routing.get("default_agent", "customer-service"))
    
    return routing.get("default_agent", "customer-service")
