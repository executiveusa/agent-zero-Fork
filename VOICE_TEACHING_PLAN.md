# Voice Agent Teaching Plan
## How to Train Your AI Voice Agent

---

### Overview

Your voice agent uses a **three-layer training system**:

1. **Persona Configuration** — Who the agent is (name, voice, personality)
2. **System Prompts** — How the agent thinks & responds
3. **Knowledge Base** — What the agent knows about your business

---

## Layer 1: Persona Configuration

**File:** `conf/agent_personas.yaml`

Each persona defines the agent's identity for phone calls:

```yaml
personas:
  your_agent:
    display_name: "Your Agent Name"
    voice_persona: "professional"          # or friendly, british
    elevenlabs_voice_id: "your_voice_id"   # Custom ElevenLabs voice
    greeting: "Hey! This is [Name]. How can I help?"
    system_style: |
      You are [Name], a [role] for [company].
      You specialize in [domains].
      Your tone is [warm/direct/casual/formal].
```

**To change identity:** Edit `conf/agent_personas.yaml` or use the Dashboard → Branding API.

**To create a custom ElevenLabs voice:**
1. Go to https://elevenlabs.io → Voices → Add Generative Voice
2. Upload 1-5 minutes of clear audio (you or someone on your team)
3. Copy the Voice ID
4. Set it as `elevenlabs_voice_id` in your persona config

---

## Layer 2: System Prompts (How the Agent Thinks)

The voice agent's behavior comes from `system_style` in the persona config plus the conversation persona in `python/helpers/voice_conversation.py`.

### Key Conversation Personas

| Persona | Role | Best For |
|---------|------|----------|
| `professional` | Agent Claw — Executive Assistant | Client calls, project updates |
| `project_manager` | Manager Claw — PM | Standups, status check-ins |
| `friendly` | Synthia — Creative Partner | Brainstorming, casual check-ins |

### Teaching the Agent New Behaviors

**Method 1: Edit the system prompt directly**

In `python/helpers/voice_conversation.py`, find `CONVERSATION_PERSONAS` and modify the `system_prompt`:

```python
"professional": {
    "system_prompt": (
        "You are Agent Claw. "
        "When asked about pricing, always say: 'I can give you a ballpark, "
        "but let me have [boss name] confirm the exact numbers.' "
        "When asked about project timelines, check the knowledge base first. "
        "Never commit to deadlines without confirming with the team."
    ),
}
```

**Method 2: Add knowledge via the Knowledge Ingestion system**

Upload documents about your business, products, FAQs:
```
POST /api/knowledge_ingest
{
  "action": "ingest_file",
  "path": "docs/company-faq.md"
}
```

The agent will reference this knowledge during voice calls.

---

## Layer 3: Conversation Patterns

### Teaching Common Scenarios

Add these to the system prompt to handle specific situations:

**Client Intake Call:**
```
When someone calls for the first time:
1. Greet them warmly and ask their name
2. Ask what they need help with
3. Summarize their request back to confirm
4. Tell them you'll have the team follow up within 24 hours
5. Get their preferred contact method
```

**Daily Standup Call:**
```
For daily check-ins:
1. Ask what they accomplished yesterday
2. Ask what they're working on today
3. Ask if they have any blockers
4. Summarize action items
5. Confirm next check-in time
```

**Emergency Escalation:**
```
If someone says "urgent" or "emergency":
1. Acknowledge urgency immediately
2. Ask for a one-sentence summary
3. Confirm you're escalating to the team lead
4. Send a notification via the dashboard
5. Stay on the line until acknowledged
```

---

## Step-by-Step: Training Your First Voice Agent

### Step 1: Test with default persona
```
POST /api/voice_conversation
{
  "action": "call_me",
  "phone": "+13234842914",
  "persona": "professional"
}
```

### Step 2: Customize the greeting
Edit `conf/agent_personas.yaml` → change the `greeting` field.

### Step 3: Add business knowledge
Place your documents in `knowledge/` and ingest them:
```
POST /api/knowledge_ingest
{"action": "ingest_file", "path": "knowledge/our-services.md"}
```

### Step 4: Refine the system prompt
After test calls, adjust the `system_prompt` based on what worked and what didn't. Common refinements:
- "Keep responses under 2 sentences"
- "Always ask one follow-up question"
- "When you don't know, say 'Let me check on that'"
- "End with a clear action item"

### Step 5: Create team-specific personas
```
POST /api/branding
{
  "action": "create",
  "key": "sarah_assistant",
  "display_name": "Sarah's Assistant",
  "voice_persona": "friendly",
  "greeting": "Hey Sarah! Quick check-in. How's the project going?"
}
```

Assign to team member:
```
POST /api/branding
{
  "action": "assign",
  "member": "sarah@company.com",
  "persona": "sarah_assistant"
}
```

---

## Voice Quality Tips

| Setting | Range | Effect |
|---------|-------|--------|
| Stability | 0.0-1.0 | Higher = more consistent, lower = more expressive |
| Similarity | 0.0-1.0 | Higher = closer to original voice |
| Style | 0.0-1.0 | Higher = more dramatic delivery |

**Recommended settings for phone calls:**
- Stability: 0.50 (natural variation)
- Similarity: 0.75 (clearly recognizable)
- Style: 0.10 (subtle, not distracting)

---

## Conversation Flow Architecture

```
User calls → Twilio → Webhook → Agent Zero
                                     │
                                     ├─ STT (Twilio built-in)
                                     ├─ Response Generation (LLM)
                                     ├─ TTS (ElevenLabs or Twilio Polly)
                                     └─ TwiML → Twilio → User hears response
                                     
Each "turn" loops back through the webhook until:
  - User says goodbye
  - 20 turns reached
  - Call timeout (no speech detected)
```

---

## Quick Reference: Dashboard Voice Controls

| Button | What it does |
|--------|-------------|
| 📲 Call Me Now | Agent calls your saved phone number |
| 📞 Make a Call | Call any number with a message |
| 🔊 Test Voice | Preview ElevenLabs voice |
| 💾 Save Config | Save voice settings (ID, stability, similarity) |
| 🔄 Refresh | Load latest call history |

---

## Next Steps

1. **Set up your Twilio phone number** — Forward inbound calls to your agent webhook
2. **Create a custom ElevenLabs voice** — Clone your voice or choose a premium voice
3. **Write your FAQ document** — The more context, the better the agent handles calls
4. **Run 5 test calls** — Iterate on the system prompt after each one
5. **Assign personas to teammates** — Each person gets their personalized AI assistant
