"""
Swarm Orchestrator Tool — AGENT CLAW EDITION

Orchestrates parallel execution of multiple Agent Zero sub-agents as a "swarm".
FULLY WIRED: tasks are actually dispatched to subordinate agents via call_subordinate.

Architecture follows the Ralphie 30-second loop:
  Perception → check task statuses, read queue, assess capacity
  Decision   → decompose objective, route tasks to agents
  Action     → dispatch via subordinate calls, persist state atomically

Methods:
  - swarm_orchestrator:launch       — Launch a swarm for a complex task
  - swarm_orchestrator:status       — Check swarm execution status
  - swarm_orchestrator:results      — Get aggregated results
  - swarm_orchestrator:cancel       — Cancel a running swarm
  - swarm_orchestrator:list         — List recent swarm executions

Created: 2026-02-09 (Agent Claw GAP 4 rewrite)
"""

import json
import asyncio
import uuid
import os
from datetime import datetime, timezone
from typing import Optional
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.tkgm_memory import ByteRoverAtomic
from agent import Agent, UserMessage
from initialize import initialize_agent

# ─── Persistence ─────────────────────────────────────────────

SWARM_DIR = "tmp/swarms"

# In-memory swarm registry (hydrated from disk on first access)
_swarm_registry: dict = {}
_registry_loaded = False


def _load_registry():
    """Load all persisted swarms from disk."""
    global _swarm_registry, _registry_loaded
    if _registry_loaded:
        return
    
    if os.path.exists(SWARM_DIR):
        for fname in os.listdir(SWARM_DIR):
            if fname.endswith(".json"):
                data = ByteRoverAtomic.read(os.path.join(SWARM_DIR, fname))
                if data and "swarm_id" in data:
                    swarm = Swarm.from_dict(data)
                    _swarm_registry[swarm.swarm_id] = swarm
    _registry_loaded = True


def _persist_swarm(swarm: "Swarm"):
    """Persist swarm state atomically."""
    ByteRoverAtomic.write(
        os.path.join(SWARM_DIR, f"{swarm.swarm_id}.json"),
        swarm.to_dict(include_results=True),
    )


# ─── SwarmTask ───────────────────────────────────────────────

class SwarmTask:
    """Represents a single task within a swarm"""

    def __init__(self, task_id: str, description: str, agent_profile: str = "default",
                 model: str = "", priority: int = 0, max_seconds: int = 300):
        self.task_id = task_id
        self.description = description
        self.agent_profile = agent_profile
        self.model = model
        self.priority = priority
        self.max_seconds = max_seconds
        self.status = "pending"  # pending, running, completed, failed, cancelled, timeout
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.retries = 0
        self.max_retries = 2

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "agent_profile": self.agent_profile,
            "model": self.model,
            "status": self.status,
            "priority": self.priority,
            "max_seconds": self.max_seconds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error,
            "retries": self.retries,
        }

    @staticmethod
    def from_dict(data: dict) -> "SwarmTask":
        t = SwarmTask(
            task_id=data.get("task_id", ""),
            description=data.get("description", ""),
            agent_profile=data.get("agent_profile", "default"),
            model=data.get("model", ""),
            priority=data.get("priority", 0),
            max_seconds=data.get("max_seconds", 300),
        )
        t.status = data.get("status", "pending")
        t.result = data.get("result")
        t.error = data.get("error")
        t.started_at = data.get("started_at")
        t.completed_at = data.get("completed_at")
        t.retries = data.get("retries", 0)
        return t


# ─── Swarm ───────────────────────────────────────────────────

