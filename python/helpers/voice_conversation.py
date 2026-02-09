"""
Voice Conversation Engine — Bidirectional Phone Conversations

This module bridges Twilio (phone infra) with ElevenLabs (voice synthesis)
and the Agent Zero reasoning loop to enable real two-way phone conversations.

Architecture:
  1. Agent initiates call via Twilio → plays ElevenLabs-generated greeting
  2. User speaks → Twilio STT captures text
  3. Text routed to Agent Zero for response generation
  4. Response synthesized via ElevenLabs → streamed back via TwiML <Play>
  5. Loop continues until either party hangs up

Also supports:
  - Inbound calls with conversational loop
  - Configurable personas (voice, style, knowledge domain)
  - Call context persistence (agent remembers conversation)
  - Auto-transcription logging
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Conversation State ──────────────────────────────────────

@dataclass
class ConversationTurn:
    """Single turn in a voice conversation."""
    role: str  # "user" or "agent"
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audio_url: str = ""
    duration_ms: int = 0

@dataclass
class VoiceConversation:
    """Full state of an active or completed voice conversation."""
    conversation_id: str
    call_sid: str = ""
    direction: str = "outbound"
    phone_number: str = ""
    persona: str = "professional"
    status: str = "pending"  # pending, active, completed, failed
    turns: List[Dict] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str = ""
    summary: str = ""

    def add_turn(self, role: str, text: str, audio_url: str = ""):
        self.turns.append(asdict(ConversationTurn(
            role=role, text=text, audio_url=audio_url
        )))

    def to_dict(self) -> dict:
        return asdict(self)


CONV_DIR = "tmp/voice/conversations"


def _ensure_conv_dir():
    os.makedirs(CONV_DIR, exist_ok=True)


def save_conversation(conv: VoiceConversation):
    _ensure_conv_dir()
    path = os.path.join(CONV_DIR, f"{conv.conversation_id}.json")
    with open(path, "w") as f:
        json.dump(conv.to_dict(), f, indent=2)


def load_conversation(conversation_id: str) -> Optional[VoiceConversation]:
    path = os.path.join(CONV_DIR, f"{conversation_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        conv = VoiceConversation(
            conversation_id=data["conversation_id"],
            call_sid=data.get("call_sid", ""),
            direction=data.get("direction", "outbound"),
            phone_number=data.get("phone_number", ""),
            persona=data.get("persona", "professional"),
            status=data.get("status", "completed"),
            turns=data.get("turns", []),
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
            summary=data.get("summary", ""),
        )
        return conv
    except Exception as e:
        logger.error(f"Failed to load conversation {conversation_id}: {e}")
        return None


def list_conversations(limit: int = 20) -> list:
    _ensure_conv_dir()
    files = sorted(Path(CONV_DIR).glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    result = []
    for f in files[:limit]:
        try:
            with open(f) as fh:
                data = json.load(fh)
                result.append({
                    "conversation_id": data.get("conversation_id"),
                    "direction": data.get("direction"),
                    "phone_number": data.get("phone_number"),
                    "persona": data.get("persona"),
                    "status": data.get("status"),
                    "turns": len(data.get("turns", [])),
                    "started_at": data.get("started_at"),
                    "summary": data.get("summary", ""),
                })
        except Exception:
            pass
    return result


# ─── ElevenLabs Voice Synthesis for Calls ─────────────────────

AUDIO_DIR = "tmp/voice/audio"


def _ensure_audio_dir():
    os.makedirs(AUDIO_DIR, exist_ok=True)


async def synthesize_voice_response(
    text: str,
    voice_id: Optional[str] = None,
    stability: float = 0.5,
    similarity: float = 0.75,
) -> Optional[str]:
    """
    Synthesize text to speech via ElevenLabs and save to a temp file.
    Returns the file path of the generated audio, or None on failure.
    """
    try:
        from python.helpers.elevenlabs_client import get_elevenlabs_client
        client = get_elevenlabs_client()
        if not client.available:
            logger.warning("ElevenLabs not available, falling back to Twilio TTS")
            return None

        _ensure_audio_dir()
        filename = f"resp_{uuid.uuid4().hex[:12]}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        audio_bytes = await client.text_to_speech(
            text=text,
            voice_id=voice_id,
            output_path=filepath,
            stability=stability,
            similarity_boost=similarity,
        )

        if audio_bytes:
            return filepath
        return None

    except Exception as e:
        logger.error(f"Voice synthesis failed: {e}")
        return None


# ─── Conversation Personas ────────────────────────────────────

CONVERSATION_PERSONAS = {
    "professional": {
        "name": "Agent Claw",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "twilio_voice": "Polly.Joanna",
        "stability": 0.5,
        "similarity": 0.75,
        "system_prompt": (
            "You are Agent Claw, an AI executive assistant for Executive USA AI Agency. "
            "You are speaking on the phone. Keep responses concise, warm, and professional. "
            "You handle project management, scheduling, team coordination, and strategic planning. "
            "Address the caller by name when known. Ask clarifying questions when needed. "
            "End each response naturally as if in a real phone conversation."
        ),
        "greeting": (
            "Hey, it's Agent Claw calling from Executive USA. "
            "I wanted to check in with you. How's everything going?"
        ),
        "inbound_greeting": (
            "Hey! Thanks for calling Executive USA AI Agency. "
            "This is Agent Claw, your AI assistant. How can I help you today?"
        ),
    },
    "project_manager": {
        "name": "Manager Claw",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "twilio_voice": "Polly.Joanna",
        "stability": 0.55,
        "similarity": 0.80,
        "system_prompt": (
            "You are Manager Claw, the AI project manager for Executive USA. "
            "You are conducting a phone check-in. Focus on: project status updates, "
            "blockers, deadlines, and action items. Be structured but friendly. "
            "Summarize what you hear and confirm next steps before ending the call."
        ),
        "greeting": (
            "Hi, this is Manager Claw. I'm doing our scheduled check-in. "
            "Can you give me a quick status update on what you're working on?"
        ),
        "inbound_greeting": (
            "Manager Claw here. I'm ready for your project update. "
            "What would you like to discuss?"
        ),
    },
    "friendly": {
        "name": "Synthia",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (or custom)
        "twilio_voice": "Polly.Salli",
        "stability": 0.45,
        "similarity": 0.70,
        "system_prompt": (
            "You are Synthia, the friendly AI from Executive USA. "
            "You're calling to have a casual but productive conversation. "
            "Be warm, personable, and supportive. Use conversational language. "
            "Help with whatever the caller needs — brainstorming, problem-solving, or just talking through ideas."
        ),
        "greeting": (
            "Hey! It's Synthia. Just wanted to touch base and see how things are going. "
            "What's on your mind?"
        ),
        "inbound_greeting": (
            "Hey there! It's Synthia. So glad you called. What's up?"
        ),
    },
}


def get_conversation_persona(name: str = "professional") -> dict:
    return CONVERSATION_PERSONAS.get(name, CONVERSATION_PERSONAS["professional"])


def list_conversation_personas() -> dict:
    return {k: {"name": v["name"], "voice_id": v["voice_id"]} for k, v in CONVERSATION_PERSONAS.items()}


# ─── Agent Response Generation ────────────────────────────────

def generate_agent_response(
    user_message: str,
    conversation: VoiceConversation,
    persona: dict,
) -> str:
    """
    Generate an agent response for the voice conversation.
    
    Uses the conversation history and persona system prompt to generate
    a contextual response. Falls back to a simple response if the 
    main LLM is unavailable.
    """
    # Build conversation history for context
    history = []
    for turn in conversation.turns[-10:]:  # Last 10 turns for context window
        role = "assistant" if turn.get("role") == "agent" else "user"
        history.append({"role": role, "content": turn.get("text", "")})

    # Try to use the agent's LLM
    try:
        from python.helpers.llm_router import route_and_call
        
        messages = [
            {"role": "system", "content": persona.get("system_prompt", "You are a helpful assistant.")},
            *history,
            {"role": "user", "content": user_message},
        ]
        
        response = route_and_call(
            messages=messages,
            max_tokens=200,  # Keep phone responses concise
            temperature=0.7,
        )
        
        if response:
            return response.strip()
    except Exception as e:
        logger.warning(f"LLM response generation failed, using fallback: {e}")

    # Fallback: simple pattern-based responses
    return _fallback_response(user_message, persona)


def _fallback_response(user_message: str, persona: dict) -> str:
    """Generate a simple fallback response when LLM is unavailable."""
    msg_lower = user_message.lower()
    name = persona.get("name", "Agent Claw")

    if any(word in msg_lower for word in ["hello", "hi", "hey"]):
        return f"Hey! {name} here. Good to hear from you. What can I help with?"

    if any(word in msg_lower for word in ["status", "update", "progress"]):
        return (
            "I've noted your update. I'll add that to our project tracker "
            "and make sure the team is aligned. Anything else?"
        )

    if any(word in msg_lower for word in ["help", "need", "problem", "issue"]):
        return (
            "I hear you. Let me take note of that and we'll get it sorted. "
            "Can you give me a bit more detail so I can prioritize it correctly?"
        )

    if any(word in msg_lower for word in ["bye", "goodbye", "later", "thanks"]):
        return (
            "Sounds good! I'll follow up on everything we discussed. "
            "Don't hesitate to call back if you need anything. Talk soon!"
        )

    if any(word in msg_lower for word in ["meeting", "schedule", "calendar"]):
        return (
            "Got it. I'll coordinate with the team and send out calendar invites. "
            "Any specific time preferences?"
        )

    return (
        "Understood. I've made a note of that. "
        "Is there anything specific you'd like me to action on this?"
    )


# ─── Outbound Conversational Call ─────────────────────────────

def start_outbound_conversation(
    to_number: str,
    persona_name: str = "professional",
    initial_message: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Initiate an outbound conversational call.
    
    This sets up a Twilio call that uses webhook callbacks to enable
    a multi-turn conversation with ElevenLabs voice.
    
    Args:
        to_number: Phone number to call (E.164)
        persona_name: Persona to use for the call
        initial_message: Optional custom greeting
        base_url: Base URL for webhooks (e.g., https://yourdomain.com)
    
    Returns:
        Dict with conversation_id, call_sid, status
    """
    try:
        from python.helpers.voice_ai import get_twilio_client, get_twilio_phone_number

        client = get_twilio_client()
        from_number = get_twilio_phone_number()

        if not from_number:
            return {"error": "No Twilio phone number configured"}

        persona = get_conversation_persona(persona_name)
        conv_id = uuid.uuid4().hex[:16]
        greeting = initial_message or persona.get("greeting", "Hello, this is Agent Claw.")

        # Create conversation record
        conv = VoiceConversation(
            conversation_id=conv_id,
            direction="outbound",
            phone_number=to_number,
            persona=persona_name,
            status="pending",
        )
        conv.add_turn("agent", greeting)
        save_conversation(conv)

        # Determine webhook URL
        if not base_url:
            base_url = os.environ.get("AGENT_BASE_URL", "http://localhost:50001")

        # Build initial TwiML with greeting and first gather
        voice = persona.get("twilio_voice", "Polly.Joanna")
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Say voice="{voice}">{greeting}</Say>'
            f'<Gather input="speech" timeout="6" speechTimeout="auto" '
            f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn=1" method="POST">'
            f'<Say voice="{voice}">Go ahead, I\'m listening.</Say>'
            "</Gather>"
            f'<Say voice="{voice}">I didn\'t hear anything. Let me try again.</Say>'
            f'<Redirect>{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn=1&amp;retry=1</Redirect>'
            "</Response>"
        )

        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=twiml,
        )

        conv.call_sid = call.sid
        conv.status = "active"
        save_conversation(conv)

        return {
            "success": True,
            "conversation_id": conv_id,
            "call_sid": call.sid,
            "persona": persona_name,
            "status": "active",
        }

    except Exception as e:
        logger.error(f"Failed to start outbound conversation: {e}")
        return {"error": str(e)}


