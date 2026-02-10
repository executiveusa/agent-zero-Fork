"""
DesktopCommanderMCP — MCP Server for Desktop Control

Provides Model Context Protocol (MCP) endpoints for desktop automation:
- Window management (list, focus, minimize, maximize, close)
- Application launching and control
- File system operations
- Clipboard operations
- Screen capture
- System commands

Designed to run as a standalone process or sidecar container.
Communicates via stdio MCP protocol.
"""

import os
import sys
import json
import subprocess
import platform
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DesktopCommanderMCP:
    """MCP Server for desktop control operations."""

    def __init__(self):
        self.platform = platform.system()
        self.tools = self._get_tools()

    def _get_tools(self) -> Dict[str, Any]:
        """Define available MCP tools."""
        return {
            "desktop_info": {
                "description": "Get desktop environment information",
                "inputSchema": {"type": "object", "properties": {}},
                "handler": self._desktop_info,
            },
            "list_windows": {
                "description": "List all open windows",
                "inputSchema": {"type": "object", "properties": {}},
                "handler": self._list_windows,
            },
            "focus_window": {
                "description": "Focus a specific window by title",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Window title to focus"},
                    },
                    "required": ["title"],
                },
                "handler": self._focus_window,
            },
            "minimize_window": {
                "description": "Minimize a window by title",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Window title to minimize"},
                    },
                    "required": ["title"],
                },
                "handler": self._minimize_window,
            },
            "maximize_window": {
                "description": "Maximize a window by title",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Window title to maximize"},
                    },
                    "required": ["title"],
                },
                "handler": self._maximize_window,
            },
            "close_window": {
                "description": "Close a window by title",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Window title to close"},
                    },
                    "required": ["title"],
                },
                "handler": self._close_window,
            },
            "launch_app": {
                "description": "Launch an application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app": {"type": "string", "description": "Application name or path"},
                        "args": {"type": "string", "description": "Optional arguments"},
                    },
                    "required": ["app"],
                },
                "handler": self._launch_app,
            },
            "get_clipboard": {
                "description": "Get clipboard content",
                "inputSchema": {"type": "object", "properties": {}},
                "handler": self._get_clipboard,
            },
            "set_clipboard": {
                "description": "Set clipboard content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to set in clipboard"},
                    },
                    "required": ["text"],
                },
                "handler": self._set_clipboard,
            },
            "screenshot": {
                "description": "Take a screenshot",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Save path (optional)"},
                    },
                },
                "handler": self._screenshot,
            },
            "run_command": {
                "description": "Run a system command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "timeout": {"type": "number", "description": "Timeout in seconds (default: 30)"},
                    },
                    "required": ["command"],
                },
                "handler": self._run_command,
            },
            "list_files": {
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                    },
                    "required": ["path"],
                },
                "handler": self._list_files,
            },
        }

    # Tool Handlers

    def _desktop_info(self, args: Dict) -> Dict:
        """Get desktop environment information."""
        return {
            "platform": self.platform,
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    def _list_windows(self, args: Dict) -> Dict:
        """List all open windows."""
        if self.platform == "Windows":
            return self._list_windows_windows()
        elif self.platform == "Darwin":  # macOS
            return self._list_windows_macos()
        elif self.platform == "Linux":
            return self._list_windows_linux()
        else:
            return {"error": f"Unsupported platform: {self.platform}"}

    def _list_windows_windows(self) -> Dict:
        """List windows on Windows."""
        try:
            import win32gui
            windows = []
            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        windows.append({"handle": hwnd, "title": title})
                return True
            win32gui.EnumWindows(enum_handler, None)
            return {"count": len(windows), "windows": windows}
        except ImportError:
            return {"error": "pywin32 not installed. Install with: pip install pywin32"}

    def _list_windows_macos(self) -> Dict:
        """List windows on macOS."""
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of every process whose background only is false'],
                capture_output=True,
                text=True,
                timeout=10
            )
            apps = [app.strip() for app in result.stdout.split(",") if app.strip()]
            return {"count": len(apps), "windows": [{"title": app} for app in apps]}
        except Exception as e:
            return {"error": f"Failed to list windows: {str(e)}"}

    def _list_windows_linux(self) -> Dict:
        """List windows on Linux using wmctrl."""
        try:
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                windows = []
                for line in result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows.append({"title": parts[3]})
                return {"count": len(windows), "windows": windows}
            else:
                return {"error": "wmctrl not available. Install with: sudo apt install wmctrl"}
        except FileNotFoundError:
            return {"error": "wmctrl not found. Install with: sudo apt install wmctrl"}

    def _focus_window(self, args: Dict) -> Dict:
        """Focus a window by title."""
        title = args.get("title", "")
        if not title:
            return {"error": "title is required"}

        if self.platform == "Windows":
            return self._focus_window_windows(title)
        elif self.platform == "Darwin":
            return self._focus_window_macos(title)
        elif self.platform == "Linux":
            return self._focus_window_linux(title)
        else:
            return {"error": f"Unsupported platform: {self.platform}"}

    def _focus_window_windows(self, title: str) -> Dict:
        """Focus window on Windows."""
        try:
            import win32gui
            import win32con

            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if title.lower() in window_title.lower():
                        win32gui.SetForegroundWindow(hwnd)
                        return False
                return True

            win32gui.EnumWindows(enum_handler, None)
            return {"success": True, "title": title}
        except ImportError:
            return {"error": "pywin32 not installed"}

    def _focus_window_macos(self, title: str) -> Dict:
        """Focus window on macOS."""
        try:
            script = f'''
            tell application "System Events"
                tell process 1 whose frontmost is true
                    set frontmost to false
                end tell
            end tell
            tell application "{title}" to activate
            '''
            subprocess.run(["osascript", "-e", script], timeout=10)
            return {"success": True, "title": title}
        except Exception as e:
            return {"error": f"Failed to focus window: {str(e)}"}

    def _focus_window_linux(self, title: str) -> Dict:
        """Focus window on Linux."""
        try:
            result = subprocess.run(
                ["wmctrl", "-a", title],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"success": result.returncode == 0, "title": title}
        except FileNotFoundError:
            return {"error": "wmctrl not found"}

    def _minimize_window(self, args: Dict) -> Dict:
        """Minimize a window by title."""
        title = args.get("title", "")
        if not title:
            return {"error": "title is required"}

        if self.platform == "Windows":
            try:
                import win32gui
                import win32con

                def enum_handler(hwnd, ctx):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title.lower() in window_title.lower():
                            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                            return False
                    return True

                win32gui.EnumWindows(enum_handler, None)
                return {"success": True, "title": title}
            except ImportError:
                return {"error": "pywin32 not installed"}
        else:
            return {"error": f"Minimize not implemented for {self.platform}"}

    def _maximize_window(self, args: Dict) -> Dict:
        """Maximize a window by title."""
        title = args.get("title", "")
        if not title:
            return {"error": "title is required"}

        if self.platform == "Windows":
            try:
                import win32gui
                import win32con

                def enum_handler(hwnd, ctx):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title.lower() in window_title.lower():
                            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                            return False
                    return True

                win32gui.EnumWindows(enum_handler, None)
                return {"success": True, "title": title}
            except ImportError:
                return {"error": "pywin32 not installed"}
        else:
            return {"error": f"Maximize not implemented for {self.platform}"}

    def _close_window(self, args: Dict) -> Dict:
        """Close a window by title."""
        title = args.get("title", "")
        if not title:
            return {"error": "title is required"}

        if self.platform == "Windows":
            try:
                import win32gui
                import win32con

                def enum_handler(hwnd, ctx):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title.lower() in window_title.lower():
                            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                            return False
                    return True

                win32gui.EnumWindows(enum_handler, None)
                return {"success": True, "title": title}
            except ImportError:
                return {"error": "pywin32 not installed"}
        else:
            return {"error": f"Close window not implemented for {self.platform}"}

    def _launch_app(self, args: Dict) -> Dict:
        """Launch an application."""
        app = args.get("app", "")
        app_args = args.get("args", "")

        if not app:
            return {"error": "app is required"}

        try:
            if self.platform == "Windows":
                if app_args:
                    subprocess.Popen([app] + app_args.split(), shell=True)
                else:
                    subprocess.Popen([app], shell=True)
            elif self.platform == "Darwin":
                subprocess.Popen(["open", "-a", app] + ([app_args] if app_args else []))
            elif self.platform == "Linux":
                subprocess.Popen([app] + app_args.split())
            else:
                return {"error": f"Unsupported platform: {self.platform}"}

            return {"success": True, "app": app}
        except Exception as e:
            return {"error": f"Failed to launch app: {str(e)}"}

    def _get_clipboard(self, args: Dict) -> Dict:
        """Get clipboard content."""
        try:
            if self.platform == "Windows":
                import win32clipboard
                win32clipboard.OpenClipboard()
                content = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                return {"content": content}
            elif self.platform == "Darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
                return {"content": result.stdout}
            elif self.platform == "Linux":
                result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=5)
                return {"content": result.stdout}
            else:
                return {"error": f"Unsupported platform: {self.platform}"}
        except Exception as e:
            return {"error": f"Failed to get clipboard: {str(e)}"}

    def _set_clipboard(self, args: Dict) -> Dict:
        """Set clipboard content."""
        text = args.get("text", "")
        if not text:
            return {"error": "text is required"}

        try:
            if self.platform == "Windows":
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
                win32clipboard.CloseClipboard()
            elif self.platform == "Darwin":
                subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
            elif self.platform == "Linux":
                subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, timeout=5)
            else:
                return {"error": f"Unsupported platform: {self.platform}"}

            return {"success": True, "length": len(text)}
        except Exception as e:
            return {"error": f"Failed to set clipboard: {str(e)}"}

    def _screenshot(self, args: Dict) -> Dict:
        """Take a screenshot."""
        try:
            from PIL import ImageGrab
            import time

            path = args.get("path", f"screenshot_{int(time.time())}.png")
            screenshot = ImageGrab.grab()
            screenshot.save(path)
            return {"success": True, "path": path, "size": screenshot.size}
        except ImportError:
            return {"error": "Pillow not installed. Install with: pip install Pillow"}
        except Exception as e:
            return {"error": f"Failed to take screenshot: {str(e)}"}

    def _run_command(self, args: Dict) -> Dict:
        """Run a system command."""
        command = args.get("command", "")
        timeout = args.get("timeout", 30)

        if not command:
            return {"error": "command is required"}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": f"Failed to run command: {str(e)}"}

    def _list_files(self, args: Dict) -> Dict:
        """List files in a directory."""
        path = args.get("path", ".")

        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}

            if not os.path.isdir(path):
                return {"error": f"Path is not a directory: {path}"}

            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                })

            return {"count": len(files), "files": files, "path": path}
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    # MCP Protocol Handlers

    def start(self):
        """Start the MCP stdio server."""
        sys.stderr.write(f"DesktopCommanderMCP started. {len(self.tools)} tools available.\n")
        sys.stderr.flush()

        buffer = ""
        for line in sys.stdin:
            buffer += line
            self._process_buffer(buffer)
            buffer = ""

    def _process_buffer(self, buffer: str):
        """Process incoming MCP messages."""
        lines = buffer.split("\n")
        for line in lines:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
                self._handle_message(message)
            except json.JSONDecodeError:
                sys.stderr.write(f"Invalid JSON: {line[:100]}\n")
                sys.stderr.flush()

    def _handle_message(self, message: Dict):
        """Handle an MCP message."""
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            self._respond(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "desktopcommander-mcp", "version": "1.0.0"},
            })
        elif method == "tools/list":
            tool_list = [
                {"name": name, "description": tool["description"], "inputSchema": tool["inputSchema"]}
                for name, tool in self.tools.items()
            ]
            self._respond(msg_id, {"tools": tool_list})
        elif method == "tools/call":
            self._handle_tool_call(msg_id, params)
        elif method == "notifications/initialized":
            pass
        else:
            self._respond_error(msg_id, -32601, f"Unknown method: {method}")

    def _handle_tool_call(self, msg_id: int, params: Dict):
        """Handle a tool call."""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self.tools:
            self._respond_error(msg_id, -32602, f"Unknown tool: {name}")
            return

        tool = self.tools[name]
        try:
            result = tool["handler"](arguments)
            self._respond(msg_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            self._respond(msg_id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })

    def _respond(self, msg_id: int, result: Dict):
        """Send an MCP response."""
        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()

    def _respond_error(self, msg_id: int, code: int, message: str):
        """Send an MCP error response."""
        response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main():
    """Main entry point."""
    server = DesktopCommanderMCP()
    server.start()


if __name__ == "__main__":
    main()
