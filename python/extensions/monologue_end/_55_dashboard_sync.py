"""
Dashboard Sync Hook -- pushes agent-completion events into the
NotificationManager so the master dashboard surfaces them in real time.

Sits at priority 55 -- after the chat-save (_90) ordering is preserved,
but before the TTS hook (_60) fires.  The notification appears on the
dashboard before the spoken announcement plays.

Also updates the TaskBoard snapshot so the swarm status cards refresh.
"""

import asyncio

from python.helpers.extension import Extension
from python.helpers.dirty_json import DirtyJson
from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority
from agent import LoopData


class DashboardSyncHook(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only broadcast for the top-level agent
        if self.agent.number != 0:
            return

        result_text = self._extract_response_text(loop_data)
        if not result_text:
            return

        # Push a SUCCESS notification -- the dashboard toast layer picks this up
        NotificationManager.send_notification(
            type=NotificationType.SUCCESS,
            priority=NotificationPriority.HIGH,
            title=f"{self.agent.agent_name} Complete",
            message=result_text[:300],          # toast-friendly length
            detail=result_text,                 # full text in expandable detail
            display_time=6,                     # seconds before auto-dismiss
            group="agent-completion",
        )

        # Also log to the context log so it shows in the beads timeline
        self.agent.context.log.log(
            type="agent",
            heading=f"icon://check {self.agent.agent_name}: Task Complete",
            content=result_text[:500],
        )

        # Kick a background refresh of the TaskBoard snapshot --
        # the dashboard poll will pick it up on the next 750 ms tick
        asyncio.create_task(self._refresh_board())

    # ── helpers ──────────────────────────────────────────────────────
    def _extract_response_text(self, loop_data: LoopData) -> str:
        raw = getattr(loop_data, "last_response", "")
        if not raw or len(raw) < 10:
            return ""
        try:
            parsed = DirtyJson.parse_string(raw)
            if not isinstance(parsed, dict):
                return ""
            if parsed.get("tool_name") != "response":
                return ""
            args = parsed.get("tool_args", {})
            return args.get("text") or args.get("message") or ""
        except Exception:
            return ""

    async def _refresh_board(self):
        """Touch the task board so its mtime changes -- triggers dashboard refresh."""
        try:
            from python.helpers.task_board import TaskBoard
            board = TaskBoard.get()
            board.snapshot()   # forces a _load if stale; snapshot is read-only
        except Exception:
            pass  # board may not exist yet -- that's fine
