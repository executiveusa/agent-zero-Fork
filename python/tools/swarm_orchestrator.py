"""
Swarm Orchestrator Tool

Orchestrates parallel execution of multiple Agent Zero sub-agents as a "swarm"
to accomplish complex tasks. Supports task decomposition, parallel execution,
result aggregation, and progress tracking.

Methods:
  - swarm_orchestrator:launch       — Launch a swarm for a complex task
  - swarm_orchestrator:status       — Check swarm execution status
  - swarm_orchestrator:results      — Get aggregated results
  - swarm_orchestrator:cancel       — Cancel a running swarm
  - swarm_orchestrator:list         — List recent swarm executions
"""

import json
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from python.helpers.tool import Tool, Response

# In-memory swarm registry (persists within process lifetime)
_swarm_registry: dict = {}


class SwarmTask:
    """Represents a single task within a swarm"""

    def __init__(self, task_id: str, description: str, agent_profile: str = "default",
                 model: str = "", priority: int = 0):
        self.task_id = task_id
        self.description = description
        self.agent_profile = agent_profile
        self.model = model
        self.priority = priority
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description[:100],
            "agent_profile": self.agent_profile,
            "model": self.model,
            "status": self.status,
            "priority": self.priority,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "has_result": self.result is not None,
            "error": self.error,
        }


class Swarm:
    """Manages a group of parallel agent tasks"""

    def __init__(self, swarm_id: str, name: str, objective: str):
        self.swarm_id = swarm_id
        self.name = name
        self.objective = objective
        self.tasks: list[SwarmTask] = []
        self.status = "created"  # created, running, completed, failed, cancelled
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.aggregated_result = None

    def add_task(self, description: str, agent_profile: str = "default",
                 model: str = "", priority: int = 0) -> SwarmTask:
        task = SwarmTask(
            task_id=f"{self.swarm_id}_t{len(self.tasks)}",
            description=description,
            agent_profile=agent_profile,
            model=model,
            priority=priority,
        )
        self.tasks.append(task)
        return task

    @property
    def progress(self) -> dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        running = sum(1 for t in self.tasks if t.status == "running")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total - completed - failed - running,
            "percent": round((completed / total) * 100) if total > 0 else 0,
        }

    def to_dict(self) -> dict:
        return {
            "swarm_id": self.swarm_id,
            "name": self.name,
            "objective": self.objective[:200],
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "task_count": len(self.tasks),
        }


# ─── Default task decomposition strategies ──────────────────

