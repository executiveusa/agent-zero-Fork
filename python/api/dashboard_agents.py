"""
Dashboard API — Agent Status Panel

Endpoint: /dashboard_agents (POST)
Actions:
  - status: Get all agent statuses
  - health: Health check for specific agent
  - roster: Get full agent roster from orchestration config
  - swarms: List active and recent swarm executions
  - loop: Get orchestrator loop state
"""

import os
import json
from datetime import datetime, timezone
from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class DashboardAgents(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "status")

        if action == "status":
            return await self._status()
        elif action == "health":
            return await self._health(input)
        elif action == "roster":
            return await self._roster()
        elif action == "swarms":
            return await self._swarms()
        elif action == "loop":
            return await self._loop_state()
        else:
            return {"error": f"Unknown action: {action}", "available": ["status", "health", "roster", "swarms", "loop"]}

    async def _status(self) -> Output:
        """Get all agent statuses from swarm registry and loop state."""
        agents = []

        # Load orchestration config for roster
        try:
            from python.helpers.orchestration_config import load_orchestration_config
            config = load_orchestration_config()
            for agent_def in config.agents:
                agents.append({
                    "id": agent_def.id,
                    "name": agent_def.name,
                    "role": agent_def.role,
                    "port": agent_def.port,
                    "model": agent_def.model,
                    "status": "configured",  # Will be updated if we find runtime data
                })
        except ImportError:
            pass

        # Check for active tasks per agent from swarm data
        swarm_dir = "tmp/swarms"
        active_tasks = {}
        if os.path.exists(swarm_dir):
            for fname in os.listdir(swarm_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            swarm = json.load(f)
                            for task in swarm.get("tasks", []):
                                profile = task.get("agent_profile", "default")
                                if profile not in active_tasks:
                                    active_tasks[profile] = {"running": 0, "completed": 0, "failed": 0}
                                status = task.get("status", "pending")
                                if status == "running":
                                    active_tasks[profile]["running"] += 1
                                elif status == "completed":
                                    active_tasks[profile]["completed"] += 1
                                elif status in ("failed", "timeout"):
                                    active_tasks[profile]["failed"] += 1
                    except Exception:
                        pass

        # Merge task counts into agent status
        for agent in agents:
            agent_id = agent.get("id", "")
            if agent_id in active_tasks:
                agent["active_tasks"] = active_tasks[agent_id]
                if active_tasks[agent_id]["running"] > 0:
                    agent["status"] = "active"

        return {"ok": True, "agents": agents, "timestamp": datetime.now(timezone.utc).isoformat()}

    async def _health(self, input: Input) -> Output:
        """Health check for a specific agent."""
        agent_id = input.get("agent_id", "")
        if not agent_id:
            return {"error": "Provide 'agent_id' parameter"}

        # Check cost tracker for agent spend
        spend = None
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            spend = tracker.get_agent_spend(agent_id)
        except ImportError:
            pass

        return {
            "ok": True,
            "agent_id": agent_id,
            "health": "ok",
            "spend_today": spend,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _roster(self) -> Output:
        """Get full agent roster from orchestration config."""
        try:
            from python.helpers.orchestration_config import load_orchestration_config
            config = load_orchestration_config()
            roster = []
            for agent_def in config.agents:
                roster.append({
                    "id": agent_def.id,
                    "name": agent_def.name,
                    "role": agent_def.role,
                    "port": agent_def.port,
                    "model": agent_def.model,
                    "fallback_model": agent_def.fallback_model,
                })
            return {"ok": True, "roster": roster, "total": len(roster)}
        except ImportError:
            return {"ok": False, "error": "Orchestration config not available"}

    async def _swarms(self) -> Output:
        """List active and recent swarm executions."""
        swarms = []
        swarm_dir = "tmp/swarms"
        if os.path.exists(swarm_dir):
            for fname in os.listdir(swarm_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            data = json.load(f)
                            swarms.append({
                                "swarm_id": data.get("swarm_id"),
                                "name": data.get("name"),
                                "status": data.get("status"),
                                "created_at": data.get("created_at"),
                                "progress": data.get("progress", {}),
                                "task_count": data.get("task_count", 0),
                            })
                    except Exception:
                        pass

        # Sort by created_at descending
        swarms.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return {"ok": True, "swarms": swarms[:20]}

    async def _loop_state(self) -> Output:
        """Get orchestrator loop state."""
        loop_state_file = "tmp/orchestrator/loop_state.json"
        if os.path.exists(loop_state_file):
            try:
                with open(loop_state_file, "r") as f:
                    state = json.load(f)
                return {"ok": True, "loop_state": state}
            except Exception:
                return {"ok": False, "error": "Failed to read loop state"}
        else:
            return {"ok": True, "loop_state": None, "note": "Orchestrator loop has not started yet"}