def handle_conversation_webhook(
    webhook_data: dict,
    conv_id: str,
    turn: int = 0,
    retry: int = 0,
) -> str:
    """
    Handle Twilio webhook for ongoing conversation.
    Called when user finishes speaking — processes their speech,
    generates a response, and returns TwiML for next turn.
    
    Returns:
        TwiML response string
    """
    conv = load_conversation(conv_id)
    if not conv:
        return _error_twiml("Sorry, I lost track of our conversation. Please call back.")

    persona = get_conversation_persona(conv.persona)
    voice = persona.get("twilio_voice", "Polly.Joanna")
    base_url = os.environ.get("AGENT_BASE_URL", "http://localhost:50001")

    # Get user's speech
    user_speech = webhook_data.get("SpeechResult", "")
    
    if not user_speech and retry < 2:
        # No speech detected, ask again
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Say voice="{voice}">I didn\'t catch that. Could you repeat?</Say>'
            f'<Gather input="speech" timeout="8" speechTimeout="auto" '
            f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn={turn}" method="POST">'
            f'<Say voice="{voice}">Go ahead.</Say>'
            "</Gather>"
            f'<Say voice="{voice}">Still can\'t hear you. I\'ll follow up later. Goodbye!</Say>'
            "</Response>"
        )

    if not user_speech:
        # Max retries hit
        conv.status = "completed"
        conv.ended_at = datetime.now(timezone.utc).isoformat()
        conv.summary = "Call ended — no speech detected after retries."
        save_conversation(conv)
        return _goodbye_twiml(voice, "It seems like we're having connection issues. I'll follow up with you later. Take care!")

    # Record user's turn
    conv.add_turn("user", user_speech)

    # Check for goodbye signals
    if _is_goodbye(user_speech):
        agent_response = "Sounds great! I'll follow up on everything we discussed. Talk to you soon. Bye!"
        conv.add_turn("agent", agent_response)
        conv.status = "completed"
        conv.ended_at = datetime.now(timezone.utc).isoformat()
        conv.summary = _generate_call_summary(conv)
        save_conversation(conv)
        return _goodbye_twiml(voice, agent_response)

    # Generate agent response
    agent_response = generate_agent_response(user_speech, conv, persona)
    conv.add_turn("agent", agent_response)
    next_turn = turn + 1
    save_conversation(conv)

    # Build TwiML with response and next gather
    # Limit conversation to 20 turns to prevent infinite loops
    if next_turn >= 20:
        farewell = "We've had a great conversation! Let me wrap up and send you a summary. Talk soon!"
        conv.add_turn("agent", farewell)
        conv.status = "completed"
        conv.ended_at = datetime.now(timezone.utc).isoformat()
        conv.summary = _generate_call_summary(conv)
        save_conversation(conv)
        return _goodbye_twiml(voice, farewell)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{voice}">{_escape_xml(agent_response)}</Say>'
        f'<Gather input="speech" timeout="6" speechTimeout="auto" '
        f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn={next_turn}" method="POST">'
        "</Gather>"
        f'<Say voice="{voice}">Are you still there?</Say>'
        f'<Gather input="speech" timeout="5" speechTimeout="auto" '
        f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn={next_turn}" method="POST">'
        "</Gather>"
        f'<Say voice="{voice}">Alright, I\'ll follow up later. Take care!</Say>'
        "</Response>"
    )


