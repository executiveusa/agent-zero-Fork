## desktop_commander: Desktop Control via DesktopCommanderMCP

Control your desktop environment through Agent Zero — window management, app launching, file operations, clipboard, screenshots, and system commands.

**Methods:**

- `desktop_info` — Get desktop environment information
- `list_windows` — List all open windows
- `focus_window` — Focus a specific window by title
- `minimize_window` — Minimize a window by title
- `maximize_window` — Maximize a window by title
- `close_window` — Close a window by title
- `launch_app` — Launch an application
- `get_clipboard` — Get clipboard content
- `set_clipboard` — Set clipboard content
- `screenshot` — Take a screenshot
- `run_command` — Run a system command
- `list_files` — List files in a directory
- `status` — Check DesktopCommanderMCP connectivity

### desktop_commander:desktop_info

Get desktop environment information (platform, version, etc.).

```json
{
  "tool_name": "desktop_commander:desktop_info",
  "tool_args": {}
}
```

### desktop_commander:list_windows

List all open windows on the desktop.

```json
{
  "tool_name": "desktop_commander:list_windows",
  "tool_args": {}
}
```

### desktop_commander:focus_window

Focus a specific window by title (partial match supported).

```json
{
  "tool_name": "desktop_commander:focus_window",
  "tool_args": {
    "title": "Chrome"
  }
}
```

### desktop_commander:minimize_window

Minimize a window by title.

```json
{
  "tool_name": "desktop_commander:minimize_window",
  "tool_args": {
    "title": "Notepad"
  }
}
```

### desktop_commander:maximize_window

Maximize a window by title.

```json
{
  "tool_name": "desktop_commander:maximize_window",
  "tool_args": {
    "title": "VS Code"
  }
}
```

### desktop_commander:close_window

Close a window by title.

```json
{
  "tool_name": "desktop_commander:close_window",
  "tool_args": {
    "title": "Calculator"
  }
}
```

### desktop_commander:launch_app

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

### desktop_commander:get_clipboard

Get current clipboard content.

```json
{
  "tool_name": "desktop_commander:get_clipboard",
  "tool_args": {}
}
```

### desktop_commander:set_clipboard

Set clipboard content.

```json
{
  "tool_name": "desktop_commander:set_clipboard",
  "tool_args": {
    "text": "Hello from Agent Zero!"
  }
}
```

### desktop_commander:screenshot

Take a screenshot and save to file.

```json
{
  "tool_name": "desktop_commander:screenshot",
  "tool_args": {
    "path": "screenshot.png"
  }
}
```

### desktop_commander:run_command

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

### desktop_commander:list_files

List files in a directory.

```json
{
  "tool_name": "desktop_commander:list_files",
  "tool_args": {
    "path": "C:/Users/execu/Documents"
  }
}
```

### desktop_commander:status

Check DesktopCommanderMCP service connectivity.

```json
{
  "tool_name": "desktop_commander:status",
  "tool_args": {}
}
```

**Platform Support:**

- Windows: Full support (requires pywin32)
- macOS: Full support (uses osascript)
- Linux: Partial support (requires wmctrl, xclip)

**Security Note:**
DesktopCommanderMCP provides powerful system access. Use with caution and only when explicitly requested by the user.
