# DesktopCommanderMCP Usage Guide

## Overview

DesktopCommanderMCP is a Model Context Protocol (MCP) server that provides Agent Zero with desktop automation capabilities. It enables control over windows, applications, file system, clipboard, screenshots, and system commands.

## Installation

### Prerequisites

Install platform-specific dependencies:

**Windows:**

```bash
pip install pywin32
```

**macOS:**

```bash
# No additional packages required (uses built-in osascript)
```

**Linux:**

```bash
sudo apt install wmctrl xclip
```

**Optional (for screenshots):**

```bash
pip install Pillow
```

### Files

The integration consists of three main files:

1. **MCP Server**: [`python/tools/desktop_commander_mcp.py`](python/tools/desktop_commander_mcp.py)
   - Standalone MCP server for desktop control
   - Can run independently or as a subprocess

2. **Agent Zero Tool**: [`python/tools/desktop_commander.py`](python/tools/desktop_commander.py)
   - Wrapper tool that communicates with the MCP server
   - Integrates with Agent Zero's tool system

3. **Configuration**: [`conf/mcp_servers.yaml`](conf/mcp_servers.yaml)
   - MCP server registration and configuration
   - Platform-specific requirements

## Available Tools

### Window Management

#### `desktop_commander:list_windows`

List all open windows on the desktop.

```json
{
  "tool_name": "desktop_commander:list_windows",
  "tool_args": {}
}
```

**Response:**

```
Found 5 windows:
  - Agent Zero - VS Code
  - Chrome
  - Notepad
  - File Explorer
  - Discord
```

#### `desktop_commander:focus_window`

Focus a specific window by title (partial match supported).

```json
{
  "tool_name": "desktop_commander:focus_window",
  "tool_args": {
    "title": "Chrome"
  }
}
```

#### `desktop_commander:minimize_window`

Minimize a window by title.

```json
{
  "tool_name": "desktop_commander:minimize_window",
  "tool_args": {
    "title": "Notepad"
  }
}
```

#### `desktop_commander:maximize_window`

Maximize a window by title.

```json
{
  "tool_name": "desktop_commander:maximize_window",
  "tool_args": {
    "title": "VS Code"
  }
}
```

#### `desktop_commander:close_window`

Close a window by title.

```json
{
  "tool_name": "desktop_commander:close_window",
  "tool_args": {
    "title": "Calculator"
  }
}
```

### Application Control

#### `desktop_commander:launch_app`

Launch an application by name or path.

```json
{
  "tool_name": "desktop_commander:launch_app",
  "tool_args": {
    "app": "notepad.exe",
    "args": ""
  }
}
```

**Examples:**

- Windows: `"notepad.exe"`, `"calc.exe"`, `"C:\\Program Files\\App\\app.exe"`
- macOS: `"Safari"`, `"TextEdit"`, `"/Applications/App.app"`
- Linux: `"firefox"`, `"gedit"`, `"/usr/bin/app"`

### Clipboard Operations

#### `desktop_commander:get_clipboard`

Get current clipboard content.

```json
{
  "tool_name": "desktop_commander:get_clipboard",
  "tool_args": {}
}
```

#### `desktop_commander:set_clipboard`

Set clipboard content.

```json
{
  "tool_name": "desktop_commander:set_clipboard",
  "tool_args": {
    "text": "Hello from Agent Zero!"
  }
}
```

### File System

#### `desktop_commander:list_files`

List files in a directory.

```json
{
  "tool_name": "desktop_commander:list_files",
  "tool_args": {
    "path": "C:/Users/execu/Documents"
  }
}
```

**Response:**

```
Found 10 items in 'C:/Users/execu/Documents':
  [file] readme.txt (1024 bytes)
  [directory] projects (0 bytes)
  [file] notes.md (512 bytes)
  ...
```

### System Commands

#### `desktop_commander:run_command`

Run a system command (use with caution).

```json
{
  "tool_name": "desktop_commander:run_command",
  "tool_args": {
    "command": "dir",
    "timeout": 30
  }
}
```

**Security Warning:** This tool can execute arbitrary commands. Use only when explicitly requested by the user.

### Screenshots

#### `desktop_commander:screenshot`

Take a screenshot and save to file.

```json
{
  "tool_name": "desktop_commander:screenshot",
  "tool_args": {
    "path": "screenshot.png"
  }
}
```

