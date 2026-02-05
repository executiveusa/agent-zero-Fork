#!/bin/bash
# tts-on-complete.sh
# ─────────────────────────────────────────────────────────────────────
# Claude Code SubagentStop hook.
# Fires every time a Claude Code subagent finishes.
# Reads the agent name from the environment and triggers a TTS
# announcement via the standalone tts_announce.py script.
#
# Claude Code sets these env vars on SubagentStop:
#   CLAUDE_SUBAGENT_NAME   – name of the subagent that just stopped
#   CLAUDE_SUBAGENT_STATUS – exit code (0 = success)
#
# If the env vars are not set (e.g. manual invocation) we fall back
# to sensible defaults.
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

AGENT_NAME="${CLAUDE_SUBAGENT_NAME:-Agent}"
STATUS="${CLAUDE_SUBAGENT_STATUS:-0}"

# Only announce on success
if [[ "$STATUS" != "0" ]]; then
    exit 0
fi

# TTS_ENABLED gate (honour the same env var the Python module uses)
if [[ "${TTS_ENABLED:-true}" != "true" ]]; then
    exit 0
fi

# Run in background so the hook returns immediately and does not
# delay the Claude Code workflow.
python3 scripts/tts_announce.py "${AGENT_NAME} finished successfully." &

exit 0
