"""
Rube MCP Setup — One-time configuration for Rube MCP server.

Reads RUBE_MCP_URL and RUBE_MCP_TOKEN from environment, builds the
MCP servers config, and writes it into the agent's settings.
Called at startup by initialize.py or run manually.
"""

import json
import os


def get_rube_mcp_config() -> dict | None:
    """Build Rube MCP server config from environment variables."""
    url = os.environ.get("RUBE_MCP_URL", "").strip()
    token = os.environ.get("RUBE_MCP_TOKEN", "").strip()
    if not url or not token:
        return None
    return {
        "name": "rube",
        "description": "Rube AI Tools Platform - full MCP toolkit for web scraping, data extraction, automation, search, code execution, and more",
        "type": "sse",
        "url": url,
        "headers": {
            "Authorization": f"Bearer {token}"
        },
        "init_timeout": 15,
        "tool_timeout": 120,
        "disabled": False
    }


def inject_rube_mcp():
    """Inject Rube MCP config into the agent's MCP settings if not already present."""
    from python.helpers import settings as settings_module
    from python.helpers.print_style import PrintStyle

    rube_config = get_rube_mcp_config()
    if not rube_config:
        PrintStyle(font_color="yellow").print(
            "Rube MCP: RUBE_MCP_URL or RUBE_MCP_TOKEN not set — skipping."
        )
        return False

    try:
        current = settings_module.get_settings()
        mcp_servers_str = current.get("mcp_servers", '{"mcpServers": {}}')

        # Parse existing config
        try:
            parsed = json.loads(mcp_servers_str.strip()) if mcp_servers_str.strip() else {"mcpServers": {}}
        except json.JSONDecodeError:
            parsed = {"mcpServers": {}}

        # Normalize to mcpServers dict format
        if "mcpServers" not in parsed:
            parsed = {"mcpServers": {}}

        # Check if rube is already configured
        if "rube" in parsed["mcpServers"]:
            PrintStyle(font_color="green").print("Rube MCP: Already configured.")
            return True

        # Add Rube MCP
        parsed["mcpServers"]["rube"] = {
            "description": rube_config["description"],
            "type": rube_config["type"],
            "url": rube_config["url"],
            "headers": rube_config["headers"],
            "init_timeout": rube_config["init_timeout"],
            "tool_timeout": rube_config["tool_timeout"],
        }

        # Save back
        new_mcp_str = json.dumps(parsed, indent=2)
        settings_module.set_settings_delta({"mcp_servers": new_mcp_str}, apply=False)

        PrintStyle(
            background_color="#6734C3", font_color="white", bold=True, padding=True
        ).print("Rube MCP: Successfully configured!")
        PrintStyle(font_color="green").print(f"  URL: {rube_config['url']}")
        return True

    except Exception as e:
        PrintStyle(font_color="red").print(f"Rube MCP setup error: {e}")
        return False


if __name__ == "__main__":
    from python.helpers import dotenv
    dotenv.load_dotenv()
    inject_rube_mcp()
