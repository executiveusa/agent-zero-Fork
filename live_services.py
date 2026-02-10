"""
Agent Claw Live Services — VPS Daemon

Runs all live services as persistent background tasks on the VPS:
  1. Telegram Bot (long-polling)
  2. Twilio Webhook Server (Flask on /webhook/voice)
  3. Secret Interceptor Middleware
  4. Security Hardening Layer
  5. Heartbeat Monitor (periodic health checks)

This is the single entry point for all live services.
Deploy to VPS, run with systemd or supervisor.

Usage:
    python live_services.py              # Start all services
    python live_services.py --bot-only   # Telegram bot only
    python live_services.py --port 8080  # Custom port

Systemd unit file: See agent-claw-live.service
"""

import argparse
import json
import logging
import os
import sys
import signal
import threading
import time
from datetime import datetime, timezone

# Setup logging before any imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tmp/live_services.log", mode="a"),
    ]
)
logger = logging.getLogger("agent_claw_live")

# Ensure tmp directory exists
os.makedirs("tmp", exist_ok=True)
os.makedirs("tmp/voice", exist_ok=True)
os.makedirs("tmp/telegram", exist_ok=True)
os.makedirs("tmp/security", exist_ok=True)


# ─── Service Health Registry ────────────────────────────────

class ServiceRegistry:
    """Track health of all running services."""
    
    def __init__(self):
        self.services = {}
        self.start_time = datetime.now(timezone.utc)
    
    def register(self, name: str, status: str = "starting"):
        self.services[name] = {
            "status": status,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "errors": 0,
        }
    
    def heartbeat(self, name: str):
        if name in self.services:
            self.services[name]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            self.services[name]["status"] = "running"
    
    def error(self, name: str, msg: str):
        if name in self.services:
            self.services[name]["errors"] += 1
            self.services[name]["last_error"] = msg
    
    def get_status(self) -> dict:
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return {
            "uptime_seconds": int(uptime),
            "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "services": self.services,
        }


registry = ServiceRegistry()


# ─── Telegram Bot Service ───────────────────────────────────

