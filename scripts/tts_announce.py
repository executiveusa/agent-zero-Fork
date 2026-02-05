#!/usr/bin/env python3
"""
Standalone TTS announcement script.

Called by Claude Code hooks and shell scripts where the full Agent Zero
runtime is not available.  Uses Kokoro for synthesis and the system's
audio player for playback.

Usage:
    python3 scripts/tts_announce.py "Scanner complete. Three issues found."

Env:
    TTS_ENABLED   true|false  (default true)
    TTS_VOICE     kokoro voice string (default am_puck,am_onyx)
    TTS_SPEED     float (default 1.1)
"""

import asyncio
import base64
import io
import os
import platform
import subprocess
import sys
import tempfile


async def synthesise(text: str) -> bytes:
    """Synthesise text to WAV bytes using Kokoro."""
    import warnings
    warnings.filterwarnings("ignore")

    from kokoro import KPipeline  # type: ignore[import-untyped]

    voice = os.environ.get("TTS_VOICE", "am_puck,am_onyx")
    speed = float(os.environ.get("TTS_SPEED", "1.1"))

    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    segments = pipeline(text.strip(), voice=voice, speed=speed)

    import soundfile as sf  # type: ignore[import-untyped]
    combined: list = []
    for seg in segments:
        audio_np = seg.audio.detach().cpu().numpy()
        combined.extend(audio_np)

    buf = io.BytesIO()
    sf.write(buf, combined, 24000, format="WAV")
    return buf.getvalue()


async def play(wav_bytes: bytes) -> None:
    """Write WAV to a temp file and play with the first available system player."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    try:
        system = platform.system()
        candidates: list[list[str]] = []

        if system == "Linux":
            candidates = [
                ["paplay", tmp_path],
                ["aplay", tmp_path],
                ["sox", "-t", "wav", tmp_path, "-d"],
            ]
        elif system == "Darwin":
            candidates = [["afplay", tmp_path]]
        elif system == "Windows":
            candidates = [["start", "/B", tmp_path]]

        for cmd in candidates:
            try:
                subprocess.run(cmd, timeout=60, capture_output=True, check=False)
                return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        # Fallback: just print the path
        print(f"[TTS] No audio player found. WAV saved at: {tmp_path}")
        return  # don't delete

    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


async def main():
    if os.environ.get("TTS_ENABLED", "true").lower() != "true":
        return

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not text:
        print("[TTS] No text provided.", file=sys.stderr)
        sys.exit(1)

    print(f"[TTS] Synthesising: {text}")
    wav = await synthesise(text)
    print("[TTS] Playing...")
    await play(wav)


if __name__ == "__main__":
    asyncio.run(main())
