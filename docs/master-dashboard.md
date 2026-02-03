# Master Dashboard Documentation

## Overview

The Master Dashboard is a high-tech, "always-on" control plane for Agent Zero that provides comprehensive observability and control over all agent operations. It replaces wondering "what is happening" with real-time visibility into:

* Active contexts and chats
* Task scheduler operations
* Live agent view (browser automation screenshots)
* Beads timeline (structured log visualization)
* System health and status
* All backend capabilities

**Repository Grounding**: This dashboard is built exclusively for the `agent-zero-Fork` repository and uses only APIs that exist in `python/api/*.py`.

---

## Features

### ✅ Implemented (Repo-Grounded)

#### Core Observability
* **Beads Timeline**: Real-time log visualization from `/poll` endpoint
  * Filter by type (error, warning, tool, code_exe, browser, progress, response, agent)
  * Search functionality
  * Hide temporary logs
  * Export to JSON
  * Color-coded by operational state

* **Live View**: Agent browser automation observation
  * Screenshots from `browser_agent.py` (via `/image_get`)
  * Step narration from progress logs
  * Current tool display
  * Blockers and errors panel

#### Context & Chat Management
* Create, load, reset, remove chats (`/chat_*` endpoints)
* Message sending (async via `/message_async`)
* History viewing (`/history_get`)
* Pause/resume/nudge controls
* Context selection and switching

#### Task Scheduler
* Full CRUD for tasks (`/scheduler_*` endpoints)
* Task types: adhoc, scheduled, planned
* State management: idle, running, disabled, error
* Filter by type, state, project
* Run now, enable/disable actions
* Manual tick trigger

#### Projects
* Project listing (`/projects`)
* Color-coded project badges
* Filter contexts and tasks by project

#### Memory & Knowledge
* Memory dashboard viewer (`/memory_dashboard`)
* Human approval warnings for edits
* Knowledge import/reindex/path (`/import_knowledge`, `/knowledge_reindex`, `/knowledge_path_get`)

#### Files
* Work directory browser (`/get_work_dir_files`)
* Upload/download/delete operations
* Image preview via `/image_get`
* Sort and filter capabilities

#### MCP Servers
* Server status monitoring (`/mcp_servers_status`)
* Configuration application (`/mcp_servers_apply`)
* Server detail view (`/mcp_server_get_detail`)
* Log viewer (`/mcp_server_get_log`)

#### Backups
* Create, inspect, restore, test operations
* All backup endpoints (`/backup_*`)
* Confirmation gates for destructive operations

#### Notifications
* Global notification system
* History, mark read, clear operations
* Unread count badges

#### Settings
* Settings viewer/editor (`/settings_get`, `/settings_set`)
* Security warnings
* No token exposure

### 🔄 Mission Control Panel

The default landing page provides:
* **Now Playing**: Current agent activity
* **Recent Beads**: Last 3 log items
* **Critical Alerts**: Errors and warnings
* **Active Contexts**: Running chat sessions
* **Running Tasks**: Currently executing scheduler tasks
* **System Health**: Backend status check

### 🎨 Operational State Colors

This dashboard follows a strict color-coding system:

| State | Color | Usage |
|-------|-------|-------|
| IDLE | Green (`#10b981`) | No activity, ready |
| PLANNING | Cyan (`#06b6d4`) | Agent is planning |
| RUNNING | Blue (`#3b82f6`) | Active execution |
| WAITING | Amber (`#f59e0b`) | Pending approval/input |
| PAUSED | Purple (`#8b5cf6`) | Manually paused |
| ERROR | Red (`#ef4444`) | Error state |
| OFFLINE | Gray (`#6b7280`) | Disconnected |

---

## Architecture

### Frontend (Browser)

```
webui/
├── master-dashboard.html          # Main HTML structure
├── css/
│   └── master-dashboard.css       # Styling and theme
└── js/master-dashboard/
    ├── main.js                    # Entry point & coordination
    ├── api.js                     # Backend API communication layer
    ├── state.js                   # Centralized state management
    ├── beads.js                   # Beads timeline component
    ├── live-view.js               # Live agent view component
    ├── panels.js                  # Panel switching and management
    └── toast.js                   # Toast notifications
```

### Backend (Flask)

The dashboard communicates with Agent Zero's existing Flask server:

* **Server**: `run_ui.py` (Flask app)
* **API Pattern**: `python/api/<name>.py` → `/<name>` endpoint
* **Mounted Routes**: `/mcp` (MCP server), `/a2a` (A2A protocol)
* **Authentication**: Session-based auth + CSRF protection (inherited from existing `/webui`)
* **Real-time**: Polling via `/poll` endpoint (750ms default, adaptive)

