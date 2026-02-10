"""
Composio MCP Bridge - Local MCP server exposing Composio tools.

Runs a local FastMCP server that wraps Composio's 870+ integrations
as standard MCP tools. This allows subordinate agents and external
MCP clients to consume Composio tools via the MCP protocol.

The bridge is optional -- the primary path is composio_tool.py which
calls the SDK directly. This bridge exists for MCP interoperability.

Starts on port 18850 by default (configurable via COMPOSIO_MCP_PORT).
"""

import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

_bridge_thread = None
_bridge_running = False

# Top toolkits to expose via MCP (curated for Agent Claw use cases)
DEFAULT_TOOLKITS = [
    "GITHUB",
    "GMAIL",
    "GOOGLECALENDAR",
    "GOOGLEDRIVE",
    "GOOGLESHEETS",
    "SLACK",
    "NOTION",
    "JIRA",
    "LINEAR",
    "TRELLO",
    "HUBSPOT",
    "STRIPE",
    "SHOPIFY",
    "TWITTER",
    "LINKEDIN",
    "YOUTUBE",
    "DISCORD",
    "TELEGRAM_BOT",
    "TWILIO",
    "HACKERNEWS",
    "FIRECRAWL",
    "BREVO",
    "CALENDLY",
    "CLICKUP",
    "ASANA",
    "AIRTABLE",
    "SUPABASE",
    "DROPBOX",
    "ONEDRIVE",
    "ZENDESK",
]


def start_composio_mcp_bridge():
    """
    Start the Composio MCP bridge server in a background thread.

    This creates a local FastMCP server that exposes a curated set of
    Composio tools as MCP-compatible endpoints.
    """
    global _bridge_thread, _bridge_running

    if _bridge_running:
        logger.info("Composio MCP bridge already running.")
        return True

    api_key = os.environ.get("COMPOSIO_API_KEY", "").strip()
    if not api_key:
        logger.info("Composio MCP bridge: No API key, skipping.")
        return False

    port = int(os.environ.get("COMPOSIO_MCP_PORT", "18850"))

    def _run_bridge():
        global _bridge_running
        try:
            from fastmcp import FastMCP

            mcp = FastMCP(
                "composio-bridge",
                instructions="Composio AI Tools Platform - 870+ app integrations. "
                "Execute actions on GitHub, Gmail, Slack, Calendar, Notion, Jira, and more.",
            )

            @mcp.tool()
            def composio_execute(action: str, params: str = "{}") -> str:
                """Execute a Composio action.

                Args:
                    action: Action slug like GITHUB_CREATE_ISSUE, GMAIL_SEND_EMAIL, etc.
                    params: JSON string of action parameters.

                Returns:
                    JSON result of the action execution.
                """
                from python.helpers.composio_setup import execute_composio_action

                try:
                    params_dict = json.loads(params)
                except json.JSONDecodeError:
                    return json.dumps({"error": f"Invalid JSON params: {params[:200]}"})

                result = execute_composio_action(action=action, params=params_dict)
                return json.dumps(result, default=str)

            @mcp.tool()
            def composio_search(app: str, use_case: str) -> str:
                """Find Composio actions by app and use case.

                Args:
                    app: App name like GITHUB, GMAIL, SLACK.
                    use_case: Natural language description of what you want to do.

                Returns:
                    JSON list of matching actions.
                """
                from python.helpers.composio_setup import find_actions_for_use_case

                actions = find_actions_for_use_case(app.upper(), use_case)
                return json.dumps(actions, default=str)

            @mcp.tool()
            def composio_schema(action: str) -> str:
                """Get the parameter schema for a Composio action.

                Args:
                    action: Action slug like GITHUB_CREATE_ISSUE.

                Returns:
                    JSON schema for the action's parameters.
                """
                from python.helpers.composio_setup import get_action_schema

                schema = get_action_schema(action)
                return json.dumps(schema or {"error": "Schema not found"}, default=str)

            @mcp.tool()
            def composio_apps() -> str:
                """List all available Composio apps/toolkits.

                Returns:
                    JSON list of available app names.
                """
                from python.helpers.composio_setup import get_available_apps

                apps = get_available_apps()
                return json.dumps({"apps": apps, "count": len(apps)})

            _bridge_running = True
            logger.info(f"Composio MCP bridge starting on port {port}")

            # Run the SSE server
            mcp.run(transport="sse", host="127.0.0.1", port=port)

        except Exception as e:
            _bridge_running = False
            logger.warning(f"Composio MCP bridge failed: {e}")

    _bridge_thread = threading.Thread(
        target=_run_bridge, daemon=True, name="composio-mcp-bridge"
    )
    _bridge_thread.start()

    return True


def get_bridge_mcp_config(port: int | None = None) -> dict | None:
    """
    Get the MCP server config dict for the local Composio bridge.

    Returns a config suitable for injection into mcpServers settings.
    Returns None if the bridge is not running.
    """
    if not _bridge_running:
        return None

    port = port or int(os.environ.get("COMPOSIO_MCP_PORT", "18850"))

    return {
        "description": "Composio Sovereign AI - 870+ app integrations via local MCP bridge",
        "type": "sse",
        "url": f"http://127.0.0.1:{port}/sse",
        "headers": {},
        "init_timeout": 10,
        "tool_timeout": 120,
    }
