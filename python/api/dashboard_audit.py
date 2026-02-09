"""
Dashboard API — Audit Trail Panel

Endpoint: /dashboard_audit (POST)
Actions:
  - recent: Get recent audit events
  - routing: Get task routing decisions log
  - errors: Get recent error log
  - recovery: Get recovery actions taken
  - export: Export audit data as JSON
"""

import os
import json
from datetime import datetime, timezone, timedelta
from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class DashboardAudit(ApiHandler):

    AUDIT_DIR = "tmp/audit"

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "recent")

        if action == "recent":
            return await self._recent(input)
        elif action == "routing":
            return await self._routing(input)
        elif action == "errors":
            return await self._errors(input)
        elif action == "recovery":
            return await self._recovery(input)
        elif action == "export":
            return await self._export(input)
        else:
            return {"error": f"Unknown action: {action}", "available": ["recent", "routing", "errors", "recovery", "export"]}

    async def _recent(self, input: Input) -> Output:
        """Get recent audit events from all sources."""
        limit = int(input.get("limit", 50))
        events = []

        # Collect from orchestrator loop state
        loop_state_file = "tmp/orchestrator/loop_state.json"
        if os.path.exists(loop_state_file):
            try:
                with open(loop_state_file, "r") as f:
                    state = json.load(f)
                    events.append({
                        "type": "loop_cycle",
                        "timestamp": state.get("last_cycle", ""),
                        "details": f"Cycle #{state.get('cycle_number', 0)} — {state.get('actions_taken', 0)} actions, {state.get('cycle_ms', 0)}ms",
                    })
            except Exception:
                pass

        # Collect from swarm executions
        swarm_dir = "tmp/swarms"
        if os.path.exists(swarm_dir):
            for fname in sorted(os.listdir(swarm_dir), reverse=True)[:10]:
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            swarm = json.load(f)
                            events.append({
                                "type": "swarm",
                                "timestamp": swarm.get("created_at", ""),
                                "details": f"Swarm '{swarm.get('name', '')}' [{swarm.get('status', '')}] — {swarm.get('task_count', 0)} tasks",
                            })
                            # Add individual task completions
                            for task in swarm.get("tasks", []):
                                if task.get("completed_at"):
                                    events.append({
                                        "type": "task_complete",
                                        "timestamp": task.get("completed_at", ""),
                                        "details": f"[{task.get('status', '')}] {task.get('agent_profile', '')}: {task.get('description', '')[:60]}",
                                    })
                    except Exception:
                        pass

        # Collect from cost tracking
        cost_dir = "tmp/cost_tracking"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cost_file = os.path.join(cost_dir, f"costs_{today}.json")
        if os.path.exists(cost_file):
            try:
                with open(cost_file, "r") as f:
                    entries = json.load(f)
                    # Only include high-cost calls
                    for entry in entries:
                        if entry.get("estimated_cost", 0) > 0.01:
                            events.append({
                                "type": "cost_event",
                                "timestamp": entry.get("timestamp", ""),
                                "details": f"${entry.get('estimated_cost', 0):.4f} — {entry.get('model', '')} ({entry.get('agent_id', '')})",
                            })
            except Exception:
                pass

        # Sort by timestamp descending
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return {"ok": True, "events": events[:limit], "total": len(events)}

    async def _routing(self, input: Input) -> Output:
        """Get task routing decisions log."""
        limit = int(input.get("limit", 30))

        # Read from task queue for routed tasks
        task_queue_path = "memory/agent_zero/task_queue.json"
        routed = []
        if os.path.exists(task_queue_path):
            try:
                with open(task_queue_path, "r") as f:
                    tasks = json.load(f)
                    for task in tasks:
                        if task.get("status") == "routed":
                            routed.append({
                                "task_id": task.get("id", ""),
                                "description": task.get("description", task.get("task", ""))[:80],
                                "routed_to": task.get("routed_to", ""),
                                "routed_at": task.get("routed_at", ""),
                            })
            except Exception:
                pass

        routed.sort(key=lambda r: r.get("routed_at", ""), reverse=True)
        return {"ok": True, "routing_decisions": routed[:limit]}

    async def _errors(self, input: Input) -> Output:
        """Get recent errors."""
        limit = int(input.get("limit", 20))
        errors = []

        # Check swarm task errors
        swarm_dir = "tmp/swarms"
        if os.path.exists(swarm_dir):
            for fname in os.listdir(swarm_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            swarm = json.load(f)
                            for task in swarm.get("tasks", []):
                                if task.get("error"):
                                    errors.append({
                                        "timestamp": task.get("completed_at", ""),
                                        "source": f"swarm/{swarm.get('swarm_id', '')}",
                                        "agent": task.get("agent_profile", ""),
                                        "error": task.get("error", ""),
                                        "task": task.get("description", "")[:60],
                                    })
                    except Exception:
                        pass

        errors.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return {"ok": True, "errors": errors[:limit]}

    async def _recovery(self, input: Input) -> Output:
        """Get recovery actions from orchestrator."""
        # This would be populated by the orchestrator loop's recovery procedures
        return {
            "ok": True,
            "recovery_actions": [],
            "note": "Recovery actions are logged when the orchestrator loop detects and handles failures",
            "supported_failures": [
                "loop_slowdown", "memory_corruption", "docker_socket_lost",
                "container_crash", "disk_full", "network_isolation",
                "memory_leak", "routing_error", "write_conflict", "glitchtip_db_full"
            ],
        }

    async def _export(self, input: Input) -> Output:
        """Export audit data as JSON."""
        days = int(input.get("days", 1))
        
        # Aggregate all audit data
        recent = await self._recent({"limit": 500})
        routing = await self._routing({"limit": 100})
        errors = await self._errors({"limit": 100})

        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "days_covered": days,
            "events": recent.get("events", []),
            "routing_decisions": routing.get("routing_decisions", []),
            "errors": errors.get("errors", []),
        }

        # Save to tmp
        os.makedirs("tmp/audit", exist_ok=True)
        export_file = f"tmp/audit/export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f, indent=2)

        return {
            "ok": True,
            "export_file": export_file,
            "event_count": len(export_data["events"]),
            "routing_count": len(export_data["routing_decisions"]),
            "error_count": len(export_data["errors"]),
        }
