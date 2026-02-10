"""
Composio Tool - Sovereign AI Tool Platform (870+ integrations).

Replaces the paid Rube MCP service ($25/mo) with Composio's open-source SDK.
Gives Agent Zero direct access to GitHub, Gmail, Slack, Google Calendar,
Notion, Jira, Sheets, Stripe, Shopify, HubSpot, and 860+ more apps.

Methods:
    execute  - Execute a specific Composio action
    search   - Find actions by use case (natural language)
    schema   - Get the parameter schema for an action
    apps     - List available apps/toolkits

Usage examples:
    {tool_name: "composio_tool", tool_args: {action: "GITHUB_CREATE_ISSUE", params: '{"owner":"user","repo":"myrepo","title":"Bug fix","body":"Details..."}'}}
    {tool_name: "composio_tool:search", tool_args: {app: "GMAIL", use_case: "send an email with attachment"}}
    {tool_name: "composio_tool:schema", tool_args: {action: "SLACK_SEND_MESSAGE"}}
    {tool_name: "composio_tool:apps", tool_args: {}}
"""

import json
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle


class ComposioTool(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "execute"

        if method == "execute":
            return await self._execute_action(**kwargs)
        elif method == "search":
            return await self._search_actions(**kwargs)
        elif method == "schema":
            return await self._get_schema(**kwargs)
        elif method == "apps":
            return await self._list_apps(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{method}'. Available: execute, search, schema, apps",
                break_loop=False,
            )

    async def _execute_action(self, **kwargs) -> Response:
        """Execute a Composio action."""
        from python.helpers.composio_setup import execute_composio_action

        action = self.args.get("action", "").strip()
        if not action:
            return Response(
                message="Error: 'action' is required. Example: GITHUB_CREATE_ISSUE, GMAIL_SEND_EMAIL, SLACK_SEND_MESSAGE.\n"
                "Use composio_tool:search to find the right action for your use case.\n"
                "Use composio_tool:apps to see all available apps.",
                break_loop=False,
            )

        # Parse params - can be a JSON string or already a dict
        params_raw = self.args.get("params", "{}")
        if isinstance(params_raw, str):
            try:
                params = json.loads(params_raw)
            except json.JSONDecodeError:
                return Response(
                    message=f"Error: 'params' must be valid JSON. Got: {params_raw[:200]}",
                    break_loop=False,
                )
        else:
            params = params_raw if isinstance(params_raw, dict) else {}

        entity_id = self.args.get("entity_id", "default")

        self.set_progress(f"Executing Composio action: {action}...")

        result = execute_composio_action(
            action=action,
            params=params,
            entity_id=entity_id,
        )

        if isinstance(result, dict) and "error" in result:
            return Response(
                message=f"Composio error: {result['error']}",
                break_loop=False,
            )

        # Format result
        if isinstance(result, dict):
            result_text = json.dumps(result, indent=2, default=str)
        else:
            result_text = str(result)

        # Truncate very long results
        if len(result_text) > 8000:
            result_text = result_text[:8000] + "\n... (truncated)"

        return Response(
            message=f"Composio action '{action}' executed successfully:\n{result_text}",
            break_loop=False,
        )

    async def _search_actions(self, **kwargs) -> Response:
        """Search for Composio actions by use case."""
        from python.helpers.composio_setup import find_actions_for_use_case

        app = self.args.get("app", "").strip().upper()
        use_case = self.args.get("use_case", "").strip()

        if not app or not use_case:
            return Response(
                message="Error: Both 'app' and 'use_case' are required.\n"
                "Example: {app: \"GITHUB\", use_case: \"create a new issue\"}",
                break_loop=False,
            )

        self.set_progress(f"Searching {app} actions for: {use_case}...")

        actions = find_actions_for_use_case(app, use_case)

        if not actions:
            return Response(
                message=f"No actions found for app '{app}' matching '{use_case}'.\n"
                "Try a broader use case description or check the app name with composio_tool:apps.",
                break_loop=False,
            )

        lines = [f"Found {len(actions)} matching actions for {app}:\n"]
        for a in actions[:20]:  # limit to top 20
            name = a.get("name", "unknown")
            desc = a.get("description", "")
            lines.append(f"  - {name}: {desc[:120]}")

        return Response(
            message="\n".join(lines),
            break_loop=False,
        )

    async def _get_schema(self, **kwargs) -> Response:
        """Get the parameter schema for a specific action."""
        from python.helpers.composio_setup import get_action_schema

        action = self.args.get("action", "").strip()
        if not action:
            return Response(
                message="Error: 'action' is required. Example: GITHUB_CREATE_ISSUE",
                break_loop=False,
            )

        self.set_progress(f"Fetching schema for: {action}...")

        schema = get_action_schema(action)
        if not schema:
            return Response(
                message=f"No schema found for action '{action}'. Check the action name.",
                break_loop=False,
            )

        return Response(
            message=f"Schema for {action}:\n{json.dumps(schema, indent=2, default=str)}",
            break_loop=False,
        )

    async def _list_apps(self, **kwargs) -> Response:
        """List all available Composio apps."""
        from python.helpers.composio_setup import get_available_apps

        self.set_progress("Fetching available Composio apps...")

        apps = get_available_apps()
        if not apps:
            return Response(
                message="No apps available. Check COMPOSIO_API_KEY in .env.\n"
                "Get a free key at: https://composio.dev/app (20k calls/mo, $0)",
                break_loop=False,
            )

        # Group into columns for readability
        lines = [f"Composio: {len(apps)} apps/toolkits available:\n"]
        # Show first 100 alphabetically
        sorted_apps = sorted(apps)
        for i in range(0, min(len(sorted_apps), 100), 4):
            row = sorted_apps[i:i+4]
            lines.append("  " + "  ".join(f"{a:<25}" for a in row))

        if len(sorted_apps) > 100:
            lines.append(f"\n  ... and {len(sorted_apps) - 100} more.")

        lines.append("\nUse composio_tool:search to find specific actions within an app.")

        return Response(
            message="\n".join(lines),
            break_loop=False,
        )
