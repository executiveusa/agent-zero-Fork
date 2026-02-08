## voice_notify: Voice Notifications & TTS

Send voice notifications, make phone calls, and synthesize speech via SYNTHIA.

**Methods:**
- `call` — Initiate a voice call via OpenClaw/Twilio
- `synthesize` — Generate TTS audio from text
- `status` — Check voice service availability

### voice_notify:call
Make a phone call and speak a message.
~~~json
{
    "tool_name": "voice_notify:call",
    "tool_args": {
        "phone": "+13234842914",
        "message": "Your morning briefing is ready. You have 3 unread messages.",
        "language": "en"
    }
}
~~~

### voice_notify:synthesize
Generate audio from text (saves to tmp/voice/).
~~~json
{
    "tool_name": "voice_notify:synthesize",
    "tool_args": {
        "text": "Buenos días. Aquí está tu resumen del día.",
        "language": "es",
        "voice": "Rachel"
    }
}
~~~

### voice_notify:status
Check if voice services are available.
~~~json
{
    "tool_name": "voice_notify:status",
    "tool_args": {}
}
~~~
