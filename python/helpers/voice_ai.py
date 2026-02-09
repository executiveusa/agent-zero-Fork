"""
Voice AI Integration — Agent Claw Twilio Voice Pipeline

Handles:
  - Outbound calls (agent → customer) via Twilio
  - Inbound call webhooks (customer → agent)
  - Text-to-Speech (TTS) responses
  - Speech-to-Text (STT) transcription
  - Call recording management
  - Voice persona configuration

Uses Twilio REST API with API Key authentication (SK SID + Secret).
"""

import os
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class CallRecord:
    """Record of a voice call."""
    call_sid: str
    direction: str  # inbound, outbound
    from_number: str
    to_number: str
    status: str  # initiated, ringing, in-progress, completed, failed, busy, no-answer
    duration_s: int = 0
    transcription: str = ""
    recording_url: str = ""
    agent_response: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


CALL_LOG_DIR = "tmp/voice"
CALL_LOG_FILE = os.path.join(CALL_LOG_DIR, "call_log.json")


def _load_call_log() -> list:
    if os.path.exists(CALL_LOG_FILE):
        try:
            with open(CALL_LOG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_call_log(log: list):
    os.makedirs(CALL_LOG_DIR, exist_ok=True)
    tmp = CALL_LOG_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(log, f, indent=2)
    os.replace(tmp, CALL_LOG_FILE)


def get_twilio_client():
    """
    Create Twilio client using API Key authentication.
    
    The master.env has:
      TWILIO_ACCOUNT_SID = SK... (this is an API Key SID)
      TWILIO_SECRET = ...
    
    For API Key auth, we also need the Account SID (AC...).
    We try multiple env var patterns to find the right credentials.
    """
    try:
        from twilio.rest import Client
    except ImportError:
        raise ImportError("twilio package not installed. Run: pip install twilio")

    # Try different credential patterns
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", os.environ.get("TWILIO_SECRET", ""))
    api_key_sid = os.environ.get("TWILIO_API_KEY_SID", "")
    api_key_secret = os.environ.get("TWILIO_API_KEY_SECRET", "")

    # If TWILIO_ACCOUNT_SID starts with SK, it's actually an API Key SID
    if account_sid.startswith("SK"):
        api_key_sid = account_sid
        api_key_secret = auth_token
        # Need the real Account SID
        account_sid = os.environ.get("TWILIO_REAL_ACCOUNT_SID", "")
        
        if account_sid and account_sid.startswith("AC"):
            return Client(api_key_sid, api_key_secret, account_sid)
        else:
            # Try to use API key SID + secret directly (some Twilio SDK versions handle this)
            return Client(api_key_sid, api_key_secret)
    
    # Standard Account SID + Auth Token
    if account_sid.startswith("AC"):
        if api_key_sid:
            return Client(api_key_sid, api_key_secret, account_sid)
        return Client(account_sid, auth_token)

    raise ValueError(
        "Cannot authenticate with Twilio. Need either:\n"
        "  1. TWILIO_ACCOUNT_SID (AC...) + TWILIO_AUTH_TOKEN, or\n"
        "  2. TWILIO_API_KEY_SID (SK...) + TWILIO_API_KEY_SECRET + TWILIO_REAL_ACCOUNT_SID (AC...)"
    )


def get_twilio_phone_number() -> str:
    """Get the Twilio phone number to use as caller ID."""
    # Check env vars
    number = os.environ.get("TWILIO_PHONE_NUMBER", "")
    if number:
        return number

    # Try to list numbers from Twilio
    try:
        client = get_twilio_client()
        numbers = client.incoming_phone_numbers.list(limit=1)
        if numbers:
            return numbers[0].phone_number
    except Exception:
        pass

    return ""


def make_outbound_call(to_number: str, message: str, voice: str = "Polly.Joanna") -> Optional[CallRecord]:
    """
    Make an outbound voice call with TTS message.
    
    Args:
        to_number: Destination phone number (E.164 format, e.g., +13234842914)
        message: Text to speak via TTS
        voice: Twilio voice name (default: Polly.Joanna)
    
    Returns:
        CallRecord if successful, None if failed
    """
    try:
        client = get_twilio_client()
        from_number = get_twilio_phone_number()
        
        if not from_number:
            raise ValueError("No Twilio phone number available")

        # Build TwiML
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Say voice="{voice}">{message}</Say>'
            "<Pause length=\"2\"/>"
            f'<Say voice="{voice}">Thank you. Goodbye.</Say>'
            "</Response>"
        )

        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=twiml,
        )

        record = CallRecord(
            call_sid=call.sid,
            direction="outbound",
            from_number=from_number,
            to_number=to_number,
            status=call.status,
            agent_response=message[:500],
        )

        # Log the call
        log = _load_call_log()
        log.append(record.to_dict())
        _save_call_log(log)

        return record

    except Exception as e:
        # Log the failure
        record = CallRecord(
            call_sid="failed",
            direction="outbound",
            from_number="",
            to_number=to_number,
            status=f"failed: {str(e)}",
            agent_response=message[:500],
        )
        log = _load_call_log()
        log.append(record.to_dict())
        _save_call_log(log)
        return record


def handle_inbound_call(raw_webhook: dict) -> str:
    """
    Handle an inbound Twilio voice webhook.
    Returns TwiML response.
    """
    caller = raw_webhook.get("From", raw_webhook.get("Caller", ""))
    call_sid = raw_webhook.get("CallSid", "")

    # Log inbound call
    record = CallRecord(
        call_sid=call_sid,
        direction="inbound",
        from_number=caller,
        to_number=raw_webhook.get("To", ""),
        status="in-progress",
    )
    log = _load_call_log()
    log.append(record.to_dict())
    _save_call_log(log)

    # Return welcome TwiML with speech gathering
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        '<Say voice="Polly.Joanna">'
        "Thank you for calling Executive USA AI Agency. "
        "I'm your AI assistant. How can I help you today?"
        "</Say>"
        '<Gather input="speech" timeout="5" speechTimeout="auto" '
        'action="/webhook/voice" method="POST">'
        '<Say voice="Polly.Joanna">Go ahead, I\'m listening.</Say>'
        "</Gather>"
        '<Say voice="Polly.Joanna">'
        "I didn't hear anything. Please call back if you need assistance. Goodbye."
        "</Say>"
        "</Response>"
    )


def get_call_log(limit: int = 20) -> list:
    """Get recent call log."""
    log = _load_call_log()
    log.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return log[:limit]


# ─── Voice Persona Configuration ─────────────────────────────

VOICE_PERSONAS = {
    "professional": {
        "voice": "Polly.Joanna",
        "language": "en-US",
        "style": "professional, warm, confident",
        "greeting": "Thank you for calling Executive USA AI Agency.",
    },
    "friendly": {
        "voice": "Polly.Salli",
        "language": "en-US",
        "style": "casual, friendly, upbeat",
        "greeting": "Hey there! Welcome to Executive USA.",
    },
    "british": {
        "voice": "Polly.Amy",
        "language": "en-GB",
        "style": "polished, articulate, sophisticated",
        "greeting": "Good day. You've reached Executive USA AI Agency.",
    },
}


def get_voice_persona(name: str = "professional") -> dict:
    """Get voice persona configuration."""
    return VOICE_PERSONAS.get(name, VOICE_PERSONAS["professional"])
