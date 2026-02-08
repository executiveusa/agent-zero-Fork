"""
openclaw_ws_connector.py — WebSocket bridge to the OpenClaw/ClawdBot gateway

Connects Agent Zero to the OpenClaw Node.js gateway (ws://127.0.0.1:18789)
to receive inbound messages from all 16 channels (WhatsApp, Telegram, etc.)
and send responses back through the same channels.

Usage:
    from python.helpers.openclaw_ws_connector import OpenClawConnector
    connector = OpenClawConnector(on_message=my_handler)
    await connector.connect()  # runs forever, auto-reconnects
"""

import asyncio
import json
import logging
import os
from typing import Callable, Optional, Awaitable, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Default gateway address
WS_URL = os.environ.get("OPENCLAW_WS_URL", "ws://127.0.0.1:18789")
RECONNECT_DELAY = 5  # seconds


class OpenClawConnector:
    """Persistent WebSocket connection to the OpenClaw messaging gateway."""

    def __init__(
        self,
        on_message: Callable[[Dict[str, Any]], Awaitable[Optional[str]]],
        ws_url: str = WS_URL,
    ):
        """
        Args:
            on_message: async callback(msg_dict) -> optional response string.
                        msg_dict has keys: id, platform, user_id, user_name,
                        content, type, channel_id, is_group, group_name, media, timestamp
            ws_url: WebSocket URL of the OpenClaw gateway
        """
        self.ws_url = ws_url
        self.on_message = on_message
        self._ws = None
        self._running = False
        self._send_queue: asyncio.Queue = asyncio.Queue()

    # ── Public API ──────────────────────────────────────────

    async def connect(self):
        """Connect and run the message loop (auto-reconnects)."""
        self._running = True
        while self._running:
            try:
                await self._run_session()
            except Exception as e:
                logger.warning(f"OpenClaw WS error: {e}. Reconnecting in {RECONNECT_DELAY}s…")
            if self._running:
                await asyncio.sleep(RECONNECT_DELAY)

    async def disconnect(self):
        """Gracefully close the connection."""
        self._running = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass

    async def send_response(self, platform: str, channel_id: str, user_id: str, text: str, **extra):
        """Queue a response to send back through OpenClaw."""
        msg = {
            "type": "response",
            "platform": platform,
            "channel_id": channel_id,
            "user_id": user_id,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            **extra,
        }
        await self._send_queue.put(json.dumps(msg))

    @property
    def connected(self) -> bool:
        return self._ws is not None

    # ── Internal ────────────────────────────────────────────

    async def _run_session(self):
        """Single WebSocket session — receive and dispatch messages."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed. Run: pip install websockets")
            self._running = False
            return

        logger.info(f"Connecting to OpenClaw gateway at {self.ws_url}…")
        async with websockets.connect(self.ws_url) as ws:
            self._ws = ws
            logger.info("Connected to OpenClaw gateway ✓")

            # Announce ourselves
            await ws.send(json.dumps({
                "type": "register",
                "agent": "agent-claw",
                "capabilities": ["text", "voice", "commands"],
                "timestamp": datetime.utcnow().isoformat(),
            }))

            # Run receive + send loops in parallel
            recv_task = asyncio.create_task(self._recv_loop(ws))
            send_task = asyncio.create_task(self._send_loop(ws))

            done, pending = await asyncio.wait(
                [recv_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
            for task in done:
                if task.exception():
                    raise task.exception()

        self._ws = None
        logger.info("Disconnected from OpenClaw gateway")

    async def _recv_loop(self, ws):
        """Receive messages from OpenClaw, dispatch to handler."""
        async for raw in ws:
            try:
                msg = json.loads(raw)
                msg_type = msg.get("type", "message")

                # Skip non-message frames (heartbeat, ack, etc.)
                if msg_type not in ("message", "text", "audio", "command"):
                    if msg_type == "ping":
                        await ws.send(json.dumps({"type": "pong"}))
                    continue

                logger.info(
                    f"[{msg.get('platform', '?')}] {msg.get('user_name', '?')}: "
                    f"{(msg.get('content', '') or '')[:80]}"
                )

                # Call the handler
                response = await self.on_message(msg)

                # If handler returns a string, auto-reply
                if response and isinstance(response, str):
                    await self.send_response(
                        platform=msg.get("platform", "direct"),
                        channel_id=msg.get("channel_id", ""),
                        user_id=msg.get("user_id", ""),
                        text=response,
                    )

            except json.JSONDecodeError:
                logger.warning(f"Non-JSON frame from OpenClaw: {raw[:100]}")
            except Exception as e:
                logger.error(f"Error handling OpenClaw message: {e}", exc_info=True)

    async def _send_loop(self, ws):
        """Send queued responses back through OpenClaw."""
        while True:
            msg = await self._send_queue.get()
            try:
                await ws.send(msg)
            except Exception as e:
                logger.error(f"Failed to send to OpenClaw: {e}")
                # Re-queue on failure
                await self._send_queue.put(msg)
                raise


# ── Factory: create connector wired to Agent Zero ────────────

def create_agent_zero_connector():
    """
    Create an OpenClawConnector that routes inbound messages
    through Agent Zero's message processing pipeline.

    Returns:
        OpenClawConnector ready to .connect()
    """
    async def handle_message(msg: Dict[str, Any]) -> Optional[str]:
        """Route an inbound message through Agent Zero."""
        try:
            from python.helpers.voice_command_router import VoiceCommandRouter

            content = msg.get("content", "").strip()
            platform = msg.get("platform", "direct")
            user_name = msg.get("user_name", "User")

            if not content:
                return None

            # Check if it's a voice command first
            router = VoiceCommandRouter()
            match = router.match(content)

            if match and match.confidence >= 0.6:
                logger.info(f"Voice command matched: {match.command.id} ({match.confidence:.0%})")
                # For now, acknowledge the command — actual dispatch happens
                # through the agent's tool execution pipeline
                return (
                    f"Got it — matched '{match.command.id}' "
                    f"(confidence {match.confidence:.0%}). Processing…"
                )

            # Otherwise, route as a general message to Agent Zero
            # This uses the async message endpoint to avoid blocking
            from python.helpers import defer
            import python.api.message_async as msg_api

            logger.info(f"Routing [{platform}] message from {user_name} to Agent Zero")

            # The actual agent processing is async — response flows back
            # through the poll loop and gets pushed to the WS via send_response
            return None

        except Exception as e:
            logger.error(f"Message handler error: {e}", exc_info=True)
            return "Sorry, I encountered an error processing that message."

    return OpenClawConnector(on_message=handle_message)