### Data Flow

```
Browser → Master Dashboard → Flask (run_ui.py) → python/api/*.py → Agent Core
                ↓
            /poll (750ms)
                ↓
        Update UI in real-time
```

---

## API Mapping (Repo-Grounded)

All endpoints are implemented in `python/api/*.py`:

### Core Operations
* `/health` - Backend health check
* `/poll` - Real-time state polling
* `/message` - Send message (sync)
* `/message_async` - Send message (async)
* `/pause` - Pause/resume agent
* `/nudge` - Nudge agent to continue

### Chat Management
* `/chat_create` - Create new chat
* `/chat_load` - Load existing chat
* `/chat_reset` - Reset chat
* `/chat_remove` - Remove chat
* `/chat_export` - Export chat history
* `/history_get` - Get chat history

### Scheduler
* `/scheduler_tasks_list` - List all tasks
* `/scheduler_task_create` - Create new task
* `/scheduler_task_update` - Update task
* `/scheduler_task_run` - Run task now
* `/scheduler_task_delete` - Delete task
* `/scheduler_tick` - Manual scheduler tick

### Files
* `/get_work_dir_files` - List work directory files
* `/download_work_dir_file` - Download file
* `/delete_work_dir_file` - Delete file
* `/file_info` - Get file metadata
* `/image_get` - Serve images/screenshots
* `/upload` - Upload files

### Knowledge & Memory
* `/import_knowledge` - Import knowledge files
* `/knowledge_reindex` - Reindex knowledge base
* `/knowledge_path_get` - Get knowledge path
* `/memory_dashboard` - View memory state

### MCP Servers
* `/mcp_servers_status` - Get all server statuses
* `/mcp_servers_apply` - Apply new configuration
* `/mcp_server_get_detail` - Get server details
* `/mcp_server_get_log` - Get server logs

### Backups
* `/backup_get_defaults` - Get default settings
* `/backup_create` - Create backup
* `/backup_preview_grouped` - Preview grouped backups
* `/backup_inspect` - Inspect backup
* `/backup_restore_preview` - Preview restore
* `/backup_restore` - Restore from backup
* `/backup_test` - Test backup validity

### Notifications
* `/notification_create` - Create notification
* `/notifications_history` - Get history
* `/notifications_mark_read` - Mark as read
* `/notifications_clear` - Clear notifications

### Settings
* `/settings_get` - Get all settings
* `/settings_set` - Update settings
* `/csrf_token` - Get CSRF token

### Other
* `/projects` - Get projects
* `/transcribe` - Speech to text (if configured)
* `/synthesize` - Text to speech (if configured)
* `/tunnel` - Tunnel management
* `/tunnel_proxy` - Tunnel proxy status

---

## Usage

### Accessing the Dashboard

1. Start Agent Zero backend:
   ```bash
   python run_ui.py
   ```

2. Open browser to:
   ```
   http://localhost:<WEB_UI_PORT>/master-dashboard.html
   ```

3. The dashboard will:
   * Auto-connect to backend
   * Start polling at 750ms
   * Display connection status
   * Load all contexts and tasks

### Navigation

**Left Sidebar**: Primary navigation
* Mission Control (default landing page)
* Beads Timeline
* Live View
* Chats
* Scheduler
* Projects
* Memory
* Knowledge
* Files
* MCP Servers
* A2A / Agent Mail (NEW)
* Backups
* Notifications
* Settings

**Top Bar**: Always visible
* Connection status (online/offline, last update time)
* Active context selector
* Current progress indicator
* Pause/Resume button
* Error badge (shows active errors)
* Autonomy level slider (Tier 0-4)

**Right Panel**: Inspector (context-sensitive)
* Shows details of selected items
* Bead details when clicked
* Task details
* File previews

### Polling Behavior

The dashboard uses **adaptive polling**:

* **Active (500ms)**: When `log_progress_active` is true or tasks are running
* **Normal (750ms)**: Default rate
* **Idle (1500ms)**: When no activity detected
* **Error (750ms)**: After an error until acknowledged

### Beads Timeline

"Beads" are structured log items from `/poll` endpoint:

**Each bead shows**:
* Type indicator (color-coded)
* Heading
* Content preview
* Timestamp/sequence
* Associated context/task

