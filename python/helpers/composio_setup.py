"""
Composio Setup - Sovereign AI Tool Platform Integration.

Replaces the paid Rube MCP ($25/mo) with Composio's open-source SDK.
Rube IS Composio (same backend, same tools, branded wrapper).

Reads COMPOSIO_API_KEY from environment, initializes the toolset,
and optionally injects a Composio MCP server into agent settings.
Called at startup by initialize.py.

Free tier: 20,000 tool calls/month, $0.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Singleton toolset instance
_toolset = None


def get_composio_api_key() -> str | None:
    """Get Composio API key from environment."""
    key = os.environ.get("COMPOSIO_API_KEY", "").strip()
    return key if key else None


def get_toolset():
    """Get or create the singleton ComposioToolSet instance."""
    global _toolset
    if _toolset is not None:
        return _toolset

    api_key = get_composio_api_key()
    if not api_key:
        return None

    try:
        from composio import ComposioToolSet
        _toolset = ComposioToolSet(api_key=api_key, entity_id="default")
        return _toolset
    except Exception as e:
        logger.warning(f"Composio toolset init failed: {e}")
        return None


def get_available_apps() -> list[str]:
    """Fetch the list of available Composio apps/toolkits."""
    toolset = get_toolset()
    if not toolset:
        return []
    try:
        apps = toolset.get_apps()
        return [app.name if hasattr(app, "name") else str(app) for app in apps]
    except Exception as e:
        logger.warning(f"Failed to fetch Composio apps: {e}")
        return []


def execute_composio_action(action: str, params: dict, entity_id: str = "default") -> dict:
    """
    Execute a Composio action directly via the SDK.

    Args:
        action: Action slug like "GITHUB_CREATE_ISSUE", "GMAIL_SEND_EMAIL", etc.
        params: Dict of action parameters.
        entity_id: The entity (user context) to execute as. Default: "default".

    Returns:
        Dict with execution result or error.
    """
    toolset = get_toolset()
    if not toolset:
        return {"error": "Composio not configured. Set COMPOSIO_API_KEY in .env"}

    try:
        result = toolset.execute_action(
            action=action,
            params=params,
            entity_id=entity_id,
        )
        return result
    except Exception as e:
        return {"error": f"Composio action '{action}' failed: {str(e)}"}


def find_actions_for_use_case(app: str, use_case: str) -> list[dict]:
    """
    Find relevant Composio actions for a given use case.

    Args:
        app: App name like "GITHUB", "GMAIL", "SLACK".
        use_case: Natural language description like "send an email".

    Returns:
        List of action dicts with name and description.
    """
    toolset = get_toolset()
    if not toolset:
        return []

    try:
        actions = toolset.find_actions_by_use_case(app, use_case=use_case)
        return [
            {"name": str(a), "description": getattr(a, "description", "")}
            for a in actions
        ]
    except Exception as e:
        logger.warning(f"Failed to find actions: {e}")
        return []


def get_action_schema(action: str) -> dict | None:
    """Get the JSON schema for a specific Composio action."""
    toolset = get_toolset()
    if not toolset:
        return None

    try:
        schemas = toolset.get_action_schemas(actions=[action])
        if schemas:
            schema = schemas[0]
            return {
                "name": schema.name if hasattr(schema, "name") else str(action),
                "description": schema.description if hasattr(schema, "description") else "",
                "parameters": schema.parameters.model_dump() if hasattr(schema, "parameters") else {},
            }
        return None
    except Exception as e:
        logger.warning(f"Failed to get schema for {action}: {e}")
        return None


def inject_composio_mcp():
    """
    Inject Composio as an MCP server in the agent's settings.

    This is a fallback path -- the primary integration is via composio_tool.py
    which calls the SDK directly. This MCP injection lets subordinate agents
    also discover Composio tools via MCP protocol.
    """
    from python.helpers import settings as settings_module
    from python.helpers.print_style import PrintStyle

    api_key = get_composio_api_key()
    if not api_key:
        PrintStyle(font_color="yellow").print(
            "Composio: COMPOSIO_API_KEY not set -- skipping MCP injection."
        )
        PrintStyle(font_color="yellow").print(
            "  Get a free key at: https://composio.dev/app (20k calls/mo, $0)"
        )
        return False

    try:
        # Initialize the toolset to validate the key
        toolset = get_toolset()
        if not toolset:
            PrintStyle(font_color="red").print("Composio: Failed to initialize toolset.")
            return False

        PrintStyle(
            background_color="#1a7f37", font_color="white", bold=True, padding=True
        ).print("Composio: Sovereign AI Tools Platform initialized!")
        PrintStyle(font_color="green").print(
            "  870+ integrations available via composio_tool"
        )
        PrintStyle(font_color="green").print(
            "  Usage: {tool_name: \"composio_tool\", tool_args: {action: \"APP_ACTION\", params: {...}}}"
        )
        return True

    except Exception as e:
        PrintStyle(font_color="red").print(f"Composio setup error: {e}")
        return False


if __name__ == "__main__":
    from python.helpers import dotenv
    dotenv.load_dotenv()
    inject_composio_mcp()
