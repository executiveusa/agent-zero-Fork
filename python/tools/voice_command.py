"""
voice_command.py — SYNTHIA Voice Command Router Tool

Agent Zero Tool subclass that matches spoken/typed utterances to
registered commands and returns routing information for dispatch.

Methods:
  route        — Match an utterance and return the best command match
  help         — Return a formatted help listing of all commands
  execute      — Match + build the tool call in one step (convenience)

Convention: Agent Zero auto-discovers this via importlib from python/tools/
"""

import json
from python.helpers.tool import Tool, Response
from agent import Agent


class VoiceCommand(Tool):
    """Routes voice/text commands to the correct Agent Zero tool."""

    async def execute(self, **kwargs):
        from python.helpers.voice_command_router import VoiceCommandRouter, CommandCategory

        method = self.args.get("method", "route")
        router = VoiceCommandRouter()

        # ── route: match an utterance ────────────────────────────
        if method == "route":
            utterance = self.args.get("utterance", "").strip()
            if not utterance:
                return Response(
                    message="No utterance provided. Pass 'utterance' in tool_args.",
                    break_loop=False,
                )

            match = router.match(utterance)
            if match is None:
                return Response(
                    message=(
                        f"No command matched for: \"{utterance}\"\n"
                        "Treat this as a general conversation request."
                    ),
                    break_loop=False,
                )

            result = {
                "matched_command": match.command.id,
                "confidence": round(match.confidence, 2),
                "tool_name": match.command.tool_name,
                "tool_args_template": match.command.tool_args_template,
                "missing_slots": match.missing_slots,
                "category": match.command.category.value,
                "needs_confirmation": match.command.confirm,
                "admin_only": match.command.admin_only,
                "raw_utterance": utterance,
            }

            summary = (
                f"Matched **{match.command.id}** (confidence {match.confidence:.0%})\n"
                f"→ Tool: `{match.command.tool_name}`\n"
            )
            if match.missing_slots:
                summary += f"⚠ Missing slots: {', '.join(match.missing_slots)}\n"
            if match.command.confirm:
                summary += "⚠ This command requires user confirmation before executing.\n"

            return Response(
                message=summary + "\n```json\n" + json.dumps(result, indent=2) + "\n```",
                break_loop=False,
            )

        # ── help: list all commands ──────────────────────────────
        elif method == "help":
            category_filter = self.args.get("category", None)
            if category_filter:
                try:
                    cat = CommandCategory(category_filter)
                    cmds = router.get_commands_by_category(cat)
                    lines = [f"## {cat.value} Commands\n"]
                    for c in cmds:
                        triggers = ", ".join(c.triggers[:3])
                        lines.append(f"- **{c.id}** — \"{triggers}\" → `{c.tool_name}`")
                    return Response(message="\n".join(lines), break_loop=False)
                except ValueError:
                    valid = [c.value for c in CommandCategory]
                    return Response(
                        message=f"Unknown category '{category_filter}'. Valid: {', '.join(valid)}",
                        break_loop=False,
                    )

            return Response(message=router.get_help_text(), break_loop=False)

        # ── execute: match + build full tool invocation ──────────
        elif method == "execute":
            utterance = self.args.get("utterance", "").strip()
            if not utterance:
                return Response(
                    message="No utterance provided.",
                    break_loop=False,
                )

            match = router.match(utterance)
            if match is None:
                return Response(
                    message=f"No command matched for: \"{utterance}\"",
                    break_loop=False,
                )

            # Build the tool_args from template + any provided overrides
            tool_args = dict(match.command.tool_args_template)
            overrides = self.args.get("slot_values", {})
            if isinstance(overrides, dict):
                tool_args.update(overrides)

            invocation = {
                "tool_name": match.command.tool_name,
                "tool_args": tool_args,
                "confidence": round(match.confidence, 2),
                "needs_confirmation": match.command.confirm,
            }

            msg = (
                f"Ready to invoke **{match.command.tool_name}**\n"
                f"```json\n{json.dumps(invocation, indent=2)}\n```"
            )
            return Response(message=msg, break_loop=False)

        # ── unknown method ───────────────────────────────────────
        else:
            return Response(
                message=(
                    f"Unknown method '{method}'. "
                    "Available: route, help, execute"
                ),
                break_loop=False,
            )
