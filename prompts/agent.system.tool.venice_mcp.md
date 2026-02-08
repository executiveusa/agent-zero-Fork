## venice_mcp: Venice AI Private Operations

Access Venice.ai for privacy-first AI operations — no data retention, no logging.

**Methods:**
- `chat` — Private LLM chat (no data stored)
- `search` — Private web search
- `image` — Generate images
- `tts` — Text-to-speech via kokoro
- `status` — Check Venice connectivity

### venice_mcp:chat
Private LLM conversation through Venice AI.
~~~json
{
    "tool_name": "venice_mcp:chat",
    "tool_args": {
        "prompt": "Summarize the latest crypto market trends",
        "model": "llama-3.3-70b",
        "system": "You are a financial analyst"
    }
}
~~~

### venice_mcp:search
Private web search (no tracking).
~~~json
{
    "tool_name": "venice_mcp:search",
    "tool_args": {
        "query": "latest AI agent frameworks 2026"
    }
}
~~~

### venice_mcp:image
Generate images via Venice AI.
~~~json
{
    "tool_name": "venice_mcp:image",
    "tool_args": {
        "prompt": "A cyberpunk city at night, neon lights, rain",
        "model": "fluently-xl",
        "width": 1024,
        "height": 1024
    }
}
~~~

### venice_mcp:tts
Text-to-speech using Venice's kokoro model.
~~~json
{
    "tool_name": "venice_mcp:tts",
    "tool_args": {
        "text": "Welcome to Agent Claw. How can I help you today?",
        "voice": "af_heart"
    }
}
~~~

### venice_mcp:status
Check Venice AI service connectivity.
~~~json
{
    "tool_name": "venice_mcp:status",
    "tool_args": {}
}
~~~
