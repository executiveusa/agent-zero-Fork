"""
Agent Branding API — /branding endpoint

Manage agent personas, rebranding, and team member assignments.
Allows deploying the same agent with different names/avatars for teammates.
"""

import traceback
from python.helpers.agent_branding import (
    get_persona,
    list_personas,
    create_persona,
    assign_team_member,
    set_default_persona,
    get_team_assignments,
    get_persona_for_team_member,
    get_branding_data,
    get_default_persona_name,
    reload_config,
)


def handle_api(request_data: dict, agent=None) -> dict:
    """Route branding actions."""
    action = request_data.get("action", "")

    try:
        # ── Get current branding (for dashboard) ─────────────
        if action == "current" or action == "":
            persona_key = request_data.get("persona", None)
            return {"success": True, "branding": get_branding_data(persona_key)}

        # ── List all personas ─────────────────────────────────
        elif action == "list":
            return {"success": True, "personas": list_personas(), "default": get_default_persona_name()}

        # ── Get specific persona ──────────────────────────────
        elif action == "get":
            name = request_data.get("persona", "")
            if not name:
                return {"error": "persona key is required"}
            persona = get_persona(name)
            return {"success": True, "persona": persona}

        # ── Create / update persona ───────────────────────────
        elif action == "create":
            key = request_data.get("key", "")
            display_name = request_data.get("display_name", "")
            if not key or not display_name:
                return {"error": "key and display_name are required"}
            result = create_persona(
                key=key,
                display_name=display_name,
                tagline=request_data.get("tagline", ""),
                avatar=request_data.get("avatar", "⭐"),
                theme_color=request_data.get("theme_color", "#00d4ff"),
                voice_persona=request_data.get("voice_persona", "professional"),
                elevenlabs_voice_id=request_data.get("elevenlabs_voice_id", ""),
                greeting=request_data.get("greeting", ""),
                system_style=request_data.get("system_style", ""),
            )
            return result

        # ── Assign team member ────────────────────────────────
        elif action == "assign":
            member_id = request_data.get("member", "")
            persona_key = request_data.get("persona", "")
            if not member_id or not persona_key:
                return {"error": "member and persona are required"}
            return assign_team_member(member_id, persona_key)

        # ── Get team assignments ──────────────────────────────
        elif action == "team":
            return {"success": True, "assignments": get_team_assignments()}

        # ── Get persona for specific team member ──────────────
        elif action == "member_persona":
            member_id = request_data.get("member", "")
            if not member_id:
                return {"error": "member ID is required"}
            persona = get_persona_for_team_member(member_id)
            return {"success": True, "persona": persona}

        # ── Set default persona ───────────────────────────────
        elif action == "set_default":
            persona_key = request_data.get("persona", "")
            if not persona_key:
                return {"error": "persona key is required"}
            return set_default_persona(persona_key)

        # ── Reload config ─────────────────────────────────────
        elif action == "reload":
            reload_config()
            return {"success": True, "message": "Config reloaded"}

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "current", "list", "get", "create",
                    "assign", "team", "member_persona",
                    "set_default", "reload",
                ],
            }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
