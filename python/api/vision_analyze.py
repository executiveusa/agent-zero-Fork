"""
Vision Analyze API — /vision_analyze endpoint

Accepts image uploads and optional text prompt. Sends the image to a
vision-capable model (e.g., GPT-4o via OpenRouter) and returns the
analysis result. Also stores the image in workspace for agent reference.
"""

import base64
import json
import os
import traceback
from datetime import datetime

from flask import Request, Response
from werkzeug.utils import secure_filename

from python.helpers.api import ApiHandler
from python.helpers import files, settings
from python.helpers.print_style import PrintStyle


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class VisionAnalyze(ApiHandler):
    """Analyze an uploaded image using a vision-capable LLM."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # ── Accept both multipart and base64 JSON ────────
            image_b64 = None
            mime_type = "image/png"
            prompt = "Describe what you see in this image in detail."
            context_id = ""

            if request.content_type and request.content_type.startswith("multipart/form-data"):
                prompt = request.form.get("prompt", prompt)
                context_id = request.form.get("context", "")
                img_file = request.files.get("image")
                if not img_file or not img_file.filename:
                    return {"error": "No image file provided"}
                if not _allowed_file(img_file.filename):
                    return {"error": f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"}

                # Read and encode
                raw = img_file.read()
                if len(raw) > MAX_FILE_SIZE:
                    return {"error": "Image exceeds 20 MB limit"}
                image_b64 = base64.b64encode(raw).decode("utf-8")
                mime_type = img_file.content_type or "image/png"

                # Save to workspace for agent reference
                upload_dir = files.get_abs_path("tmp/vision")
                os.makedirs(upload_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = secure_filename(img_file.filename)
                save_path = os.path.join(upload_dir, f"{ts}_{safe_name}")
                with open(save_path, "wb") as f:
                    f.write(raw)
            else:
                # JSON with base64
                image_b64 = input.get("image_base64", "")
                mime_type = input.get("mime_type", "image/png")
                prompt = input.get("prompt", prompt)
                context_id = input.get("context", "")
                if not image_b64:
                    return {"error": "No image_base64 provided"}

            # ── Call vision model via OpenRouter ─────────────
            set = settings.get_settings()
            api_key = (
                os.environ.get("OPENROUTER_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or set.get("chat_api_key", "")
            )
            if not api_key:
                return {"error": "No API key configured for vision model. Set OPENROUTER_API_KEY or OPENAI_API_KEY."}

            # Determine provider URL
            base_url = set.get("chat_api_url", "https://openrouter.ai/api/v1")
            model = set.get("chat_model_vision", "") or "openai/gpt-4o"

            import httpx

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if "openrouter" in base_url:
                headers["HTTP-Referer"] = "https://agentclaw.ai"
                headers["X-Title"] = "Agent Claw Vision"

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_b64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 2048,
            }

            async with httpx.AsyncClient(timeout=60) as client:
                url = f"{base_url.rstrip('/')}/chat/completions"
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            analysis = data["choices"][0]["message"]["content"]

            # ── Optionally feed result into agent context ────
            if context_id:
                try:
                    ctx = self.use_context(context_id, create_if_not_exists=False)
                    ctx.log.log(
                        type="info",
                        heading="Vision Analysis",
                        content=f"**Prompt:** {prompt}\n\n**Result:**\n{analysis}",
                    )
                except Exception:
                    pass  # Non-critical

            return {
                "success": True,
                "analysis": analysis,
                "model": model,
                "prompt": prompt,
            }

        except Exception as e:
            PrintStyle.error(f"Vision analyze error: {e}")
            return {"error": str(e), "trace": traceback.format_exc()}
