"""
Voice Conversation API — /voice_conversation endpoint

Enables bidirectional phone conversations using Twilio + ElevenLabs.
Supports outbound calls (agent calls user), inbound calls (user calls agent),
and webhook handling for multi-turn conversations.
"""

import json
import traceback
from python.helpers.voice_conversation import (
    start_outbound_conversation,
    handle_conversation_webhook,
    handle_inbound_conversation,
    list_conversations,
    load_conversation,
    list_conversation_personas,
    get_conversation_persona,
    CONVERSATION_PERSONAS,
)


def handle_api(request_data: dict, agent=None) -> dict:
    """Route voice conversation actions."""
    action = request_data.get("action", "")

    try:
        # ── Outbound: Agent calls the user ────────────────────
        if action == "call_me":
            phone = request_data.get("phone", "")
            persona = request_data.get("persona", "professional")
            message = request_data.get("message", "")
            if not phone:
                return {"error": "phone number is required (E.164 format)"}
            result = start_outbound_conversation(
                to_number=phone,
                persona_name=persona,
                initial_message=message or None,
            )
            return result

        # ── Inbound call webhook (Twilio → agent) ────────────
        elif action == "inbound":
            twiml = handle_inbound_conversation(request_data)
            return {"success": True, "twiml": twiml, "content_type": "text/xml"}

        # ── Conversation turn webhook ─────────────────────────
        elif action == "turn":
            conv_id = request_data.get("conv_id", "")
            turn = int(request_data.get("turn", 0))
            retry = int(request_data.get("retry", 0))
            if not conv_id:
                return {"error": "conv_id is required"}
            twiml = handle_conversation_webhook(
                webhook_data=request_data,
                conv_id=conv_id,
                turn=turn,
                retry=retry,
            )
            return {"success": True, "twiml": twiml, "content_type": "text/xml"}

        # ── List conversations ────────────────────────────────
        elif action == "list":
            limit = int(request_data.get("limit", 20))
            convs = list_conversations(limit=limit)
            return {"success": True, "conversations": convs}

        # ── Get single conversation ───────────────────────────
        elif action == "get":
            conv_id = request_data.get("conv_id", "")
            if not conv_id:
                return {"error": "conv_id is required"}
            conv = load_conversation(conv_id)
            if conv:
                return {"success": True, "conversation": conv.to_dict()}
            return {"error": f"Conversation {conv_id} not found"}

        # ── Personas ──────────────────────────────────────────
        elif action == "personas":
            return {"success": True, "personas": list_conversation_personas()}

        # ── Get full persona config ───────────────────────────
        elif action == "persona_config":
            name = request_data.get("persona", "professional")
            persona = get_conversation_persona(name)
            safe_persona = {k: v for k, v in persona.items() if k != "system_prompt"}
            return {"success": True, "persona": safe_persona}

        # ── Test / dry run ────────────────────────────────────
        elif action == "test":
            phone = request_data.get("phone", "+10000000000")
            persona = request_data.get("persona", "professional")
            return {
                "success": True,
                "dry_run": True,
                "phone": phone,
                "persona": persona,
                "available_personas": list(CONVERSATION_PERSONAS.keys()),
                "message": "Test successful. Call not placed.",
            }

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "call_me",
                    "inbound",
                    "turn",
                    "list",
                    "get",
                    "personas",
                    "persona_config",
                    "test",
                ],
            }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
