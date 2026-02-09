"""
Orchestrator Loop Extension — Ralphie 30-Second Cycle

Runs as a message_loop_start hook. When the active agent profile is 'orchestrator',
this extension executes the Perception → Decision → Action loop each cycle.

For non-orchestrator profiles, this extension is a no-op.
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from python.helpers.extension import Extension
from python.helpers.print_style import PrintStyle
from agent import Agent, LoopData

# Cycle state key
DATA_NAME_LOOP_STATE = "orchestrator_loop_state"
LOOP_STATE_FILE = "tmp/orchestrator/loop_state.json"


class OrchestratorLoop(Extension):
    """
    Implements the Ralphie Perception → Decision → Action loop.
    Only activates when agent profile == 'orchestrator'.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only run for orchestrator profile
        if not self.agent.config or not hasattr(self.agent.config, 'profile'):
            return
        if self.agent.config.profile != "orchestrator":
            return

        try:
            cycle_start = datetime.now(timezone.utc)

            # ── PERCEPTION ──────────────────────────────
            perception = await self._perceive()

            # ── DECISION ────────────────────────────────
            decisions = await self._decide(perception)

            # ── ACTION ──────────────────────────────────
            actions_taken = await self._act(decisions)

            # ── PERSIST STATE ───────────────────────────
            cycle_end = datetime.now(timezone.utc)
            cycle_ms = (cycle_end - cycle_start).total_seconds() * 1000

            state = {
                "last_cycle": cycle_end.isoformat(),
                "cycle_ms": round(cycle_ms),
                "perception_summary": perception.get("summary", ""),
                "decisions_count": len(decisions),
                "actions_taken": actions_taken,
                "cycle_number": (self.agent.get_data(DATA_NAME_LOOP_STATE) or {}).get("cycle_number", 0) + 1,
            }
            self.agent.set_data(DATA_NAME_LOOP_STATE, state)
            self._persist_state(state)

            # Warn if cycle took too long
            if cycle_ms > 45000:
                PrintStyle.warning(f"Orchestrator loop cycle took {cycle_ms:.0f}ms (>45s threshold)")

        except Exception as e:
            PrintStyle.error(f"Orchestrator loop error: {e}")
            # Never crash the loop — log and continue

    async def _perceive(self) -> dict:
        """
        PERCEPTION phase: gather state from all subsystems.
        Returns a dict summarizing current platform state.
        """
        perception = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_queue": [],
            "agent_health": {},
            "budget_status": {},
            "swarm_status": [],
            "summary": "",
        }

        # 1. Check task queue
        task_queue_path = "memory/agent_zero/task_queue.json"
        if os.path.exists(task_queue_path):
            try:
                with open(task_queue_path, "r") as f:
                    tasks = json.load(f)
                    perception["task_queue"] = [
                        t for t in tasks if t.get("status") in ("pending", "queued", "retry")
                    ]
            except Exception:
                pass

        # 2. Check cost budget
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            perception["budget_status"] = tracker.get_budget_status()
        except ImportError:
            perception["budget_status"] = {"available": True}

        # 3. Check swarm status
        try:
            swarm_dir = "tmp/swarms"
            if os.path.exists(swarm_dir):
                for fname in os.listdir(swarm_dir):
                    if fname.endswith(".json"):
                        with open(os.path.join(swarm_dir, fname), "r") as f:
                            swarm_data = json.load(f)
                            if swarm_data.get("status") == "running":
                                perception["swarm_status"].append({
                                    "id": swarm_data.get("swarm_id"),
                                    "name": swarm_data.get("name"),
                                    "progress": swarm_data.get("progress", {}),
                                })
        except Exception:
            pass

        # Build summary
        pending = len(perception["task_queue"])
        running_swarms = len(perception["swarm_status"])
        budget_ok = perception["budget_status"].get("available", True)
        perception["summary"] = (
            f"Tasks pending: {pending}, Running swarms: {running_swarms}, "
            f"Budget OK: {budget_ok}"
        )

        return perception

    async def _decide(self, perception: dict) -> list:
        """
        DECISION phase: determine what actions to take this cycle.
        Returns a list of action dicts.
        """
        decisions = []

        # Route pending tasks
        try:
            from python.helpers.orchestration_config import load_orchestration_config
            config = load_orchestration_config()
        except ImportError:
            config = None

        for task in perception.get("task_queue", []):
            task_desc = task.get("description", task.get("task", ""))
            if not task_desc:
                continue

            # Route using orchestration config
            if config:
                agent_id = config.route_task(task_desc)
            else:
                agent_id = "developer"  # fallback

            decisions.append({
                "action": "dispatch",
                "task": task_desc,
                "target_agent": agent_id,
                "task_id": task.get("id", "unknown"),
                "priority": task.get("priority", 5),
            })

        # Check for budget downgrade needed
        budget = perception.get("budget_status", {})
        if not budget.get("available", True):
            decisions.append({
                "action": "budget_alert",
                "message": "Monthly budget exceeded — all agents auto-downgraded to free tier",
            })

        # Check for stalled swarms
        for swarm in perception.get("swarm_status", []):
            progress = swarm.get("progress", {})
            if progress.get("running", 0) == 0 and progress.get("pending", 0) > 0:
                decisions.append({
                    "action": "swarm_recovery",
                    "swarm_id": swarm.get("id"),
                    "reason": "Swarm has pending tasks but none running",
                })

        return decisions

    async def _act(self, decisions: list) -> int:
        """
        ACTION phase: execute decisions.
        Returns count of actions taken.
        """
        actions_taken = 0

        for decision in decisions:
            try:
                action_type = decision.get("action", "")

                if action_type == "dispatch":
                    # Log the routing decision (actual dispatch happens via swarm_orchestrator or call_subordinate)
                    PrintStyle.standard(
                        f"[Orchestrator] Routing task to {decision['target_agent']}: "
                        f"{decision['task'][:60]}"
                    )
                    # Mark task as routed in task queue
                    self._mark_task_routed(decision.get("task_id"), decision.get("target_agent"))
                    actions_taken += 1

                elif action_type == "budget_alert":
                    PrintStyle.warning(f"[Orchestrator] {decision['message']}")
                    actions_taken += 1

                elif action_type == "swarm_recovery":
                    PrintStyle.warning(
                        f"[Orchestrator] Swarm recovery needed: {decision['swarm_id']} — "
                        f"{decision['reason']}"
                    )
                    actions_taken += 1

            except Exception as e:
                PrintStyle.error(f"[Orchestrator] Action failed: {e}")

        return actions_taken

    def _mark_task_routed(self, task_id: str, target_agent: str):
        """Update task status in the queue file."""
        task_queue_path = "memory/agent_zero/task_queue.json"
        if not os.path.exists(task_queue_path):
            return

        try:
            with open(task_queue_path, "r") as f:
                tasks = json.load(f)

            for task in tasks:
                if task.get("id") == task_id:
                    task["status"] = "routed"
                    task["routed_to"] = target_agent
                    task["routed_at"] = datetime.now(timezone.utc).isoformat()
                    break

            # Atomic write
            tmp_path = task_queue_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(tasks, f, indent=2)
            os.replace(tmp_path, task_queue_path)
        except Exception:
            pass

    def _persist_state(self, state: dict):
        """Persist loop state atomically."""
        os.makedirs(os.path.dirname(LOOP_STATE_FILE), exist_ok=True)
        tmp_path = LOOP_STATE_FILE + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(state, f, indent=2)
            os.replace(tmp_path, LOOP_STATE_FILE)
        except Exception:
            pass
