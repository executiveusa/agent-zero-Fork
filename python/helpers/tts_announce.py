"""
TTS Announcement Engine

When an agent finishes a task this module:
  1. Condenses the result into a 1-2 sentence spoken summary via the utility model.
  2. Synthesises the summary to audio using the existing Kokoro pipeline.
  3. Plays the WAV on the local machine (paplay → aplay → afplay, first available).

Everything runs in background tasks -- the agent loop is never blocked.

Env switches:
  TTS_ENABLED   "true"/"false"  (default true)
  TTS_VOICE     kokoro voice id (default: inherit from kokoro_tts module)
  TTS_SPEED     float           (default: inherit)
"""

import asyncio
import base64
import os
import platform
import subprocess
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from python.helpers.print_style import PrintStyle


# ── config ───────────────────────────────────────────────────────────────────
_TTS_ENABLED = os.environ.get("TTS_ENABLED", "true").lower() == "true"

# Spoken-summary prompt -- kept short so the utility model stays fast.
_SUMMARY_SYSTEM = """You generate short spoken announcements for an AI agency.
Rules:
- 1 to 2 sentences maximum.
- Start with what finished (e.g. "Scanner", "Deployment", "Implementation").
- State the key outcome.
- Do NOT repeat the full output -- summarise only.
- No markdown, no bullet points. Plain spoken English only.

Examples:
  Input: long code-review text        → "Code review complete. All tests pass, two minor refactors suggested."
  Input: deployment log               → "Deployment finished. The app is live on Vercel."
  Input: scan results with 3 issues   → "Scan complete. Three issues found in the auth module."
"""


# ── public entry-point ────────────────────────────────────────────────────────
async def announce_completion(agent: "Agent", result_text: str) -> None:
    """
    Top-level coroutine.  Fire-and-forget safe -- all errors are caught and
    logged, never raised.
    """
    if not _TTS_ENABLED:
        return

    try:
        # Step 1: condense
        summary = await _generate_summary(agent, result_text)
        if not summary:
            return

        PrintStyle(font_color="#9370DB", bold=True).print(
            f"[TTS] {agent.agent_name}: {summary}"
        )

        # Step 2: synthesise
        audio_b64 = await _synthesise(summary)
        if not audio_b64:
            return

        # Step 3: play (non-blocking)
        asyncio.create_task(_play_audio(audio_b64))

    except Exception as exc:
        PrintStyle(font_color="orange").print(f"[TTS] announcement failed: {exc}")


# ── internals ─────────────────────────────────────────────────────────────────
async def _generate_summary(agent: "Agent", text: str) -> str:
    """Ask the utility model for a TTS-friendly summary."""
    try:
        # Cap input to keep the utility call cheap
        capped = text[:1200]
        summary = await agent.call_utility_model(
            system=_SUMMARY_SYSTEM,
            message=f"Agent {agent.agent_name} completed:\n{capped}",
            background=True,   # does NOT consume the rate-limiter budget
        )
        return summary.strip() if summary else ""
    except Exception as exc:
        PrintStyle(font_color="orange").print(f"[TTS] summary generation failed: {exc}")
        return ""


async def _synthesise(text: str) -> str:
    """Run Kokoro synthesis with espeak-ng fallback.  Returns base64 WAV or empty string."""
    try:
        from python.helpers import kokoro_tts
        audio_b64 = await kokoro_tts.synthesize_sentences([text])
        if audio_b64:
            return audio_b64
    except Exception as exc:
        PrintStyle(font_color="orange").print(f"[TTS] Kokoro synthesis failed: {exc}")

    # espeak-ng fallback — works without GPU or model download
    try:
        import subprocess, tempfile, base64
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        result = subprocess.run(
            ["espeak-ng", "-w", wav_path, text.strip()],
            capture_output=True, timeout=30,
        )
        if result.returncode == 0:
            with open(wav_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            PrintStyle(font_color="#9370DB").print("[TTS] Using espeak-ng fallback")
            return audio_b64
        import os
        os.unlink(wav_path)
    except Exception as exc:
        PrintStyle(font_color="orange").print(f"[TTS] espeak-ng fallback failed: {exc}")

    return ""


async def _play_audio(audio_b64: str) -> None:
    """Decode and play WAV.  Tries platform-appropriate players in order."""
    audio_bytes = base64.b64decode(audio_b64)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # Persist at a predictable path for headless / download access
    persist_path = os.path.join(os.environ.get("WORKSPACE_PATH", "/tmp"), "tts_last.wav")
    try:
        import shutil
        shutil.copy2(tmp_path, persist_path)
    except OSError:
        pass

    try:
        system = platform.system()
        candidates: list[list[str]] = []

        if system == "Linux":
            candidates = [
                ["paplay", tmp_path],          # PulseAudio
                ["aplay", tmp_path],           # ALSA
                ["sox", "-t", "wav", tmp_path, "-d"],  # sox
            ]
        elif system == "Darwin":
            candidates = [["afplay", tmp_path]]
        elif system == "Windows":
            candidates = [["start", "/B", tmp_path]]

        for cmd in candidates:
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    timeout=60,
                    capture_output=True,
                )
                if result.returncode == 0:
                    return  # first success wins
            except (FileNotFoundError, subprocess.SubprocessError):
                continue  # player not installed, try next

        PrintStyle(font_color="orange").print(
            f"[TTS] no audio player available (headless). WAV at: {persist_path}"
        )

    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