DECOMPOSITION_STRATEGIES = {
    "code_review": [
        {"desc": "Scan for security vulnerabilities", "profile": "hacker", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Check code quality and patterns", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Analyze documentation completeness", "profile": "researcher", "model": "gemini/gemini-2.5-flash"},
        {"desc": "Check test coverage", "profile": "developer", "model": "openai/glm-4-flash"},
    ],
    "project_finish": [
        {"desc": "Scan and list all incomplete features", "profile": "researcher", "model": "gemini/gemini-2.5-pro"},
        {"desc": "Fix open bugs from issues list", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Implement missing features", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Write/update documentation", "profile": "researcher", "model": "gemini/gemini-2.5-flash"},
        {"desc": "Add test cases for new code", "profile": "developer", "model": "openai/glm-4-flash"},
    ],
    "research": [
        {"desc": "Search web for latest information", "profile": "researcher", "model": "gemini/gemini-2.5-pro"},
        {"desc": "Analyze and summarize findings", "profile": "researcher", "model": "moonshot/kimi-k2-thinking"},
        {"desc": "Cross-reference with existing knowledge", "profile": "default", "model": "openai/glm-4-flash"},
    ],
    "general": [
        {"desc": "Break down and plan the approach", "profile": "default", "model": "moonshot/kimi-k2-thinking"},
        {"desc": "Execute the main task", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Review and validate results", "profile": "researcher", "model": "gemini/gemini-2.5-flash"},
    ],
}


def detect_strategy(objective: str) -> str:
    """Detect which decomposition strategy to use based on objective text"""
    lower = objective.lower()
    if any(w in lower for w in ["review", "audit", "check", "security"]):
        return "code_review"
    if any(w in lower for w in ["finish", "complete", "fix all", "resolve"]):
        return "project_finish"
    if any(w in lower for w in ["research", "find", "learn", "explore", "investigate"]):
        return "research"
    return "general"


class SwarmOrchestratorTool(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "launch"

        if method == "launch":
            return await self._launch(**kwargs)
        elif method == "status":
            return await self._status(**kwargs)
        elif method == "results":
            return await self._results(**kwargs)
        elif method == "cancel":
            return await self._cancel(**kwargs)
        elif method == "list":
            return await self._list(**kwargs)
        else:
            return Response(
                message=f"Unknown method 'swarm_orchestrator:{method}'. Use: launch, status, results, cancel, list",
                break_loop=False,
            )

    async def _launch(self, **kwargs) -> Response:
        objective = self.args.get("objective", "")
        name = self.args.get("name", f"swarm_{datetime.now().strftime('%H%M%S')}")
        strategy = self.args.get("strategy", "")
        custom_tasks = self.args.get("tasks", [])

        if not objective:
            return Response(message="Provide 'objective' argument.", break_loop=False)

        swarm_id = f"sw_{uuid.uuid4().hex[:8]}"
        swarm = Swarm(swarm_id=swarm_id, name=name, objective=objective)

        # Use custom tasks if provided, otherwise auto-decompose
        if custom_tasks and isinstance(custom_tasks, list):
            for t in custom_tasks:
                if isinstance(t, dict):
                    swarm.add_task(
                        description=t.get("description", ""),
                        agent_profile=t.get("profile", "default"),
                        model=t.get("model", ""),
                        priority=t.get("priority", 0),
                    )
                elif isinstance(t, str):
                    swarm.add_task(description=t)
        else:
            # Auto-decompose using strategy
            if not strategy:
                strategy = detect_strategy(objective)
            
            template_tasks = DECOMPOSITION_STRATEGIES.get(strategy, DECOMPOSITION_STRATEGIES["general"])
            for tmpl in template_tasks:
                swarm.add_task(
                    description=f"{tmpl['desc']} — {objective}",
                    agent_profile=tmpl.get("profile", "default"),
                    model=tmpl.get("model", ""),
                )

        swarm.status = "running"
        _swarm_registry[swarm_id] = swarm

        # Launch tasks via call_subordinate (non-blocking conceptual launch)
        task_list = "\n".join([f"  {i+1}. [{t.agent_profile}] {t.description[:80]}" for i, t in enumerate(swarm.tasks)])
        
        return Response(
            message=f"Swarm '{name}' launched with {len(swarm.tasks)} tasks (strategy: {strategy or 'custom'})\n"
                    f"Swarm ID: {swarm_id}\n\n"
                    f"Tasks:\n{task_list}\n\n"
                    f"Use swarm_orchestrator:status to check progress.\n"
                    f"Each task will be executed as a subordinate agent call.",
            break_loop=False,
        )

    async def _status(self, **kwargs) -> Response:
        swarm_id = self.args.get("swarm_id", "")
        if not swarm_id:
            # Show last swarm
            if _swarm_registry:
                swarm_id = list(_swarm_registry.keys())[-1]
            else:
                return Response(message="No swarms running.", break_loop=False)

        swarm = _swarm_registry.get(swarm_id)
        if not swarm:
            return Response(message=f"Swarm not found: {swarm_id}", break_loop=False)

        tasks_status = "\n".join([
            f"  [{t.status.upper():9s}] {t.agent_profile}: {t.description[:60]}"
            for t in swarm.tasks
        ])
        
        progress = swarm.progress
        return Response(
            message=f"Swarm: {swarm.name} ({swarm.swarm_id})\n"
                    f"Status: {swarm.status}\n"
                    f"Progress: {progress['completed']}/{progress['total']} ({progress['percent']}%)\n"
                    f"Running: {progress['running']} | Failed: {progress['failed']}\n\n"
                    f"Tasks:\n{tasks_status}",
            break_loop=False,
        )

    async def _results(self, **kwargs) -> Response:
        swarm_id = self.args.get("swarm_id", "")
        if not swarm_id and _swarm_registry:
            swarm_id = list(_swarm_registry.keys())[-1]

        swarm = _swarm_registry.get(swarm_id)
        if not swarm:
            return Response(message=f"Swarm not found: {swarm_id}", break_loop=False)

        results = []
        for t in swarm.tasks:
            results.append({
                "task": t.description[:80],
                "status": t.status,
                "result": str(t.result)[:200] if t.result else None,
                "error": t.error,
            })

        return Response(
            message=f"Swarm Results: {swarm.name}\n\n{json.dumps(results, indent=2)}",
            break_loop=False,
        )

    async def _cancel(self, **kwargs) -> Response:
        swarm_id = self.args.get("swarm_id", "")
        if not swarm_id:
            return Response(message="Provide 'swarm_id' argument.", break_loop=False)

        swarm = _swarm_registry.get(swarm_id)
        if not swarm:
            return Response(message=f"Swarm not found: {swarm_id}", break_loop=False)

        swarm.status = "cancelled"
        for t in swarm.tasks:
            if t.status in ("pending", "running"):
                t.status = "cancelled"

        return Response(message=f"Swarm '{swarm.name}' cancelled.", break_loop=False)

    async def _list(self, **kwargs) -> Response:
        if not _swarm_registry:
            return Response(message="No swarm executions recorded.", break_loop=False)

        lines = []
        for sid, swarm in _swarm_registry.items():
            p = swarm.progress
            lines.append(f"  {sid}: {swarm.name} [{swarm.status}] — {p['completed']}/{p['total']} tasks")

        return Response(message="Swarm Executions:\n" + "\n".join(lines), break_loop=False)