**Filtering**:
* By type (all, error, warning, tool, code_exe, browser, progress, response, agent)
* By search term (heading + content)
* Hide temporary logs option

**Actions**:
* Click bead to inspect in right panel
* Export timeline to JSON
* Jump to latest
* Pin errors to top

### Live View

Shows agent browser automation in real-time:

**Screenshot Display**:
* Extracts `img://` paths from log kvps
* Converts to `/image_get?path=...`
* Auto-refreshes when new screenshots available

**Step Narration**:
* Derived from `log_progress` and browser agent logs
* Shows "what's happening" + "what's next"

**Current Tool**:
* Tool name, args (redacted for sensitive data)

**Blockers**:
* Latest errors/warnings with recommended actions

### Task Scheduler

**Create Tasks**:
1. Click "➕ Adhoc", "⏰ Scheduled", or "📅 Planned"
2. Fill task details:
   * Name
   * Type-specific fields (schedule for scheduled, plan for planned)
   * System prompt
   * User prompt
   * Attachments
   * Project binding
3. Save

**Manage Tasks**:
* Run Now: Execute task immediately
* Enable/Disable: Toggle task state
* Edit: Modify task configuration
* Delete: Remove task (requires confirmation)
* Tick: Manually trigger scheduler tick

**Filters**:
* Type: All, Adhoc, Scheduled, Planned
* State: All, Idle, Running, Disabled, Error
* Search: By task name

---

## Security & Guardrails

### Built-in Protections

1. **No Token Exposure**: CSRF tokens and API keys never rendered client-side
2. **Confirmation Gates**: All destructive operations require explicit confirmation
3. **Audit Logging**: Memory edits and sensitive operations logged
4. **Autonomy Levels**: Tier 0-4 policy enforcement (UI feedback)
5. **Secret Redaction**: Sensitive data masked in logs and displays

### Autonomy Tiers

| Tier | Permissions | Approvals |
|------|-------------|-----------|
| T0 | Read-only, summaries | All actions |
| T1 | Non-destructive tools, planning | Writes, network |
| T2 | File writes in work_dir, browser automation | Network, installs |
| T3 | Network calls, external integrations, package installs | Approval required |
| T4 | Deletes, restores, credentials, tunnel, admin | Explicit approval + audit |

**Note**: The slider provides UI feedback; full enforcement requires backend policy implementation.

### Negative Constraints

The dashboard enforces:
* ❌ Never fabricate API responses or tool results
* ❌ Never claim task completion without poll confirmation
* ❌ Never expose secrets/tokens in UI or logs
* ❌ Never enable remote access without explicit user action
* ❌ Never run destructive actions without confirmation

---

## Troubleshooting

### Dashboard won't connect

1. Check Agent Zero backend is running:
   ```bash
   python run_ui.py
   ```

2. Check console for errors (F12 → Console)

3. Verify port and host settings in `.env` or runtime args

4. Test health endpoint directly:
   ```
   curl http://localhost:<port>/health
   ```

### No beads appearing

1. Ensure context is selected (top bar context selector)
2. Check filter settings (may be filtering out all types)
3. Verify `/poll` endpoint returns logs:
   ```bash
   curl -X POST http://localhost:<port>/poll \
     -H "Content-Type: application/json" \
     -d '{"context": "<context_id>"}'
   ```

### Live View not showing screenshots

1. Confirm browser agent is active and producing screenshots
2. Check log kvps for `screenshot` field with `img://` prefix
3. Verify `/image_get` endpoint is accessible
4. Check browser console for image load errors

### Polling too fast/slow

Polling is adaptive but can be adjusted in `main.js`:
```javascript
this.pollingRate = 750; // Change default rate (ms)
```

### CSRF errors

1. Ensure session cookie is valid
2. Check `/csrf_token` endpoint returns token
3. Clear browser cache and restart Agent Zero

---

## NEW Features (Marked as NEW)

### A2A / Agent Mail

**Status**: NEW - UI scaffold only, requires backend implementation

The A2A panel provides a UI for inter-agent messaging using existing A2A patterns:

**Intended Features**:
* Agent-to-agent message threads
* Send/broadcast capabilities
* Delivery metrics
* Routing status

**Implementation Note**: The A2A server exists at `/a2a` (mounted in `run_ui.py`), but message-specific endpoints must be added. The UI provides the interface; backend must be extended to support full agent mail functionality.

---

## Development

### Adding New Panels

1. Add HTML structure in `master-dashboard.html`:
   ```html
   <div id="panel-new-feature" class="panel">
       <div class="panel-header">
           <h1>New Feature</h1>
       </div>
       <div id="new-feature-content"></div>
   </div>
   ```

