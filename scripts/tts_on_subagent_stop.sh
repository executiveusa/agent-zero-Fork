#!/bin/bash
# tts_on_subagent_stop.sh
# ─────────────────────────────────────────────────────────────────────
# Thin wrapper invoked by .claude/settings.json SubagentStop hook.
# Derives an announcement from env vars and delegates to
# scripts/tts_announce.py (non-blocking -- runs in background).
# ─────────────────────────────────────────────────────────────────────

AGENT_NAME="${CLAUDE_SUBAGENT_NAME:-Subagent}"
STATUS="${CLAUDE_SUBAGENT_STATUS:-0}"

[[ "$STATUS" != "0" ]] && exit 0
[[ "${TTS_ENABLED:-true}" != "true" ]] && exit 0

# Best-effort: run in background, never block the hook
python3 "$(dirname "$0")/tts_announce.py" "${AGENT_NAME} finished." &

exit 0
