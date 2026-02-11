"""
read_deploy_prd — Agent Zero Tool
===================================
Reads the deployment PRD for an app and returns the next unchecked task.
Returns break_loop=True when all tasks are complete (deploy finished).

Tool args:
    app_name: Name of the app (matches workspace/deploys/{app_name}/PRD.md)
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.tool import Tool, Response


class ReadDeployPrd(Tool):

    async def execute(self, **kwargs) -> Response:
        app_name = self.args.get("app_name", "").strip()
        if not app_name:
            return Response(
                message="Error: app_name is required.",
                break_loop=False,
            )

        prd_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "PRD.md"
        if not prd_path.exists():
            return Response(
                message=f"No PRD found for '{app_name}'. Run generate_deploy_prd first.",
                break_loop=False,
            )

        prd_text = prd_path.read_text(encoding="utf-8")

        # Parse all tasks
        tasks = []
        for line in prd_text.splitlines():
            # Match: - [ ] N. STEP — description  or  - [x] N. STEP — description
            m = re.match(r"^- \[([ x])\] (\d+)\.\s+(\w+)\s*[—–-]\s*(.+)$", line.strip())
            if m:
                tasks.append({
                    "done": m.group(1) == "x",
                    "step": int(m.group(2)),
                    "name": m.group(3),
                    "description": m.group(4),
                    "raw": line.strip(),
                })

        if not tasks:
            return Response(
                message=f"PRD for '{app_name}' has no parseable tasks. Check format.",
                break_loop=False,
            )

        # Find next unchecked task
        done_count = sum(1 for t in tasks if t["done"])
        total = len(tasks)

        next_task = None
        for t in tasks:
            if not t["done"]:
                next_task = t
                break

        if next_task is None:
            # All tasks done!
            return Response(
                message=f"ALL TASKS COMPLETE ({done_count}/{total}). "
                        f"Deployment of '{app_name}' is finished! ✓",
                break_loop=True,
            )

        # Load config if available
        config_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "config.json"
        config_info = ""
        if config_path.exists():
            config_info = f"\n\nConfig: {config_path.read_text(encoding='utf-8')}"

        return Response(
            message=f"Progress: {done_count}/{total} tasks complete.\n"
                    f"NEXT TASK: Step {next_task['step']} — {next_task['name']}\n"
                    f"Description: {next_task['description']}\n"
                    f"App: {app_name}{config_info}",
            break_loop=False,
        )