def handle_inbound_conversation(webhook_data: dict) -> str:
    """
    Handle an inbound call as a conversation.
    Creates a new conversation and returns TwiML with greeting + gather.
    """
    caller = webhook_data.get("From", webhook_data.get("Caller", "unknown"))
    call_sid = webhook_data.get("CallSid", "")

    # Determine persona — default professional for inbound
    persona_name = "professional"
    persona = get_conversation_persona(persona_name)
    voice = persona.get("twilio_voice", "Polly.Joanna")
    base_url = os.environ.get("AGENT_BASE_URL", "http://localhost:50001")

    conv_id = uuid.uuid4().hex[:16]
    greeting = persona.get("inbound_greeting", "Thank you for calling. How can I help?")

    conv = VoiceConversation(
        conversation_id=conv_id,
        call_sid=call_sid,
        direction="inbound",
        phone_number=caller,
        persona=persona_name,
        status="active",
    )
    conv.add_turn("agent", greeting)
    save_conversation(conv)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{voice}">{greeting}</Say>'
        f'<Gather input="speech" timeout="6" speechTimeout="auto" '
        f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn=1" method="POST">'
        "</Gather>"
        f'<Say voice="{voice}">Go ahead, I\'m listening.</Say>'
        f'<Gather input="speech" timeout="8" speechTimeout="auto" '
        f'action="{base_url}/api/voice_conversation?conv_id={conv_id}&amp;turn=1" method="POST">'
        "</Gather>"
        f'<Say voice="{voice}">I didn\'t hear anything. Please call back when you\'re ready. Goodbye!</Say>'
        "</Response>"
    )


