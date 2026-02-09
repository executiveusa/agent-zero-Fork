"""
Content Automation API — /content endpoint
Provides CRUD for content pieces, calendar management, and brief generation.
"""

import json
import traceback
from python.helpers.content_automation import (
    create_content,
    update_content,
    get_content,
    get_content_calendar,
    generate_content_brief,
    CONTENT_TEMPLATES,
)


def handle_api(request_data: dict, agent=None) -> dict:
    """Route content automation actions."""
    action = request_data.get("action", "")

    try:
        if action == "create":
            content_type = request_data.get("content_type", "blog")
            topic = request_data.get("topic", "")
            client_name = request_data.get("client_name", "")
            notes = request_data.get("notes", "")
            if not topic:
                return {"error": "topic is required"}
            piece = create_content(
                content_type=content_type,
                topic=topic,
                client_name=client_name,
                notes=notes,
            )
            return {"success": True, "content": piece.__dict__}

        elif action == "update":
            content_id = request_data.get("content_id", "")
            updates = request_data.get("updates", {})
            if not content_id:
                return {"error": "content_id is required"}
            piece = update_content(content_id, updates)
            if piece:
                return {"success": True, "content": piece.__dict__}
            return {"error": f"Content {content_id} not found"}

        elif action == "get":
            content_id = request_data.get("content_id", "")
            if not content_id:
                return {"error": "content_id is required"}
            piece = get_content(content_id)
            if piece:
                return {"success": True, "content": piece.__dict__}
            return {"error": f"Content {content_id} not found"}

        elif action == "calendar":
            days = request_data.get("days", 30)
            calendar = get_content_calendar(days=days)
            return {"success": True, "calendar": calendar}

        elif action == "templates":
            templates = {}
            for k, v in CONTENT_TEMPLATES.items():
                templates[k] = {
                    "sections": v["sections"],
                    "tone": v["tone"],
                    "target_words": v["target_words"],
                }
            return {"success": True, "templates": templates}

        elif action == "generate_brief":
            content_type = request_data.get("content_type", "blog")
            topic = request_data.get("topic", "")
            if not topic:
                return {"error": "topic is required"}
            brief = generate_content_brief(content_type=content_type, topic=topic)
            return {"success": True, "brief": brief}

        else:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "create",
                    "update",
                    "get",
                    "calendar",
                    "templates",
                    "generate_brief",
                ],
            }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