class Swarm:
    """Manages a group of parallel agent tasks"""

    def __init__(self, swarm_id: str, name: str, objective: str):
        self.swarm_id = swarm_id
        self.name = name
        self.objective = objective
        self.tasks: list[SwarmTask] = []
        self.status = "created"  # created, running, completed, failed, cancelled
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.completed_at = None
        self.aggregated_result = None

    def add_task(self, description: str, agent_profile: str = "default",
                 model: str = "", priority: int = 0, max_seconds: int = 300) -> SwarmTask:
        task = SwarmTask(
            task_id=f"{self.swarm_id}_t{len(self.tasks)}",
            description=description,
            agent_profile=agent_profile,
            model=model,
            priority=priority,
            max_seconds=max_seconds,
        )
        self.tasks.append(task)
        return task

    @property
    def progress(self) -> dict:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status in ("failed", "timeout"))
        running = sum(1 for t in self.tasks if t.status == "running")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total - completed - failed - running,
            "percent": round((completed / total) * 100) if total > 0 else 0,
        }

    def to_dict(self, include_results: bool = False) -> dict:
        d = {
            "swarm_id": self.swarm_id,
            "name": self.name,
            "objective": self.objective,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
            "task_count": len(self.tasks),
            "tasks": [t.to_dict() for t in self.tasks],
        }
        if include_results and self.aggregated_result:
            d["aggregated_result"] = str(self.aggregated_result)[:2000]
        return d

    @staticmethod
    def from_dict(data: dict) -> "Swarm":
        s = Swarm(
            swarm_id=data.get("swarm_id", ""),
            name=data.get("name", ""),
            objective=data.get("objective", ""),
        )
        s.status = data.get("status", "created")
        s.created_at = data.get("created_at", "")
        s.completed_at = data.get("completed_at")
        s.aggregated_result = data.get("aggregated_result")
        for t_data in data.get("tasks", []):
            s.tasks.append(SwarmTask.from_dict(t_data))
        return s

    def check_completion(self):
        """Check if all tasks are done and update swarm status."""
        p = self.progress
        if p["pending"] == 0 and p["running"] == 0:
            if p["failed"] > 0 and p["completed"] == 0:
                self.status = "failed"
            else:
                self.status = "completed"
            self.completed_at = datetime.now(timezone.utc).isoformat()


# ─── Decomposition Strategies ────────────────────────────────
# Updated to use 7 Agent Claw roles from orchestration.yaml

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
    "design": [
        {"desc": "Generate design system specification", "profile": "default", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Create UI component library", "profile": "default", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Validate accessibility compliance", "profile": "default", "model": "openai/glm-4-flash"},
    ],
    "deployment": [
        {"desc": "Verify container health", "profile": "default", "model": "openai/glm-4-flash"},
        {"desc": "Run deployment checks", "profile": "default", "model": "openai/glm-4-flash"},
        {"desc": "Update infrastructure config", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
    ],
    "agency": [
        {"desc": "Research and qualify leads", "profile": "researcher", "model": "gemini/gemini-2.5-pro"},
        {"desc": "Generate marketing content", "profile": "default", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Design landing pages", "profile": "default", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Set up automation workflows", "profile": "developer", "model": "openai/glm-4-flash"},
    ],
    "general": [
        {"desc": "Break down and plan the approach", "profile": "default", "model": "moonshot/kimi-k2-thinking"},
        {"desc": "Execute the main task", "profile": "developer", "model": "moonshot/kimi-k2-turbo-preview"},
        {"desc": "Review and validate results", "profile": "researcher", "model": "gemini/gemini-2.5-flash"},
    ],
}


def detect_strategy(objective: str) -> str:
    """Detect which decomposition strategy to use based on objective text."""
    lower = objective.lower()
    if any(w in lower for w in ["review", "audit", "check", "security"]):
        return "code_review"
    if any(w in lower for w in ["finish", "complete", "fix all", "resolve"]):
        return "project_finish"
    if any(w in lower for w in ["research", "find", "learn", "explore", "investigate"]):
        return "research"
    if any(w in lower for w in ["design", "ui", "ux", "layout", "style"]):
        return "design"
    if any(w in lower for w in ["deploy", "release", "infrastructure", "container"]):
        return "deployment"
    if any(w in lower for w in ["agency", "leads", "marketing", "clients", "revenue"]):
        return "agency"
    return "general"


# ─── Subordinate Dispatch ────────────────────────────────────

async def _dispatch_task(parent_agent: Agent, task: SwarmTask) -> str:
    """
    Actually dispatch a task to a subordinate agent.
    This is the critical GAP 4 fix — tasks now execute for real.
    """
    task.status = "running"
    task.started_at = datetime.now(timezone.utc).isoformat()
    
    try:
        # Initialize subordinate config
        config = initialize_agent()
        
        # Set profile if specified
        if task.agent_profile and task.agent_profile != "default":
            config.profile = task.agent_profile
        
        # Create subordinate agent
        sub = Agent(parent_agent.number + 1, config, parent_agent.context)
        sub.set_data(Agent.DATA_NAME_SUPERIOR, parent_agent)
        
        # Send task message
        message = (
            f"SWARM TASK [{task.task_id}]: {task.description}\n\n"
            f"You are executing as part of a swarm. Complete this specific task and return your results. "
            f"Be thorough but concise. Focus only on this task."
        )
        sub.hist_add_user_message(UserMessage(message=message, attachments=[]))
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                sub.monologue(),
                timeout=task.max_seconds,
            )
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc).isoformat()
        except asyncio.TimeoutError:
            task.status = "timeout"
            task.error = f"Task exceeded {task.max_seconds}s timeout"
            task.completed_at = datetime.now(timezone.utc).isoformat()
            
            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = "pending"
                task.error = f"Timeout (retry {task.retries}/{task.max_retries})"
        
        return task.result or task.error or "No result"
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now(timezone.utc).isoformat()
        PrintStyle.error(f"Swarm task {task.task_id} failed: {e}")
        return f"Error: {e}"


