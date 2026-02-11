"""
mark_task_done — Agent Zero Tool
==================================
Marks a specific PRD task as complete and logs the result.

Tool args:
    app_name:  Name of the app
    step:      Step number (1-11)
    result:    Brief result description (e.g. "App UUID: abc123")
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.tool import Tool, Response


class MarkTaskDone(Tool):

    async def execute(self, **kwargs) -> Response:
        app_name = self.args.get("app_name", "").strip()
        step_str = self.args.get("step", "").strip()
        result_text = self.args.get("result", "done").strip()

        if not app_name or not step_str:
            return Response(
                message="Error: app_name and step are required.",
                break_loop=False,
            )

        try:
            step_num = int(step_str)
        except ValueError:
            return Response(
                message=f"Error: step must be a number, got '{step_str}'.",
                break_loop=False,
            )

        prd_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "PRD.md"
        if not prd_path.exists():
            return Response(
                message=f"No PRD found for '{app_name}'.",
                break_loop=False,
            )

        prd_text = prd_path.read_text(encoding="utf-8")
        lines = prd_text.splitlines()

        # Find and mark the task
        found = False
        for i, line in enumerate(lines):
            pattern = rf"^- \[ \] {step_num}\.\s+"
            if re.match(pattern, line.strip()):
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                found = True
                break

        if not found:
            return Response(
                message=f"Step {step_num} not found or already marked done.",
                break_loop=False,
            )

        # Append to progress log
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        log_entry = f"- **Step {step_num}** completed at {timestamp}: {result_text}"
        lines.append(log_entry)

        # Write back
        prd_path.write_text("\n".join(lines), encoding="utf-8")

        # Count progress
        done_count = sum(1 for l in lines if re.match(r"^- \[x\] \d+\.", l.strip()))
        total = sum(1 for l in lines if re.match(r"^- \[[x ]\] \d+\.", l.strip()))

        return Response(
            message=f"Step {step_num} marked DONE. Progress: {done_count}/{total}. "
                    f"Result: {result_text}",
            break_loop=False,
        )