**Response:**

```
Screenshot saved to: screenshot_1234567890.png (size: 1920x1080)
```

### System Information

#### `desktop_commander:desktop_info`

Get desktop environment information.

```json
{
  "tool_name": "desktop_commander:desktop_info",
  "tool_args": {}
}
```

**Response:**

```
Desktop Info:
{
  "platform": "Windows",
  "platform_version": "10.0.19045",
  "machine": "AMD64",
  "processor": "Intel64 Family 6 Model 158",
  "python_version": "3.11.0"
}
```

#### `desktop_commander:status`

Check DesktopCommanderMCP service connectivity.

```json
{
  "tool_name": "desktop_commander:status",
  "tool_args": {}
}
```

## Platform Support

| Feature         | Windows | macOS | Linux |
| --------------- | ------- | ----- | ----- |
| List Windows    | ✅      | ✅    | ✅    |
| Focus Window    | ✅      | ✅    | ✅    |
| Minimize Window | ✅      | ❌    | ❌    |
| Maximize Window | ✅      | ❌    | ❌    |
| Close Window    | ✅      | ❌    | ❌    |
| Launch App      | ✅      | ✅    | ✅    |
| Clipboard       | ✅      | ✅    | ✅    |
| List Files      | ✅      | ✅    | ✅    |
| Run Command     | ✅      | ✅    | ✅    |
| Screenshot      | ✅      | ✅    | ✅    |

**Requirements:**

- Windows: `pywin32` package
- macOS: Built-in `osascript`
- Linux: `wmctrl`, `xclip` packages
- All platforms: `Pillow` (optional, for screenshots)

## Security Considerations

DesktopCommanderMCP provides powerful system access capabilities:

1. **Window Control**: Can manipulate any open window
2. **Application Launching**: Can start any installed application
3. **File System**: Can read directory contents
4. **System Commands**: Can execute arbitrary shell commands
5. **Clipboard**: Can read and write clipboard content

**Best Practices:**

- Always confirm with the user before performing sensitive operations
- Use partial window titles carefully to avoid unintended matches
- Be cautious with `run_command` - validate commands before execution
- Consider the security implications of clipboard access

## Troubleshooting

### "pywin32 not installed"

**Solution:** Install pywin32:

```bash
pip install pywin32
```

### "wmctrl not found" (Linux)

**Solution:** Install wmctrl:

```bash
sudo apt install wmctrl xclip
```

### "Pillow not installed" (Screenshot)

**Solution:** Install Pillow:

```bash
pip install Pillow
```

### MCP server not responding

**Solution:** Check that the MCP server is running:

```bash
python python/tools/desktop_commander_mcp.py
```

### Window not found

**Solution:** Use `list_windows` first to see exact window titles, then use partial matching.

## Integration with Agent Zero

The DesktopCommander tool is automatically available to all agents in Agent Zero. To use it:

1. Agent requests a desktop operation
2. Agent Zero calls the appropriate `desktop_commander:*` method
3. The tool communicates with the MCP server
4. Results are returned to the agent

### Example Workflow

```
User: "Open Chrome and take a screenshot"

Agent:
1. Calls desktop_commander:launch_app with app="chrome.exe"
2. Waits for app to launch
3. Calls desktop_commander:screenshot
4. Returns screenshot path to user
```

## Configuration

Edit [`conf/mcp_servers.yaml`](conf/mcp_servers.yaml) to customize:

```yaml
servers:
  desktopcommander:
    enabled: true # Enable/disable the server
    command: "python" # Command to run the server
    args:
      - "python/tools/desktop_commander_mcp.py"
```

## Development

### Running the MCP Server Standalone

For testing or development, run the MCP server directly:

```bash
python python/tools/desktop_commander_mcp.py
```

The server will start and listen for MCP protocol messages on stdin/stdout.

### Adding New Tools

To add a new desktop control capability:

1. Add the tool definition to `_get_tools()` in `desktop_commander_mcp.py`
2. Implement the handler method
3. Add the corresponding method to `desktop_commander.py`
4. Update the prompt documentation in `prompts/agent.system.tool.desktop_commander.md`

## License

DesktopCommanderMCP is part of Agent Zero and follows the same license terms.

## Support

For issues or questions:

- Check the Agent Zero documentation
- Review the MCP protocol specification
- Examine logs for error messages
