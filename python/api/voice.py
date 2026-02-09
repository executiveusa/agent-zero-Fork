"""
Voice AI API — /voice endpoint
Provides outbound calling, inbound call webhook, call logs, and voice persona management.
"""

import json
import traceback
from python.helpers.voice_ai import (
    make_outbound_call,
    handle_inbound_call,
    get_call_log,
    VOICE_PERSONAS,
)


def handle_api(request_data: dict, agent=None) -> dict:
    """Route voice AI actions."""
    action = request_data.get("action", "")

    try:
        if action == "make_call":
            to = request_data.get("to", "")
            message = request_data.get("message", "")
            voice = request_data.get("voice", "professional")
            if not to:
                return {"error": "to (phone number) is required"}
            if not message:
                return {"error": "message is required"}
            result = make_outbound_call(to=to, message=message, voice=voice)
            return {"success": True, "call": result}

        elif action == "inbound_webhook":
            # Returns TwiML for Twilio to process
            twiml = handle_inbound_call()
            return {"success": True, "twiml": twiml, "content_type": "text/xml"}

        elif action == "call_log":
            limit = request_data.get("limit", 50)
            log = get_call_log()
            return {"success": True, "calls": log[-limit:], "total": len(log)}

        elif action == "personas":
            return {"success": True, "personas": VOICE_PERSONAS}

        elif action == "test":
            # Dry-run test — does not actually call
            to = request_data.get("to", "+10000000000")
            message = request_data.get("message", "This is a test call from Agent Claw.")
            return {
                "success": True,
                "dry_run": True,
                "to": to,
                "message": message,
                "available_personas": list(VOICE_PERSONAS.keys()),
            }

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "make_call",
                    "inbound_webhook",
                    "call_log",
                    "personas",
                    "test",
                ],
            }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
