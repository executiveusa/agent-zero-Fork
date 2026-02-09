"""
BFF Channel Router API — /channels endpoint
Provides channel management, inbound message routing, and outbound formatting.
"""

import json
import traceback
from python.helpers.bff_channel_router import (
    route_inbound,
    format_outbound,
    get_default_agent,
    CHANNEL_PRIORITIES,
)


def handle_api(request_data: dict, agent=None) -> dict:
    """Route BFF channel actions."""
    action = request_data.get("action", "")

    try:
        if action == "inbound":
            channel = request_data.get("channel", "")
            raw_payload = request_data.get("payload", {})
            if not channel:
                return {"error": "channel is required"}
            message = route_inbound(channel, raw_payload)
            if message:
                return {"success": True, "message": message.__dict__}
            return {"error": f"Failed to normalize message from channel: {channel}"}

        elif action == "outbound":
            channel = request_data.get("channel", "")
            response_text = request_data.get("response_text", "")
            conversation_id = request_data.get("conversation_id", "")
            metadata = request_data.get("metadata", {})
            if not channel or not response_text:
                return {"error": "channel and response_text are required"}
            formatted = format_outbound(channel, response_text, conversation_id, metadata)
            return {"success": True, "formatted": formatted}

        elif action == "channels":
            channels = {}
            for ch, priority in CHANNEL_PRIORITIES.items():
                channels[ch] = {
                    "priority": priority,
                    "default_agent": get_default_agent(ch),
                }
            return {"success": True, "channels": channels}

        elif action == "route_info":
            channel = request_data.get("channel", "web_chat")
            return {
                "success": True,
                "channel": channel,
                "default_agent": get_default_agent(channel),
                "priority": CHANNEL_PRIORITIES.get(channel, 50),
            }

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": ["inbound", "outbound", "channels", "route_info"],
            }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
