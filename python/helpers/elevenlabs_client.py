"""
ElevenLabs TTS & Conversational AI Client

Wraps the ElevenLabs REST API for:
- Text-to-speech synthesis (eleven_multilingual_v2)
- Voice listing and management
- Conversational AI agent creation (future)

Falls back gracefully when API key is unavailable.
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Attempt to import requests; it's in requirements but guard anyway
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests package not available — ElevenLabs client disabled")


class ElevenLabsClient:
    """Async-friendly wrapper around ElevenLabs REST API."""

    BASE_URL = "https://api.elevenlabs.io/v1"
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — clear, professional
    DEFAULT_MODEL = "eleven_multilingual_v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        self._voices_cache: Optional[list] = None

        if not self.api_key:
            logger.warning("No ElevenLabs API key found. TTS will be unavailable.")

    @property
    def available(self) -> bool:
        return bool(self.api_key) and REQUESTS_AVAILABLE

    def _headers(self) -> Dict[str, str]:
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_path: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
    ) -> Optional[bytes]:
        """
        Convert text to speech audio bytes.

        Args:
            text: The text to synthesize
            voice_id: ElevenLabs voice ID (defaults to Rachel)
            model_id: Model to use (defaults to eleven_multilingual_v2)
            output_path: If provided, save audio to this file path
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice clarity/similarity (0.0-1.0)
            style: Style exaggeration (0.0-1.0)

        Returns:
            Audio bytes (mp3) or None on failure
        """
        if not self.available:
            logger.error("ElevenLabs client not available (missing key or requests)")
            return None

        voice_id = voice_id or self.DEFAULT_VOICE_ID
        model_id = model_id or self.DEFAULT_MODEL

        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
            },
        }

        try:
            # Run blocking request in executor to keep async compatibility
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=30,
                ),
            )

            if response.status_code == 200:
                audio_bytes = response.content
                if output_path:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                    logger.info(f"Audio saved to {output_path}")
                return audio_bytes
            else:
                logger.error(
                    f"ElevenLabs TTS failed [{response.status_code}]: {response.text[:200]}"
                )
                return None

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return None

    async def list_voices(self) -> list:
        """List available voices. Cached after first call."""
        if self._voices_cache is not None:
            return self._voices_cache

        if not self.available:
            return []

        url = f"{self.BASE_URL}/voices"
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=self._headers(), timeout=15),
            )
            if response.status_code == 200:
                data = response.json()
                self._voices_cache = data.get("voices", [])
                return self._voices_cache
            else:
                logger.error(f"Failed to list voices [{response.status_code}]")
                return []
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []

    async def get_voice_by_name(self, name: str) -> Optional[Dict]:
        """Find a voice by name (case-insensitive)."""
        voices = await self.list_voices()
        name_lower = name.lower()
        for voice in voices:
            if voice.get("name", "").lower() == name_lower:
                return voice
        return None

    async def check_quota(self) -> Optional[Dict]:
        """Check remaining character quota."""
        if not self.available:
            return None

        url = f"{self.BASE_URL}/user/subscription"
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=self._headers(), timeout=15),
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "character_count": data.get("character_count", 0),
                    "character_limit": data.get("character_limit", 0),
                    "remaining": data.get("character_limit", 0) - data.get("character_count", 0),
                }
            return None
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return None


# Module-level singleton
_client: Optional[ElevenLabsClient] = None


def get_elevenlabs_client(api_key: Optional[str] = None) -> ElevenLabsClient:
    """Get or create the module-level ElevenLabs client singleton."""
    global _client
    if _client is None or (api_key and api_key != _client.api_key):
        _client = ElevenLabsClient(api_key=api_key)
    return _client
