# Master Dashboard - Quick Start Guide

## 🚀 Getting Started in 60 Seconds

### 1. Start Agent Zero Backend

```bash
cd agent-zero-Fork
python run_ui.py
```

Wait for the server to start. You'll see output like:
```
Starting server at http://localhost:50001 ...
```

### 2. Open Master Dashboard

Navigate to:
```
http://localhost:50001/master-dashboard.html
```

(Adjust port if you configured a different `WEB_UI_PORT`)

### 3. Verify Connection

* Top status bar should show "Online" in green
* Connection status indicator will pulse
* Mission Control panel loads automatically

**That's it!** You're now viewing the Master Dashboard.

---

## 🎯 First Tasks

### Task 1: View Activity Timeline (Beads)

1. Click **"📿 Beads Timeline"** in left navigation
2. Select a context from the top bar if you have active chats
3. Watch logs appear in real-time as beads
4. Try filtering by type (Errors, Tools, Progress, etc.)

### Task 2: Create a Chat

1. Click **"💬 Chats"** in left navigation
2. Click **"➕ New"** button
3. Select or create a new context
4. Start chatting - watch beads populate in real-time

### Task 3: Schedule a Task

1. Click **"📋 Scheduler"** in left navigation
2. Click **"➕ Adhoc"** to create a simple task
3. Fill in:
   * Task name
   * Prompt (what you want the agent to do)
4. Click **"Run Now"** to execute immediately
5. Watch the task in Mission Control "Running Tasks" card

### Task 4: View Live Agent Activity

1. Trigger any browser automation task
2. Click **"👁️ Live View"** in left navigation
3. See screenshots as the agent navigates
4. Read step narration on the right panel
5. Monitor current tool usage

---

## 🎨 Understanding the Interface

### Top Bar (Always Visible)

```
[Logo] [Connection Status] [Current Progress] [Context] [⏸] [Errors] [🛡️ T2]
```

* **Connection Status**: Green = online, Red = offline, shows last update time
* **Current Progress**: Shows what the agent is currently doing
* **Context Selector**: Switch between active chats
* **⏸ Button**: Pause/Resume current context
* **Errors Badge**: Shows count of recent errors
* **🛡️ Autonomy Slider**: Set operational tier (0-4)

### Three-Panel Layout

```
┌──────────────┬─────────────────────────────┬────────────────┐
│              │                             │                │
│ Left Nav     │  Main Content               │  Inspector     │
│              │  (Selected Panel)           │  (Details)     │
│ • Overview   │                             │                │
│ • Beads      │                             │                │
│ • Live View  │                             │                │
│ • Chats      │                             │                │
│ • Tasks      │                             │                │
│ • etc...     │                             │                │
│              │                             │                │
└──────────────┴─────────────────────────────┴────────────────┘
```

* **Left**: Navigate between panels
* **Center**: Main working area
* **Right**: Inspector shows details when you click items

### Color System

Learn the operational state colors:

* 🟢 **Green**: Idle/Ready
* 🔵 **Blue**: Running
* 🟣 **Purple**: Paused
* 🟡 **Amber**: Waiting/Warning
* 🔴 **Red**: Error
* ⚪ **Gray**: Offline

---

## 📊 Key Panels Explained

### 🎯 Mission Control (Default)

Your command center:

* **Now Playing**: Current agent activity + recent beads
* **Critical Alerts**: Errors and warnings requiring attention
* **Active Contexts**: All running chat sessions
* **Running Tasks**: Tasks currently executing
* **System Health**: Backend status

**Use this for**: Quick overview of everything happening

### 📿 Beads Timeline

Structured log viewer:

* Each "bead" is a log entry
* Color-coded by type
* Click to inspect details
* Filter and search

**Use this for**: Debugging, understanding agent reasoning, tracking execution flow

### 👁️ Live View

Real-time agent observation:

* Browser screenshots (when agent uses browser_agent tool)
* Step-by-step narration
* Current tool display
* Blockers/errors

**Use this for**: Watching agent work, debugging browser automation

### 📋 Scheduler

Task automation:

* **Adhoc**: Run once, manually or via token
* **Scheduled**: Cron-style recurring tasks
* **Planned**: One-time future scheduled task

**Use this for**: Automation, recurring jobs, batch processing

---

## 🔍 Common Workflows

### Workflow 1: Debug a Failed Task

1. Go to **Mission Control** → Check "Critical Alerts"
2. Click on error to see full details in Inspector
3. Go to **Beads Timeline** → Filter for "Errors"
4. Find the error bead and expand it
5. Read the error message and context
6. Check previous beads to understand what led to failure

