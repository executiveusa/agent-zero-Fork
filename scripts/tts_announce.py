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
    """Synthesise text to WAV bytes.  Kokoro first, espeak-ng fallback."""
    try:
        return await _synthesise_kokoro(text)
    except Exception as e:
        print(f"[TTS] Kokoro unavailable ({e}), falling back to espeak-ng")
        return await _synthesise_espeak(text)


async def _synthesise_kokoro(text: str) -> bytes:
    """Kokoro (Kokoro-82M) synthesis."""
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


async def _synthesise_espeak(text: str) -> bytes:
    """espeak-ng fallback — no GPU or model download required."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        result = subprocess.run(
            ["espeak-ng", "-w", wav_path, text.strip()],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"espeak-ng exited {result.returncode}: {result.stderr.decode()}")
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)


async def play(wav_bytes: bytes) -> None:
    """Write WAV to a temp file and play with the first available system player."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    # Always persist a copy at a predictable path for headless / download access
    persist_path = os.path.join(os.environ.get("WORKSPACE_PATH", "/tmp"), "tts_last.wav")
    try:
        import shutil
        shutil.copy2(tmp_path, persist_path)
        print(f"[TTS] WAV saved to: {persist_path}")
    except OSError:
        pass

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
                result = subprocess.run(cmd, timeout=60, capture_output=True)
                if result.returncode == 0:
                    print("[TTS] Playback started.")
                    return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        print("[TTS] No audio player available (headless). WAV ready at persist path above.")

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
