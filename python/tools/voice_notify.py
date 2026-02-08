"""
VoiceNotify Tool — Agent Zero Tool for voice notifications via SYNTHIA

Routes voice output through:
1. OpenClaw voice-call plugin (Twilio) — preferred for actual phone calls
2. ElevenLabs TTS — fallback for audio file generation
3. Text fallback — when no voice service is available

Follows the Tool subclass pattern from python/helpers/tool.py
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from python.helpers.tool import Tool, Response

logger = logging.getLogger(__name__)


class VoiceNotify(Tool):
    """Agent Zero tool for voice notifications and TTS synthesis."""

    async def execute(self, **kwargs) -> Response:
        if self.method == "call":
            return await self._voice_call(**kwargs)
        elif self.method == "synthesize":
            return await self._synthesize(**kwargs)
        elif self.method == "status":
            return await self._status(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{self.name}:{self.method}'",
                break_loop=False,
            )

    async def _voice_call(self, **kwargs) -> Response:
        """
        Initiate a voice call via OpenClaw → Twilio.

        Args (from self.args):
            phone: Phone number to call (E.164 format)
            message: Text to speak
            language: 'en' or 'es' (default: 'en')
        """
        phone = self.args.get("phone", "")
        message = self.args.get("message", "")
        language = self.args.get("language", "en")

        if not phone or not message:
            return Response(
                message="Error: 'phone' and 'message' are required for voice calls.",
                break_loop=False,
            )

        # Try OpenClaw voice-call plugin first
        openclaw_result = await self._try_openclaw_call(phone, message, language)
        if openclaw_result:
            return Response(
                message=f"Voice call initiated to {phone} via OpenClaw. Message: '{message[:50]}...'",
                break_loop=False,
            )

        # Fallback: generate TTS audio file
        tts_result = await self._try_elevenlabs_tts(message, language)
        if tts_result:
            return Response(
                message=f"Voice call unavailable. Generated TTS audio instead: {tts_result}",
                break_loop=False,
            )

        # Final fallback: text only
        return Response(
            message=f"Voice services unavailable. Text message for {phone}: {message}",
            break_loop=False,
        )

    async def _synthesize(self, **kwargs) -> Response:
        """
        Generate TTS audio from text.

        Args (from self.args):
            text: Text to synthesize
            voice: Voice name or ID (optional)
            language: 'en' or 'es' (default: 'en')
            output_path: Where to save the audio file (optional)
        """
        text = self.args.get("text", "")
        voice = self.args.get("voice", "")
        language = self.args.get("language", "en")
        output_path = self.args.get("output_path", "")

        if not text:
            return Response(
                message="Error: 'text' is required for synthesis.",
                break_loop=False,
            )

        result = await self._try_elevenlabs_tts(text, language, voice, output_path)
        if result:
            return Response(
                message=f"Audio synthesized successfully: {result}",
                break_loop=False,
            )

        return Response(
            message="TTS synthesis failed — ElevenLabs unavailable or error occurred.",
            break_loop=False,
        )

    async def _status(self, **kwargs) -> Response:
        """Check voice service availability and quota."""
        status_parts = []

        # Check OpenClaw
        openclaw_ok = await self._check_openclaw()
        status_parts.append(f"OpenClaw Voice: {'✓ connected' if openclaw_ok else '✗ unavailable'}")

        # Check ElevenLabs
        try:
            from python.helpers.elevenlabs_client import get_elevenlabs_client
            client = get_elevenlabs_client()
            if client.available:
                quota = await client.check_quota()
                if quota:
                    status_parts.append(
                        f"ElevenLabs: ✓ ({quota['remaining']:,} chars remaining)"
                    )
                else:
                    status_parts.append("ElevenLabs: ✓ (quota check failed)")
            else:
                status_parts.append("ElevenLabs: ✗ (no API key)")
        except Exception as e:
            status_parts.append(f"ElevenLabs: ✗ ({e})")

        return Response(
            message="Voice Service Status:\n" + "\n".join(status_parts),
            break_loop=False,
        )

    # --- Private helpers ---

    async def _try_openclaw_call(
        self, phone: str, message: str, language: str
    ) -> bool:
        """Attempt voice call via OpenClaw gateway WebSocket."""
        try:
            import websockets

            gateway_url = os.environ.get(
                "OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789"
            )
            payload = json.dumps({
                "action": "voice_call",
                "phone": phone,
                "message": message,
                "language": language,
                "voice_provider": "elevenlabs",
                "voice_model": "eleven_multilingual_v2",
            })

            async with websockets.connect(gateway_url, open_timeout=5) as ws:
                await ws.send(payload)
                resp = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(resp)
                return data.get("status") == "ok"

        except ImportError:
            logger.debug("websockets not installed — OpenClaw call unavailable")
            return False
        except Exception as e:
            logger.warning(f"OpenClaw voice call failed: {e}")
            return False

    async def _try_elevenlabs_tts(
        self,
        text: str,
        language: str = "en",
        voice: str = "",
        output_path: str = "",
    ) -> Optional[str]:
        """Generate audio via ElevenLabs TTS."""
        try:
            from python.helpers.elevenlabs_client import get_elevenlabs_client

            client = get_elevenlabs_client()
            if not client.available:
                return None

            # Select voice based on language if not specified
            voice_id = None
            if voice:
                v = await client.get_voice_by_name(voice)
                if v:
                    voice_id = v.get("voice_id")

            if not output_path:
                os.makedirs("tmp/voice", exist_ok=True)
                import time
                output_path = f"tmp/voice/tts_{int(time.time())}.mp3"

            audio = await client.text_to_speech(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
            )

            return output_path if audio else None

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            return None

    async def _check_openclaw(self) -> bool:
        """Check if OpenClaw gateway is reachable."""
        try:
            import websockets

            gateway_url = os.environ.get(
                "OPENCLAW_GATEWAY_URL", "ws://127.0.0.1:18789"
            )
            async with websockets.connect(gateway_url, open_timeout=3) as ws:
                await ws.send(json.dumps({"action": "ping"}))
                resp = await asyncio.wait_for(ws.recv(), timeout=5)
                return True
        except Exception:
            return False