def run_telegram_bot():
    """Run Telegram bot in long-polling mode (blocking)."""
    registry.register("telegram_bot")
    logger.info("Starting Telegram Bot service...")
    
    try:
        from python.helpers.telegram_bot import start_bot, get_me
        
        # Verify bot
        me = get_me()
        if not me.get("ok"):
            logger.error(f"Telegram bot auth failed: {me}")
            registry.error("telegram_bot", f"Auth failed: {me}")
            return
        
        bot_info = me["result"]
        logger.info(f"Telegram Bot: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
        registry.heartbeat("telegram_bot")
        
        # Run with heartbeat wrapper
        while True:
            try:
                from python.helpers.telegram_bot import get_updates, process_message, send_message
                from python.helpers.vault import vault_get
                import httpx
                
                token = vault_get("TELEGRAM_BOT_TOKEN")
                offset = 0
                
                while True:
                    updates = get_updates(offset=offset, timeout=30)
                    registry.heartbeat("telegram_bot")
                    
                    for update in updates:
                        offset = update["update_id"] + 1
                        message = update.get("message")
                        if not message:
                            continue
                        
                        response = process_message(message)
                        if response:
                            chat_id = message.get("chat", {}).get("id")
                            send_message(chat_id, response)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                registry.error("telegram_bot", str(e))
                logger.error(f"Telegram Bot error (retrying in 10s): {e}")
                time.sleep(10)
    
    except KeyboardInterrupt:
        logger.info("Telegram Bot stopped")
    except Exception as e:
        logger.error(f"Telegram Bot fatal error: {e}")
        registry.error("telegram_bot", f"Fatal: {e}")


# ─── Flask Webhook Server ───────────────────────────────────

def create_webhook_app(port: int = 5001):
    """Create Flask app with Twilio voice webhooks and security hardening."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        logger.warning("Flask not installed — webhook server unavailable")
        return None
    
    app = Flask(__name__)
    registry.register("webhook_server")
    
    # Apply security hardening
    try:
        from python.helpers.security_hardening import SecurityHardener
        hardener = SecurityHardener(app)
        hardener.activate()
        logger.info("Security hardening activated on webhook server")
    except Exception as e:
        logger.warning(f"Security hardening failed to activate: {e}")
    
    # Apply secret interceptor middleware
    try:
        from python.helpers.secret_interceptor import create_flask_middleware
        interceptor = create_flask_middleware(app)
        logger.info("Secret interceptor middleware activated")
    except Exception as e:
        logger.warning(f"Secret interceptor middleware failed: {e}")
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(registry.get_status())
    
    @app.route("/webhook/voice", methods=["POST"])
    def voice_webhook():
        """Handle incoming Twilio voice webhooks."""
        try:
            from python.helpers.voice_ai import handle_inbound_call
            twiml = handle_inbound_call(request.form.to_dict())
            registry.heartbeat("webhook_server")
            return twiml, 200, {"Content-Type": "text/xml"}
        except Exception as e:
            logger.error(f"Voice webhook error: {e}")
            return "<Response><Say>Sorry, an error occurred.</Say></Response>", 200, {"Content-Type": "text/xml"}
    
    @app.route("/webhook/voice/status", methods=["POST"])
    def voice_status():
        """Handle Twilio call status callbacks."""
        data = request.form.to_dict()
        logger.info(f"Call status: {data.get('CallSid', '?')} -> {data.get('CallStatus', '?')}")
        return "", 204
    
    @app.route("/webhook/telegram", methods=["POST"])
    def telegram_webhook():
        """Handle Telegram webhook updates (production mode)."""
        try:
            from python.helpers.telegram_bot import handle_webhook
            body = request.get_json(silent=True)
            if body:
                handle_webhook(body)
            return "", 200
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}")
            return "", 200
    
    @app.route("/api/vault/audit", methods=["GET"])
    def vault_audit_api():
        """Vault audit endpoint (protected)."""
        # Require auth header
        auth = request.headers.get("Authorization", "")
        from python.helpers.vault import vault_get
        expected = vault_get("AUTH_PASSWORD")
        if expected and auth != f"Bearer {expected}":
            return jsonify({"error": "Unauthorized"}), 401
        
        from python.helpers.vault import vault_audit
        return jsonify(vault_audit())
    
    @app.route("/api/security/report", methods=["GET"])
    def security_report_api():
        """Security report endpoint (protected)."""
        auth = request.headers.get("Authorization", "")
        from python.helpers.vault import vault_get
        expected = vault_get("AUTH_PASSWORD")
        if expected and auth != f"Bearer {expected}":
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            return jsonify(hardener.get_security_report())
        except Exception:
            return jsonify({"error": "Security hardener not active"}), 500
    
    return app, port


# ─── Heartbeat Monitor ──────────────────────────────────────

def run_heartbeat_monitor(interval: int = 300):
    """
    Periodic heartbeat that checks all service health.
    Runs every `interval` seconds (default 5 min).
    """
    registry.register("heartbeat_monitor")
    logger.info(f"Heartbeat monitor started (every {interval}s)")
    
    while True:
        try:
            registry.heartbeat("heartbeat_monitor")
            status = registry.get_status()
            
            # Log status
            logger.info(f"Heartbeat: {status['uptime_human']} uptime, "
                       f"{len(status['services'])} services")
            
            # Save to file
            with open("tmp/heartbeat.json", "w") as f:
                json.dump(status, f, indent=2)
            
            # Check for unhealthy services
            for name, svc in status["services"].items():
                if svc.get("errors", 0) > 10:
                    logger.warning(f"Service {name} has {svc['errors']} errors!")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            time.sleep(60)


# ─── Main Entry Point ───────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agent Claw Live Services")
    parser.add_argument("--bot-only", action="store_true", help="Run Telegram bot only")
    parser.add_argument("--webhook-only", action="store_true", help="Run webhook server only")
    parser.add_argument("--port", type=int, default=5001, help="Webhook server port")
    parser.add_argument("--heartbeat-interval", type=int, default=300, help="Heartbeat interval (seconds)")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Agent Claw Live Services — Starting")
    logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)
    
    threads = []
    
    # Start Heartbeat Monitor (always)
    heartbeat_thread = threading.Thread(
        target=run_heartbeat_monitor,
        args=(args.heartbeat_interval,),
        daemon=True,
        name="heartbeat",
    )
    heartbeat_thread.start()
    threads.append(heartbeat_thread)
    
    if args.bot_only:
        # Just run the Telegram bot (blocking)
        run_telegram_bot()
        return
    
    if args.webhook_only:
        # Just run the webhook server
        result = create_webhook_app(args.port)
        if result:
            app, port = result
            logger.info(f"Webhook server starting on port {port}")
            app.run(host="0.0.0.0", port=port, debug=False)
        return
    
    # Start all services
    
    # 1. Telegram Bot (in thread)
    bot_thread = threading.Thread(
        target=run_telegram_bot,
        daemon=True,
        name="telegram_bot",
    )
    bot_thread.start()
    threads.append(bot_thread)
    
    # 2. Webhook Server (main thread)
    result = create_webhook_app(args.port)
    if result:
        app, port = result
        logger.info(f"Starting webhook server on port {port}")
        try:
            app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    else:
        # No Flask — just run bot in main thread
        logger.info("Flask unavailable — running Telegram bot only")
        try:
            bot_thread.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")


# Graceful shutdown handler
def _signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


if __name__ == "__main__":
    main()