### Workflow 2: Monitor Long-Running Agent

1. Start agent task in **Chats** or **Scheduler**
2. Go to **Live View** to watch in real-time
3. Monitor step narration to see progress
4. Check Current Tool to see what's executing
5. If needed, pause via top bar button

### Workflow 3: Schedule Recurring Report

1. Go to **Scheduler** → **"⏰ Scheduled"**
2. Set name: "Daily Report"
3. Set schedule: `0 9 * * *` (9 AM daily)
4. Set timezone
5. Write prompt: "Generate daily status report and email to team"
6. Save
7. Task will auto-run per schedule

### Workflow 4: Manage Projects

1. Go to **Projects** panel
2. View all projects with color tags
3. Click project to filter contexts/tasks
4. Use project colors to visually organize work

---

## 🛡️ Safety & Guardrails

### Autonomy Levels

The **🛡️ slider** sets operational tier:

* **T0**: Read-only (safest)
* **T1**: Planning + non-destructive tools
* **T2**: File writes + browser automation (recommended default)
* **T3**: Network calls + installs (requires approval - UI shows warning)
* **T4**: Delete/restore/credentials (requires explicit confirmation)

**Recommendation**: Keep at T2 for daily use, increase only when needed

### Destructive Operations

Whenever you:
* Delete files
* Restore backups
* Change critical settings
* Remove contexts/tasks

A confirmation modal will appear. Read carefully before confirming.

### Secrets & Tokens

The dashboard **never** displays:
* API keys
* Passwords
* Tokens
* Credentials

All sensitive data is redacted automatically.

---

## 🐛 Troubleshooting Quick Fixes

### Problem: Dashboard shows "Offline"

**Solution**:
```bash
# 1. Verify backend is running
ps aux | grep run_ui.py

# 2. Restart if needed
python run_ui.py

# 3. Check port
# Look for "Starting server at http://localhost:XXXXX"
```

### Problem: No beads appearing

**Solution**:
1. Ensure a context is selected (top bar dropdown)
2. Check filter settings - click "All" chip
3. Uncheck "Hide Temporary" if enabled
4. Try sending a message in Chats panel

### Problem: Live View not showing screenshots

**Solution**:
1. Verify the agent is using `browser_agent` tool
2. Check beads for browser-type logs
3. Look for logs with `screenshot` in kvps
4. Browser automation must be active to produce screenshots

### Problem: Tasks not running

**Solution**:
1. Check task state (should be "idle", not "disabled")
2. Verify schedule syntax for scheduled tasks
3. Click "⚡ Tick" button to manually trigger scheduler
4. Check "Running Tasks" in Mission Control

### Problem: Connection flapping (online/offline)

**Solution**:
1. Check network stability
2. Verify backend isn't overloaded (check CPU/memory)
3. Increase polling interval in `main.js` if needed
4. Check backend logs for errors

---

## 📚 Next Steps

### Learn More

* Read full documentation: `docs/master-dashboard.md`
* Explore API mappings and data models
* Understand polling strategy and adaptive rates
* Review security and guardrails details

### Customize

* Adjust polling rates in `js/master-dashboard/main.js`
* Modify color scheme in `css/master-dashboard.css`
* Add custom bead renderers in `js/master-dashboard/beads.js`
* Create new panels following development guide

### Extend

* Add new endpoints in `python/api/`
* Register them in `run_ui.py`
* Add corresponding API methods in `api.js`
* Build UI in new panel

---

## 💡 Pro Tips

1. **Use keyboard**: Tab through controls, Enter to activate
2. **Pin errors**: Click 📌 in Beads Timeline to keep errors at top
3. **Export timeline**: 📥 button saves JSON for analysis
4. **Jump to latest**: ⬇️ button scrolls to most recent bead
5. **Search beads**: Type in search box to filter by heading/content
6. **Multi-monitor**: Open classic UI + Master Dashboard side-by-side
7. **Mobile**: Dashboard works on tablets/phones for monitoring
8. **Context switching**: Use top dropdown to quickly switch contexts
9. **Inspector**: Click any bead/task/file to see details in right panel
10. **Toast notifications**: Watch bottom-right for success/error messages

---

## 🎉 You're Ready!

The Master Dashboard gives you complete visibility and control over Agent Zero. 

**Remember**: 
* Green status = good
* Beads = logs
* Live View = watch agent work
* Autonomy slider = safety control

Start with Mission Control, explore from there. Happy agentic operations! 🚀
