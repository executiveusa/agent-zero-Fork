"""
TTS Completion Hook -- extension that fires at monologue_end.

When the top-level agent (A0) completes a task via the response tool,
this extension synthesises a spoken announcement and plays it locally.

Design decisions:
  - Only fires for agent number 0.  Subordinate completions are internal -- the
    user cares about the top-level result.
  - Parses loop_data.last_response to extract the response-tool text.  This is
    the same JSON the LLM emitted, so no extra round-trip is needed.
  - The actual synthesis + playback runs in a fire-and-forget asyncio task so
    the monologue_end extension chain is never blocked.
  - Controlled by the TTS_ENABLED env var (default true).
"""

import asyncio

from python.helpers.extension import Extension
from python.helpers.dirty_json import DirtyJson
from agent import LoopData


class TTSCompletionHook(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only the top-level agent speaks
        if self.agent.number != 0:
            return

        # Extract the response text from the last LLM message.
        # The LLM emits JSON like:  {"tool_name": "response", "tool_args": {"text": "..."}}
        result_text = self._extract_response_text(loop_data)
        if not result_text:
            return

        # Fire-and-forget -- never blocks the extension chain
        asyncio.create_task(self._announce(result_text))

    # ── helpers ──────────────────────────────────────────────────────
    def _extract_response_text(self, loop_data: LoopData) -> str:
        """Pull the final user-facing text out of last_response."""
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

    async def _announce(self, text: str):
        """Delegate to the TTS engine (import here to keep module-level clean)."""
        from python.helpers.tts_announce import announce_completion
        await announce_completion(self.agent, text)
