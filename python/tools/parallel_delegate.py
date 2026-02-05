"""
Parallel Delegate -- spawns N subordinate agents concurrently and collects results.

This is the key parallelism unlock for the swarm.  Unlike call_subordinate
(which blocks the parent until the single child finishes), parallel_delegate:
  - Creates an *isolated* AgentContext per subtask (no shared-state collisions).
  - Runs all subtasks via asyncio.gather.
  - Registers / transitions each subtask on the TaskBoard so the master
    dashboard can show live progress.
  - Returns a combined result the parent can act on.

The LLM is told how to invoke this tool via
  prompts/agent.system.tool.parallel_delegate.md
"""

import asyncio

from agent import Agent, AgentContext, AgentContextType, UserMessage
from python.helpers.tool import Tool, Response
from python.helpers.task_board import TaskBoard
from python.helpers.print_style import PrintStyle
from initialize import initialize_agent


class ParallelDelegate(Tool):
    """Tool class loaded by the standard extract_tools mechanism."""

    # ── execute ────────────────────────────────────────────────────────
    async def execute(self, tasks: list[dict] | None = None, **kwargs) -> Response:
        tasks = tasks or []
        if not tasks:
            return Response(
                message="parallel_delegate: no tasks provided. "
                        "Pass a JSON array under the 'tasks' key.",
                break_loop=False,
            )

        board = TaskBoard.get()

        # 1. Register every task on the board *before* any work starts so the
        #    dashboard can show them immediately.
        task_ids: list[str] = []
        for t in tasks:
            tid = board.register(
                title=t.get("message", "")[:100],
                owner=self.agent.agent_name,
                metadata={"profile": t.get("profile", "")},
            )
            task_ids.append(tid)

        # 2. Log the fan-out
        self.agent.context.log.log(
            type="tool",
            heading=f"icon://layers {self.agent.agent_name}: "
                    f"Parallel Delegation ({len(tasks)} tasks)",
            content="\n".join(f"  • {t.get('message', '')[:90]}" for t in tasks),
        )

        # 3. Fire them all concurrently.  return_exceptions=True so one failure
        #    does not cancel the others.
        results = await asyncio.gather(
            *[
                self._run_subtask(task, tid)
                for task, tid in zip(tasks, task_ids)
            ],
            return_exceptions=True,
        )

        # 4. Assemble the combined output and finalise board entries
        parts: list[str] = []
        for i, (task, tid, result) in enumerate(zip(tasks, task_ids, results)):
            label = task.get("message", "task")[:70]
            if isinstance(result, BaseException):
                board.fail(tid, str(result))
                parts.append(f"[Task {i + 1} FAILED] {label}\nError: {result}")
            else:
                board.complete(tid, result)
                parts.append(f"[Task {i + 1} DONE] {label}\nResult: {result}")

        return Response(
            message="\n\n---\n\n".join(parts),
            break_loop=False,
        )

    # ── subtask runner ─────────────────────────────────────────────────
    async def _run_subtask(self, task: dict, task_id: str) -> str:
        """Execute one subtask in a fully isolated AgentContext."""
        board = TaskBoard.get()
        board.claim(task_id, f"{self.agent.agent_name}/sub")

        # Initialise a fresh config, optionally with a specialised profile
        config = initialize_agent()
        profile = task.get("profile", "")
        if profile:
            config.profile = profile

        # Isolated BACKGROUND context -- ephemeral, removed on completion
        sub_context = AgentContext(
            config=config,
            type=AgentContextType.BACKGROUND,
            name=f"par-{task_id}",
        )

        try:
            sub_agent = sub_context.agent0
            sub_agent.hist_add_user_message(
                UserMessage(
                    message=task.get("message", ""),
                    attachments=task.get("attachments", []),
                )
            )
            result = await sub_agent.monologue()
            return result if result else "Subtask completed (no output)."
        finally:
            AgentContext.remove(sub_context.id)

    # ── logging ────────────────────────────────────────────────────────
    def get_log_object(self):
        tasks = self.args.get("tasks", [])
        return self.agent.context.log.log(
            type="tool",
            heading=(
                f"icon://layers {self.agent.agent_name}: "
                f"Parallel Delegation ({len(tasks)} tasks)"
            ),
            content="\n".join(f"  • {t.get('message', '')[:90]}" for t in tasks),
            kvps={"task_count": len(tasks)},
        )
