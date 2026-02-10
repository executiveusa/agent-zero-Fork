"""
Beads Tool — Git-backed Issue Tracking for Agent Zero

Wraps the beads CLI (bd) and the BeadsIntegration Python layer
to provide dependency-aware task management inside Agent Zero's tool system.

Methods:
  - beads_tool:create    — Create a new task
  - beads_tool:ready     — Get tasks ready to work on (no blockers)
  - beads_tool:status    — Update task status
  - beads_tool:close     — Close/complete a task
  - beads_tool:show      — Get task details
  - beads_tool:list      — List all tasks for an agent
  - beads_tool:sync      — Force beads sync (export → commit → push)
  - beads_tool:dep       — Add dependency between tasks

Created: 2026-02-10
"""

import json
import os
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle

# Default project path for beads operations
DEFAULT_PROJECT_PATH = os.path.join(os.path.dirname(__file__), "..", "..")
BD_BINARY = os.environ.get("BEADS_BD_BINARY", "bd")


def _run_bd(args: List[str], project_path: str = DEFAULT_PROJECT_PATH, capture_json: bool = True) -> Dict[str, Any]:
    """Execute bd CLI command safely."""
    cmd = [BD_BINARY] + args

    if capture_json and "--json" not in args:
        args.append("--json")
        cmd = [BD_BINARY] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return {
                "error": True,
                "returncode": result.returncode,
                "stderr": result.stderr.strip(),
                "stdout": result.stdout.strip(),
            }

        if capture_json and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip(), "error": False}

        return {"output": result.stdout.strip(), "error": False}

    except FileNotFoundError:
        return {"error": True, "message": f"bd binary not found at '{BD_BINARY}'. Install beads or set BEADS_BD_BINARY env var."}
    except subprocess.TimeoutExpired:
        return {"error": True, "message": "Command timed out after 60s"}
    except Exception as e:
        return {"error": True, "message": str(e)}


def _ensure_beads_init(project_path: str):
    """Initialize beads in project if not already present."""
    beads_dir = os.path.join(project_path, ".beads")
    if not os.path.exists(beads_dir):
        result = _run_bd(["init", "--prefix", "bd"], project_path, capture_json=False)
        if result.get("error"):
            PrintStyle.warning(f"Beads init failed: {result}")


