"""
VeniceMCP Tool — Privacy-first AI via Venice.ai

Provides Agent Zero tool access to Venice AI's capabilities:
- Private LLM chat (no data retention)
- Web search & scraping
- Image generation
- Text-to-speech (kokoro)

Uses OpenAI-compatible API at https://api.venice.ai/api/v1
Follows the Tool subclass pattern from python/helpers/tool.py
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from python.helpers.tool import Tool, Response

logger = logging.getLogger(__name__)

VENICE_API_BASE = "https://api.venice.ai/api/v1"


class VeniceMCP(Tool):
    """Agent Zero tool for Venice AI private operations."""

    async def execute(self, **kwargs) -> Response:
        if self.method == "chat":
            return await self._private_chat(**kwargs)
        elif self.method == "search":
            return await self._web_search(**kwargs)
        elif self.method == "image":
            return await self._generate_image(**kwargs)
        elif self.method == "tts":
            return await self._text_to_speech(**kwargs)
        elif self.method == "status":
            return await self._status(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{self.name}:{self.method}'",
                break_loop=False,
            )

    def _get_api_key(self) -> str:
        """Get Venice API key from env."""
        return os.environ.get("VENICE_API_KEY", "")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

    async def _api_request(
        self, method: str, endpoint: str, payload: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make an async API request to Venice."""
        try:
            import requests as req

            url = f"{VENICE_API_BASE}/{endpoint}"
            headers = self._get_headers()

            loop = asyncio.get_event_loop()
            if method.upper() == "GET":
                resp = await loop.run_in_executor(
                    None,
                    lambda: req.get(url, headers=headers, timeout=30),
                )
            else:
                resp = await loop.run_in_executor(
                    None,
                    lambda: req.post(url, json=payload, headers=headers, timeout=60),
                )

            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Venice API [{resp.status_code}]: {resp.text[:200]}")
                return None

        except ImportError:
            logger.error("requests package not available")
            return None
        except Exception as e:
            logger.error(f"Venice API error: {e}")
            return None

    async def _private_chat(self, **kwargs) -> Response:
        """
        Private LLM chat via Venice (no data retention).

        Args (from self.args):
            prompt: The user message
            model: Venice model name (default: llama-3.3-70b)
            system: Optional system prompt
        """
        prompt = self.args.get("prompt", "")
        model = self.args.get("model", "llama-3.3-70b")
        system = self.args.get("system", "")

        if not prompt:
            return Response(message="Error: 'prompt' is required.", break_loop=False)

        if not self._get_api_key():
            return Response(
                message="Error: VENICE_API_KEY not set. Cannot use Venice AI.",
                break_loop=False,
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "venice_parameters": {"include_venice_system_prompt": False},
        }

        result = await self._api_request("POST", "chat/completions", payload)
        if result:
            content = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "No response")
            )
            return Response(message=content, break_loop=False)

        return Response(
            message="Venice AI chat request failed. Check API key and connectivity.",
            break_loop=False,
        )

    async def _web_search(self, **kwargs) -> Response:
        """
        Private web search via Venice.

        Args (from self.args):
            query: Search query
            max_results: Maximum results (default: 5)
        """
        query = self.args.get("query", "")
        if not query:
            return Response(message="Error: 'query' is required.", break_loop=False)

        if not self._get_api_key():
            return Response(
                message="Error: VENICE_API_KEY not set.",
                break_loop=False,
            )

        # Venice web search goes through chat completions with web search enabled
        payload = {
            "model": "llama-3.3-70b",
            "messages": [
                {"role": "user", "content": f"Search the web for: {query}"}
            ],
            "venice_parameters": {
                "include_venice_system_prompt": False,
                "enable_web_search": "always",
            },
        }

        result = await self._api_request("POST", "chat/completions", payload)
        if result:
            content = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "No results")
            )
            return Response(
                message=f"Venice Web Search Results for '{query}':\n\n{content}",
                break_loop=False,
            )

        return Response(message="Venice web search failed.", break_loop=False)

    async def _generate_image(self, **kwargs) -> Response:
        """
        Generate image via Venice AI.

        Args (from self.args):
            prompt: Image description
            model: Image model (default: fluently-xl)
            width: Image width (default: 1024)
            height: Image height (default: 1024)
        """
        prompt = self.args.get("prompt", "")
        model = self.args.get("model", "fluently-xl")
        width = int(self.args.get("width", "1024"))
        height = int(self.args.get("height", "1024"))

        if not prompt:
            return Response(message="Error: 'prompt' is required.", break_loop=False)

        if not self._get_api_key():
            return Response(
                message="Error: VENICE_API_KEY not set.",
                break_loop=False,
            )

        payload = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": 1,
        }

        result = await self._api_request("POST", "images/generations", payload)
        if result and result.get("data"):
            image_url = result["data"][0].get("url", "")
            return Response(
                message=f"Image generated: {image_url}",
                break_loop=False,
            )

        return Response(message="Venice image generation failed.", break_loop=False)

    async def _text_to_speech(self, **kwargs) -> Response:
        """
        Text-to-speech via Venice (kokoro model).

        Args (from self.args):
            text: Text to synthesize
            voice: Voice preset (default: af_heart)
        """
        text = self.args.get("text", "")
        voice = self.args.get("voice", "af_heart")

        if not text:
            return Response(message="Error: 'text' is required.", break_loop=False)

        if not self._get_api_key():
            return Response(
                message="Error: VENICE_API_KEY not set.",
                break_loop=False,
            )

        payload = {
            "model": "tts-kokoro",
            "input": text,
            "voice": voice,
        }

        try:
            import requests as req

            url = f"{VENICE_API_BASE}/audio/speech"
            headers = self._get_headers()
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: req.post(url, json=payload, headers=headers, timeout=30),
            )

            if resp.status_code == 200:
                os.makedirs("tmp/voice", exist_ok=True)
                import time
                path = f"tmp/voice/venice_tts_{int(time.time())}.mp3"
                with open(path, "wb") as f:
                    f.write(resp.content)
                return Response(
                    message=f"TTS audio generated: {path}",
                    break_loop=False,
                )
            else:
                return Response(
                    message=f"Venice TTS failed [{resp.status_code}]: {resp.text[:200]}",
                    break_loop=False,
                )
        except Exception as e:
            return Response(
                message=f"Venice TTS error: {e}",
                break_loop=False,
            )

    async def _status(self, **kwargs) -> Response:
        """Check Venice AI connectivity and available models."""
        key = self._get_api_key()
        if not key:
            return Response(
                message="Venice AI Status: ✗ (VENICE_API_KEY not set)",
                break_loop=False,
            )

        result = await self._api_request("GET", "models")
        if result:
            models = result.get("data", [])
            model_names = [m.get("id", "?") for m in models[:10]]
            return Response(
                message=(
                    f"Venice AI Status: ✓ connected\n"
                    f"Available models ({len(models)} total): "
                    + ", ".join(model_names)
                ),
                break_loop=False,
            )

        return Response(
            message="Venice AI Status: ✗ (API request failed)",
            break_loop=False,
        )