async def _execute_swarm(parent_agent: Agent, swarm: Swarm):
    """
    Execute all tasks in a swarm in parallel.
    Follows Ralphie Action phase pattern.
    """
    swarm.status = "running"
    _persist_swarm(swarm)
    
    # Sort tasks by priority (lower = higher priority)
    sorted_tasks = sorted(swarm.tasks, key=lambda t: t.priority)
    
    # Launch all tasks concurrently
    dispatch_coroutines = [
        _dispatch_task(parent_agent, task) 
        for task in sorted_tasks 
        if task.status == "pending"
    ]
    
    if dispatch_coroutines:
        await asyncio.gather(*dispatch_coroutines, return_exceptions=True)
    
    # Check for retries
    retry_tasks = [t for t in swarm.tasks if t.status == "pending" and t.retries > 0]
    if retry_tasks:
        retry_coroutines = [_dispatch_task(parent_agent, task) for task in retry_tasks]
        await asyncio.gather(*retry_coroutines, return_exceptions=True)
    
    # Aggregate results
    results = []
    for task in swarm.tasks:
        if task.result:
            results.append(f"[{task.agent_profile}] {task.description[:60]}: {str(task.result)[:200]}")
    
    swarm.aggregated_result = "\n\n".join(results) if results else "No results collected"
    swarm.check_completion()
    _persist_swarm(swarm)


# ─── Tool Implementation ────────────────────────────────────

class SwarmOrchestratorTool(Tool):

    async def execute(self, **kwargs) -> Response:
        _load_registry()
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
        name = self.args.get("name", f"swarm_{datetime.now(timezone.utc).strftime('%H%M%S')}")
        strategy = self.args.get("strategy", "")
        custom_tasks = self.args.get("tasks", [])
        max_seconds = int(self.args.get("max_seconds", 300))

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
                        max_seconds=t.get("max_seconds", max_seconds),
                    )
                elif isinstance(t, str):
                    swarm.add_task(description=t, max_seconds=max_seconds)
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
                    max_seconds=max_seconds,
                )

        _swarm_registry[swarm_id] = swarm

        # Record cost tracking
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            # Cost tracking happens inside each subordinate call
        except ImportError:
            pass

        # ACTUALLY DISPATCH — this is the GAP 4 fix
        # Launch execution in background so we can return immediately
        asyncio.create_task(_execute_swarm(self.agent, swarm))

        task_list = "\n".join([f"  {i+1}. [{t.agent_profile}] {t.description[:80]}" for i, t in enumerate(swarm.tasks)])
        
        return Response(
            message=f"Swarm '{name}' launched with {len(swarm.tasks)} tasks (strategy: {strategy or 'custom'})\n"
                    f"Swarm ID: {swarm_id}\n\n"
                    f"Tasks (DISPATCHING NOW):\n{task_list}\n\n"
                    f"Tasks are being executed by subordinate agents in parallel.\n"
                    f"Use swarm_orchestrator:status to check progress.",
            break_loop=False,
        )

    async def _status(self, **kwargs) -> Response:
        swarm_id = self.args.get("swarm_id", "")
        if not swarm_id:
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
                "task": t.description[:100],
                "profile": t.agent_profile,
                "status": t.status,
                "result": str(t.result)[:300] if t.result else None,
                "error": t.error,
                "retries": t.retries,
            })

        summary = f"Swarm Results: {swarm.name} [{swarm.status}]\n"
        if swarm.aggregated_result:
            summary += f"\nAGGREGATED:\n{swarm.aggregated_result[:1000]}\n"
        summary += f"\nDETAILS:\n{json.dumps(results, indent=2)}"

        return Response(message=summary, break_loop=False)

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
        _persist_swarm(swarm)

        return Response(message=f"Swarm '{swarm.name}' cancelled.", break_loop=False)

    async def _list(self, **kwargs) -> Response:
        if not _swarm_registry:
            return Response(message="No swarm executions recorded.", break_loop=False)

        lines = []
        for sid, swarm in _swarm_registry.items():
            p = swarm.progress
            lines.append(f"  {sid}: {swarm.name} [{swarm.status}] — {p['completed']}/{p['total']} tasks")

        return Response(message="Swarm Executions:\n" + "\n".join(lines), break_loop=False)

