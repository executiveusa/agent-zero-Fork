"""
DesktopCommander Tool — Agent Zero wrapper for DesktopCommanderMCP

Provides Agent Zero tool access to desktop automation capabilities:
- Window management (list, focus, minimize, maximize, close)
- Application launching and control
- File system operations
- Clipboard operations
- Screen capture
- System commands

Communicates with DesktopCommanderMCP server via stdio MCP protocol.
"""

import os
import json
import asyncio
import subprocess
import logging
from typing import Optional, Dict, Any

from python.helpers.tool import Tool, Response

logger = logging.getLogger(__name__)


class DesktopCommander(Tool):
    """Agent Zero tool for desktop control via DesktopCommanderMCP."""

    async def execute(self, **kwargs) -> Response:
        """Execute a desktop command."""
        if self.method == "desktop_info":
            return await self._desktop_info(**kwargs)
        elif self.method == "list_windows":
            return await self._list_windows(**kwargs)
        elif self.method == "focus_window":
            return await self._focus_window(**kwargs)
        elif self.method == "minimize_window":
            return await self._minimize_window(**kwargs)
        elif self.method == "maximize_window":
            return await self._maximize_window(**kwargs)
        elif self.method == "close_window":
            return await self._close_window(**kwargs)
        elif self.method == "launch_app":
            return await self._launch_app(**kwargs)
        elif self.method == "get_clipboard":
            return await self._get_clipboard(**kwargs)
        elif self.method == "set_clipboard":
            return await self._set_clipboard(**kwargs)
        elif self.method == "screenshot":
            return await self._screenshot(**kwargs)
        elif self.method == "run_command":
            return await self._run_command(**kwargs)
        elif self.method == "list_files":
            return await self._list_files(**kwargs)
        elif self.method == "status":
            return await self._status(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{self.name}:{self.method}'",
                break_loop=False,
            )

    def _get_mcp_command(self) -> str:
        """Get the command to run the MCP server."""
        # Check if DesktopCommanderMCP server is already running
        # If not, start it as a subprocess
        return f"python {os.path.join(os.path.dirname(__file__), 'desktop_commander_mcp.py')}"

    async def _call_mcp(self, method: str, arguments: Dict[str, Any]) -> Optional[Dict]:
        """Call the MCP server."""
        try:
            # Start the MCP server process
            cmd = self._get_mcp_command()
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send initialize request
            init_msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
            proc.stdin.write(json.dumps(init_msg) + "\n")
            proc.stdin.flush()

            # Read initialize response
            init_response = proc.stdout.readline()
            if not init_response:
                return {"error": "Failed to initialize MCP server"}

            # Send tool call request
            call_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": method, "arguments": arguments},
            }
            proc.stdin.write(json.dumps(call_msg) + "\n")
            proc.stdin.flush()

            # Read tool call response
            tool_response = proc.stdout.readline()
            if not tool_response:
                return {"error": "No response from MCP server"}

            # Parse response
            response_data = json.loads(tool_response)
            result = response_data.get("result", {})
            content = result.get("content", [])

            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                return json.loads(text_content)

            return {"error": "No content in response"}

        except Exception as e:
            logger.error(f"DesktopCommanderMCP error: {e}")
            return {"error": str(e)}

    async def _desktop_info(self, **kwargs) -> Response:
        """Get desktop environment information."""
        result = await self._call_mcp("desktop_info", {})
        if result and "error" not in result:
            return Response(
                message=f"Desktop Info:\n{json.dumps(result, indent=2)}",
                break_loop=False,
            )
        return Response(
            message=f"Error getting desktop info: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _list_windows(self, **kwargs) -> Response:
        """List all open windows."""
        result = await self._call_mcp("list_windows", {})
        if result and "error" not in result:
            count = result.get("count", 0)
            windows = result.get("windows", [])
            message = f"Found {count} windows:\n"
            for win in windows[:20]:  # Limit to first 20
                title = win.get("title", "Unknown")
                message += f"  - {title}\n"
            if count > 20:
                message += f"  ... and {count - 20} more\n"
            return Response(message=message, break_loop=False)
        return Response(
            message=f"Error listing windows: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _focus_window(self, **kwargs) -> Response:
        """Focus a specific window by title."""
        title = self.args.get("title", "")
        if not title:
            return Response(message="Error: 'title' is required.", break_loop=False)

        result = await self._call_mcp("focus_window", {"title": title})
        if result and "error" not in result:
            return Response(
                message=f"Focused window: {title}",
                break_loop=False,
            )
        return Response(
            message=f"Error focusing window: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _minimize_window(self, **kwargs) -> Response:
        """Minimize a window by title."""
        title = self.args.get("title", "")
        if not title:
            return Response(message="Error: 'title' is required.", break_loop=False)

        result = await self._call_mcp("minimize_window", {"title": title})
        if result and "error" not in result:
            return Response(
                message=f"Minimized window: {title}",
                break_loop=False,
            )
        return Response(
            message=f"Error minimizing window: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _maximize_window(self, **kwargs) -> Response:
        """Maximize a window by title."""
        title = self.args.get("title", "")
        if not title:
            return Response(message="Error: 'title' is required.", break_loop=False)

        result = await self._call_mcp("maximize_window", {"title": title})
        if result and "error" not in result:
            return Response(
                message=f"Maximized window: {title}",
                break_loop=False,
            )
        return Response(
            message=f"Error maximizing window: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _close_window(self, **kwargs) -> Response:
        """Close a window by title."""
        title = self.args.get("title", "")
        if not title:
            return Response(message="Error: 'title' is required.", break_loop=False)

        result = await self._call_mcp("close_window", {"title": title})
        if result and "error" not in result:
            return Response(
                message=f"Closed window: {title}",
                break_loop=False,
            )
        return Response(
            message=f"Error closing window: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _launch_app(self, **kwargs) -> Response:
        """Launch an application."""
        app = self.args.get("app", "")
        app_args = self.args.get("args", "")

        if not app:
            return Response(message="Error: 'app' is required.", break_loop=False)

        result = await self._call_mcp("launch_app", {"app": app, "args": app_args})
        if result and "error" not in result:
            return Response(
                message=f"Launched application: {app}",
                break_loop=False,
            )
        return Response(
            message=f"Error launching app: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _get_clipboard(self, **kwargs) -> Response:
        """Get clipboard content."""
        result = await self._call_mcp("get_clipboard", {})
        if result and "error" not in result:
            content = result.get("content", "")
            return Response(
                message=f"Clipboard content:\n{content}",
                break_loop=False,
            )
        return Response(
            message=f"Error getting clipboard: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _set_clipboard(self, **kwargs) -> Response:
        """Set clipboard content."""
        text = self.args.get("text", "")
        if not text:
            return Response(message="Error: 'text' is required.", break_loop=False)

        result = await self._call_mcp("set_clipboard", {"text": text})
        if result and "error" not in result:
            length = result.get("length", 0)
            return Response(
                message=f"Set clipboard ({length} characters)",
                break_loop=False,
            )
        return Response(
            message=f"Error setting clipboard: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _screenshot(self, **kwargs) -> Response:
        """Take a screenshot."""
        path = self.args.get("path", "")

        result = await self._call_mcp("screenshot", {"path": path})
        if result and "error" not in result:
            screenshot_path = result.get("path", "unknown")
            size = result.get("size", [0, 0])
            return Response(
                message=f"Screenshot saved to: {screenshot_path} (size: {size[0]}x{size[1]})",
                break_loop=False,
            )
        return Response(
            message=f"Error taking screenshot: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _run_command(self, **kwargs) -> Response:
        """Run a system command."""
        command = self.args.get("command", "")
        timeout = self.args.get("timeout", 30)

        if not command:
            return Response(message="Error: 'command' is required.", break_loop=False)

        result = await self._call_mcp("run_command", {"command": command, "timeout": timeout})
        if result and "error" not in result:
            success = result.get("success", False)
            returncode = result.get("returncode", -1)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")

            message = f"Command executed (exit code: {returncode})\n"
            if stdout:
                message += f"STDOUT:\n{stdout}\n"
            if stderr:
                message += f"STDERR:\n{stderr}\n"

            return Response(message=message, break_loop=False)
        return Response(
            message=f"Error running command: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _list_files(self, **kwargs) -> Response:
        """List files in a directory."""
        path = self.args.get("path", ".")

        result = await self._call_mcp("list_files", {"path": path})
        if result and "error" not in result:
            count = result.get("count", 0)
            files = result.get("files", [])
            message = f"Found {count} items in '{path}':\n"
            for f in files[:50]:  # Limit to first 50
                name = f.get("name", "unknown")
                ftype = f.get("type", "file")
                size = f.get("size", 0)
                message += f"  [{ftype}] {name} ({size} bytes)\n"
            if count > 50:
                message += f"  ... and {count - 50} more\n"
            return Response(message=message, break_loop=False)
        return Response(
            message=f"Error listing files: {result.get('error', 'Unknown error')}",
            break_loop=False,
        )

    async def _status(self, **kwargs) -> Response:
        """Check DesktopCommanderMCP status."""
        # Try to get desktop info to verify connection
        result = await self._call_mcp("desktop_info", {})
        if result and "error" not in result:
            platform = result.get("platform", "unknown")
            return Response(
                message=f"DesktopCommanderMCP Status: ✓ connected\nPlatform: {platform}",
                break_loop=False,
            )
        return Response(
            message="DesktopCommanderMCP Status: ✗ (connection failed)",
            break_loop=False,
        )