class BeadsTool(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "ready"
        project_path = self.args.get("project_path", DEFAULT_PROJECT_PATH)

        if method == "create":
            return self._create(project_path)
        elif method == "ready":
            return self._ready(project_path)
        elif method == "status":
            return self._update_status(project_path)
        elif method == "close":
            return self._close(project_path)
        elif method == "show":
            return self._show(project_path)
        elif method == "list":
            return self._list_tasks(project_path)
        elif method == "sync":
            return self._sync(project_path)
        elif method == "dep":
            return self._add_dep(project_path)
        else:
            return Response(
                message=f"Unknown method 'beads_tool:{method}'. Use: create, ready, status, close, show, list, sync, dep",
                break_loop=False,
            )

    def _create(self, project_path: str) -> Response:
        title = self.args.get("title", "")
        priority = self.args.get("priority", "2")
        description = self.args.get("description", "")
        depends_on = self.args.get("depends_on", [])

        if not title:
            return Response(message="Provide 'title' argument.", break_loop=False)

        args = ["create", title, "-p", str(priority)]
        if description:
            args.extend(["--description", description])

        result = _run_bd(args, project_path)

        if result.get("error"):
            return Response(
                message=f"Failed to create beads task: {result.get('message') or result.get('stderr', 'unknown error')}",
                break_loop=False,
            )

        task_id = result.get("id", "unknown")

        # Add dependencies if provided
        if depends_on and isinstance(depends_on, list):
            for dep_id in depends_on:
                _run_bd(["dep", "add", task_id, dep_id], project_path)

        return Response(
            message=f"Beads task created: {task_id}\n  Title: {title}\n  Priority: P{priority}\n  Deps: {depends_on or 'none'}",
            break_loop=False,
        )

    def _ready(self, project_path: str) -> Response:
        limit = int(self.args.get("limit", 10))
        args = ["ready", "--limit", str(limit)]

        result = _run_bd(args, project_path)

        if result.get("error"):
            # Graceful fallback if bd not installed
            return Response(
                message=f"Beads ready query failed: {result.get('message', result.get('stderr', 'unknown'))}.\n"
                        f"Tip: Install beads CLI (bd) or set BEADS_BD_BINARY env var.",
                break_loop=False,
            )

        tasks = result.get("issues", []) if isinstance(result, dict) else []
        if not tasks:
            return Response(message="No ready tasks (all blocked or empty).", break_loop=False)

        lines = []
        for t in tasks:
            tid = t.get("id", "?")
            title = t.get("title", "?")
            prio = t.get("priority", "?")
            lines.append(f"  [{tid}] P{prio}: {title}")

        return Response(
            message=f"Ready work ({len(tasks)} tasks):\n" + "\n".join(lines),
            break_loop=False,
        )

    def _update_status(self, project_path: str) -> Response:
        task_id = self.args.get("task_id", "")
        new_status = self.args.get("new_status", "in_progress")
        notes = self.args.get("notes", "")

        if not task_id:
            return Response(message="Provide 'task_id' argument.", break_loop=False)

        args = ["update", task_id, "--status", new_status]
        if notes:
            args.extend(["--notes", notes])

        result = _run_bd(args, project_path)

        if result.get("error"):
            return Response(message=f"Status update failed: {result}", break_loop=False)

        return Response(
            message=f"Task {task_id} → {new_status}" + (f" ({notes})" if notes else ""),
            break_loop=False,
        )

    def _close(self, project_path: str) -> Response:
        task_id = self.args.get("task_id", "")
        reason = self.args.get("reason", "Completed")

        if not task_id:
            return Response(message="Provide 'task_id' argument.", break_loop=False)

        args = ["close", task_id, "--reason", reason]
        result = _run_bd(args, project_path)

        if result.get("error"):
            return Response(message=f"Close failed: {result}", break_loop=False)

        return Response(message=f"Task {task_id} closed: {reason}", break_loop=False)

    def _show(self, project_path: str) -> Response:
        task_id = self.args.get("task_id", "")

        if not task_id:
            return Response(message="Provide 'task_id' argument.", break_loop=False)

        result = _run_bd(["show", task_id], project_path)

        if result.get("error"):
            return Response(message=f"Show failed: {result}", break_loop=False)

        return Response(message=json.dumps(result, indent=2, default=str), break_loop=False)

    def _list_tasks(self, project_path: str) -> Response:
        status_filter = self.args.get("filter_status", "")
        args = ["list"]
        if status_filter:
            args.extend(["--status", status_filter])

        result = _run_bd(args, project_path)

        if result.get("error"):
            return Response(message=f"List failed: {result}", break_loop=False)

        tasks = result.get("issues", []) if isinstance(result, dict) else []
        if not tasks:
            output = result.get("output", "No tasks found.")
            return Response(message=output, break_loop=False)

        lines = []
        for t in tasks:
            tid = t.get("id", "?")
            title = t.get("title", "?")
            status = t.get("status", "?")
            prio = t.get("priority", "?")
            lines.append(f"  [{tid}] P{prio} [{status}]: {title}")

        return Response(message=f"Tasks ({len(tasks)}):\n" + "\n".join(lines), break_loop=False)

    def _sync(self, project_path: str) -> Response:
        result = _run_bd(["sync"], project_path, capture_json=False)

        if result.get("error"):
            return Response(message=f"Sync failed: {result}", break_loop=False)

        return Response(message=f"Beads sync complete: {result.get('output', 'OK')}", break_loop=False)

    def _add_dep(self, project_path: str) -> Response:
        child_id = self.args.get("child_id", "")
        parent_id = self.args.get("parent_id", "")

        if not child_id or not parent_id:
            return Response(message="Provide 'child_id' and 'parent_id' arguments.", break_loop=False)

        result = _run_bd(["dep", "add", child_id, parent_id], project_path)

        if result.get("error"):
            return Response(message=f"Dependency add failed: {result}", break_loop=False)

        return Response(
            message=f"Dependency added: {parent_id} blocks {child_id}",
            break_loop=False,
        )