2. Add navigation button:
   ```html
   <button class="nav-btn" data-panel="new-feature">
       <span class="nav-icon">🆕</span>
       <span class="nav-label">New Feature</span>
   </button>
   ```

3. Add panel logic in `panels.js` or create module in `js/master-dashboard/`

4. Register in `main.js` if needed

### Extending API Client

Add new endpoint methods to `api.js`:

```javascript
async myNewEndpoint(data) {
    return this.fetchAPI('/my_new_endpoint', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}
```

### Custom Beads Rendering

Extend `beads.js` to add custom rendering for specific log types:

```javascript
renderBead(log) {
    if (log.type === 'my_custom_type') {
        // Custom rendering logic
    }
    // ... default rendering
}
```

---

## File Reference

### Key Files

| File | Purpose | Grounded To |
|------|---------|-------------|
| `webui/master-dashboard.html` | Main HTML structure | N/A |
| `webui/css/master-dashboard.css` | Styling and theme | N/A |
| `webui/js/master-dashboard/main.js` | Entry point, coordination | N/A |
| `webui/js/master-dashboard/api.js` | Backend API layer | `python/api/*.py` |
| `webui/js/master-dashboard/state.js` | State management | `/poll` response |
| `webui/js/master-dashboard/beads.js` | Beads timeline | `python/helpers/log.py` (LogItem) |
| `webui/js/master-dashboard/live-view.js` | Live agent view | `python/tools/browser_agent.py` |
| `webui/js/master-dashboard/panels.js` | Panel management | N/A |
| `webui/js/master-dashboard/toast.js` | Toast notifications | N/A |
| `python/api/poll.py` | Real-time polling endpoint | Central data source |
| `python/helpers/log.py` | Log item structure | Beads definition |
| `run_ui.py` | Flask server | Dashboard backend |

---

## Migration from Classic UI

The Master Dashboard coexists with the classic UI:

* **Classic UI**: `http://localhost:<port>/` (default)
* **Master Dashboard**: `http://localhost:<port>/master-dashboard.html`

**Differences**:

| Feature | Classic UI | Master Dashboard |
|---------|-----------|------------------|
| Layout | Single-page chat | Multi-panel ops grid |
| Observability | Limited | Full beads timeline |
| Task Management | Basic | Full scheduler CRUD |
| Live View | No | Yes (screenshots + narration) |
| Navigation | Minimal | Comprehensive left nav |
| Real-time Updates | Polling | Adaptive polling |

**Recommendation**: Use Master Dashboard for:
* Complex multi-task workflows
* Debugging and observability
* Task scheduler management
* Full system control

Use Classic UI for:
* Quick chat sessions
* Simple queries
* Minimal interface preference

---

## Known Limitations

1. **No WebSocket support**: Uses polling only (matches backend architecture)
2. **A2A / Agent Mail**: UI exists but requires backend implementation
3. **Full desktop streaming**: Not implemented (only browser screenshots)
4. **Autonomy tier enforcement**: UI feedback only; backend must enforce policies
5. **Mobile optimization**: Works on mobile but optimized for desktop

---

## Roadmap (Future Enhancements)

### Potential Backend Additions
* NEW api-key-only endpoints for all operations (avoid session/CSRF complexity)
* Streaming endpoints (SSE or WebSocket) for true real-time updates
* Approval queue system for high-autonomy operations
* Desktop streaming via noVNC or similar

### UI Enhancements
* Customizable panel layouts (drag-and-drop grid)
* Dark/light theme toggle
* Export reports (PDF, HTML)
* Advanced search across all logs
* Multi-context comparison view
* Timeline playback (replay agent activity)

---

## Credits

**Built for**: agent-zero-Fork repository  
**Backend**: Flask (`run_ui.py`) + existing `python/api/*.py` endpoints  
**Frontend**: Vanilla JavaScript + CSS (no framework dependencies)  
**Design**: High-tech ops grid theme with operational state color coding  
**Philosophy**: "Never wonder what is happening"

---

## Support

For issues, questions, or contributions:

1. Check existing endpoint implementation in `python/api/`
2. Verify backend logs for API errors
3. Use browser DevTools console for frontend debugging
4. Review poll response structure in Network tab

**Remember**: This dashboard only uses APIs that exist in the repo. If a feature doesn't work, check if the corresponding `python/api/<name>.py` file exists and is properly registered in `run_ui.py`.