# ─── Helper Functions ─────────────────────────────────────────

def _is_goodbye(text: str) -> bool:
    """Detect if the user is saying goodbye."""
    goodbye_signals = [
        "goodbye", "bye bye", "bye", "talk later", "gotta go",
        "take care", "see you", "that's all", "that's it",
        "nothing else", "i'm good", "all good", "all set",
        "hang up", "end call",
    ]
    text_lower = text.lower().strip()
    return any(signal in text_lower for signal in goodbye_signals)


def _generate_call_summary(conv: VoiceConversation) -> str:
    """Generate a brief summary of the conversation."""
    user_messages = [t["text"] for t in conv.turns if t.get("role") == "user"]
    if not user_messages:
        return "No user messages captured."
    
    topics = ", ".join(user_messages[:5])
    return f"Call with {conv.phone_number} ({conv.direction}). " \
           f"{len(conv.turns)} turns. Topics discussed: {topics[:200]}"


def _escape_xml(text: str) -> str:
    """Escape text for safe inclusion in TwiML XML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _error_twiml(message: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="Polly.Joanna">{_escape_xml(message)}</Say>'
        "</Response>"
    )


def _goodbye_twiml(voice: str, message: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{voice}">{_escape_xml(message)}</Say>'
        "<Hangup/>"
        "</Response>"
    )
