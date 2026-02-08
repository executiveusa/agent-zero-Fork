"""
Voice Command Router — Maps spoken intents to Agent Zero tool calls.

This is the central dispatch for SYNTHIA's voice-activated command system.
It parses natural language commands, matches them to registered intents,
extracts arguments, and returns the tool call JSON the agent should execute.

Architecture:
  Voice input → STT (Whisper/ElevenLabs) → text
  text → VoiceCommandRouter.match() → CommandMatch
  CommandMatch → agent dispatches the tool_name + tool_args

All commands are registered declaratively in COMMAND_REGISTRY.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class CommandCategory(Enum):
    """Command categories for grouping and access control."""
    COMMS = "communications"
    TASKS = "tasks"
    MEMORY = "memory"
    SEARCH = "search"
    SYSTEM = "system"
    MEDIA = "media"
    VOICE = "voice"
    BROWSE = "browse"
    CODE = "code"


@dataclass
class CommandDef:
    """Definition of a single voice command."""
    id: str                                      # Unique command ID
    category: CommandCategory                    # Grouping
    triggers: List[str]                          # Phrases that activate this command
    tool_name: str                               # Agent Zero tool to call
    tool_args_template: Dict[str, Any]           # Default args (placeholders use {slot})
    description: str                             # Human-readable description
    examples: List[str]                          # Example voice utterances
    slots: Dict[str, str] = field(default_factory=dict)  # Named slots to extract
    confirm: bool = False                        # Require confirmation before executing
    admin_only: bool = False                     # Restrict to admin user


@dataclass
class CommandMatch:
    """Result of matching a voice command."""
    command: CommandDef
    confidence: float                            # 0.0-1.0
    extracted_args: Dict[str, Any]               # Filled-in tool_args
    raw_input: str                               # Original utterance


# ─── COMMAND REGISTRY ───────────────────────────────────────────
# Every voice command the system understands. Add new commands here.

COMMAND_REGISTRY: List[CommandDef] = [

    # ── COMMUNICATIONS ──────────────────────────────────────────

    CommandDef(
        id="check_messages",
        category=CommandCategory.COMMS,
        triggers=["check messages", "check my messages", "any new messages",
                  "unread messages", "what's new", "message update",
                  "revisar mensajes", "hay mensajes nuevos"],
        tool_name="code_execution_tool",
        tool_args_template={
            "runtime": "python",
            "code": "# Fetch unread messages from all OpenClaw channels\nimport json, asyncio\nfrom python.tools.clawbot_messaging_bridge import MessagingBridge, Platform\nbridge = MessagingBridge()\nprint('Checking all channels for unread messages...')",
        },
        description="Check unread messages across all messaging platforms",
        examples=["Hey SYNTHIA, check my messages", "Any new messages?", "¿Hay mensajes nuevos?"],
    ),

    CommandDef(
        id="send_message",
        category=CommandCategory.COMMS,
        triggers=["send message", "send a message", "text", "message",
                  "enviar mensaje", "mandar mensaje"],
        tool_name="code_execution_tool",
        tool_args_template={
            "runtime": "python",
            "code": "# Send message via OpenClaw\nprint('Ready to send. Specify: platform, recipient, and message.')",
        },
        description="Send a message via WhatsApp, Telegram, Discord, etc.",
        examples=["Send a message to John on WhatsApp", "Text Maria on Telegram"],
        slots={"recipient": "person to message", "platform": "messaging platform", "content": "message text"},
    ),

    CommandDef(
        id="call_someone",
        category=CommandCategory.VOICE,
        triggers=["call", "phone call", "dial", "ring",
                  "llamar", "hacer llamada"],
        tool_name="voice_notify:call",
        tool_args_template={"phone": "{phone}", "message": "{message}", "language": "en"},
        description="Make a voice call via Twilio/OpenClaw",
        examples=["Call +1-323-484-2914 and say the server is down", "Llamar y decir que todo está listo"],
        slots={"phone": "phone number", "message": "what to say"},
        confirm=True,
    ),

    # ── TASKS & SCHEDULING ──────────────────────────────────────

    CommandDef(
        id="list_tasks",
        category=CommandCategory.TASKS,
        triggers=["list tasks", "show tasks", "what's scheduled", "my tasks",
                  "upcoming tasks", "pending tasks", "mostrar tareas"],
        tool_name="scheduler:list_tasks",
        tool_args_template={},
        description="List all scheduled and pending tasks",
        examples=["What tasks are pending?", "Show me my schedule", "¿Qué tareas tengo?"],
    ),

    CommandDef(
        id="create_reminder",
        category=CommandCategory.TASKS,
        triggers=["remind me", "set reminder", "set a reminder", "reminder",
                  "recuérdame", "crear recordatorio"],
        tool_name="scheduler:create_planned_task",
        tool_args_template={
            "name": "{description}",
            "system_prompt": "You are a helpful reminder assistant.",
            "prompt": "Remind the user: {description}. Notify them via voice_notify if available, otherwise use notify_user.",
            "plan": ["{datetime}"],
            "dedicated_context": True,
        },
        description="Set a reminder for a specific time",
        examples=["Remind me to call the dentist at 3pm", "Recuérdame comprar leche mañana a las 9"],
        slots={"description": "what to remember", "datetime": "when (ISO format)"},
    ),

    CommandDef(
        id="create_recurring",
        category=CommandCategory.TASKS,
        triggers=["schedule", "every day", "every hour", "every morning",
                  "recurring task", "cron", "programar tarea"],
        tool_name="scheduler:create_scheduled_task",
        tool_args_template={
            "name": "{name}",
            "system_prompt": "You are a task automation assistant.",
            "prompt": "{task_description}",
            "schedule": {"minute": "{minute}", "hour": "{hour}", "day": "*", "month": "*", "weekday": "*"},
            "dedicated_context": True,
        },
        description="Create a recurring scheduled task",
        examples=["Schedule a daily standup summary at 9am", "Run health checks every hour"],
        slots={"name": "task name", "task_description": "what to do", "minute": "cron minute", "hour": "cron hour"},
    ),

    CommandDef(
        id="run_task",
        category=CommandCategory.TASKS,
        triggers=["run task", "execute task", "trigger task", "start task",
                  "ejecutar tarea"],
        tool_name="scheduler:run_task",
        tool_args_template={"uuid": "{task_id}"},
        description="Manually run an existing task",
        examples=["Run the morning briefing", "Execute the backup task"],
        slots={"task_id": "task UUID or name"},
    ),

    CommandDef(
        id="cancel_task",
        category=CommandCategory.TASKS,
        triggers=["cancel task", "delete task", "remove task", "stop task",
                  "cancelar tarea", "eliminar tarea"],
        tool_name="scheduler:delete_task",
        tool_args_template={"uuid": "{task_id}"},
        description="Cancel/delete a scheduled task",
        examples=["Cancel the 3pm reminder", "Delete the backup task"],
        slots={"task_id": "task UUID or name"},
        confirm=True,
    ),

    # ── MEMORY ──────────────────────────────────────────────────

    CommandDef(
        id="remember",
        category=CommandCategory.MEMORY,
        triggers=["remember", "save this", "memorize", "store this",
                  "don't forget", "recuerda", "guarda esto"],
        tool_name="memory_save",
        tool_args_template={"text": "{content}"},
        description="Save information to long-term memory",
        examples=["Remember that the API key is stored in vault", "Don't forget: meeting moved to Thursday"],
        slots={"content": "what to remember"},
    ),

    CommandDef(
        id="recall",
        category=CommandCategory.MEMORY,
        triggers=["recall", "what do you know about", "search memory",
                  "do you remember", "find in memory", "¿recuerdas"],
        tool_name="memory_load",
        tool_args_template={"query": "{query}", "threshold": 0.6, "limit": 5},
        description="Search long-term memory",
        examples=["Do you remember the server IP?", "What do you know about the Venice API key?"],
        slots={"query": "what to search for"},
    ),

    CommandDef(
        id="forget",
        category=CommandCategory.MEMORY,
        triggers=["forget", "delete memory", "erase", "remove from memory",
                  "olvida", "borrar memoria"],
        tool_name="memory_forget",
        tool_args_template={"query": "{query}", "threshold": 0.75},
        description="Remove information from memory",
        examples=["Forget everything about the old API keys", "Erase memory about Project X"],
        slots={"query": "what to forget"},
        confirm=True,
    ),

    # ── SEARCH ──────────────────────────────────────────────────

    CommandDef(
        id="web_search",
        category=CommandCategory.SEARCH,
        triggers=["search", "google", "look up", "find online",
                  "buscar", "busca en internet"],
        tool_name="search_engine",
        tool_args_template={"query": "{query}"},
        description="Search the web",
        examples=["Search for the latest AI news", "Look up Python asyncio tutorials"],
        slots={"query": "search query"},
    ),

    CommandDef(
        id="private_search",
        category=CommandCategory.SEARCH,
        triggers=["private search", "venice search", "search privately",
                  "búsqueda privada"],
        tool_name="venice_mcp:search",
        tool_args_template={"query": "{query}"},
        description="Private web search via Venice AI (no tracking)",
        examples=["Private search for competitor analysis", "Venice search for crypto prices"],
        slots={"query": "search query"},
    ),

    # ── SYSTEM ──────────────────────────────────────────────────

    CommandDef(
        id="system_status",
        category=CommandCategory.SYSTEM,
        triggers=["system status", "health check", "how's everything",
                  "status report", "check systems", "estado del sistema"],
        tool_name="code_execution_tool",
        tool_args_template={
            "runtime": "python",
            "code": (
                "import subprocess, os, psutil\n"
                "print('=== SYSTEM STATUS ===')\n"
                "print(f'CPU: {psutil.cpu_percent()}%')\n"
                "print(f'RAM: {psutil.virtual_memory().percent}%')\n"
                "print(f'Disk: {psutil.disk_usage(\"/\").percent}%')\n"
                "try:\n"
                "    r = subprocess.run(['docker', 'ps', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True, timeout=10)\n"
                "    print(f'\\n=== CONTAINERS ===\\n{r.stdout or \"No containers\"}')\n"
                "except: print('Docker: unavailable')\n"
            ),
        },
        description="Check system health (CPU, RAM, Docker containers)",
        examples=["How's the system doing?", "Run a health check", "¿Cómo está el sistema?"],
    ),

    CommandDef(
        id="voice_status",
        category=CommandCategory.VOICE,
        triggers=["voice status", "check voice", "tts status",
                  "estado de voz"],
        tool_name="voice_notify:status",
        tool_args_template={},
        description="Check voice service availability (ElevenLabs, OpenClaw)",
        examples=["Is voice working?", "Check voice status"],
    ),

    CommandDef(
        id="venice_status",
        category=CommandCategory.SYSTEM,
        triggers=["venice status", "check venice", "is venice up",
                  "estado de venice"],
        tool_name="venice_mcp:status",
        tool_args_template={},
        description="Check Venice AI connectivity",
        examples=["Is Venice AI online?", "Check Venice status"],
    ),

    # ── MEDIA ───────────────────────────────────────────────────

    CommandDef(
        id="generate_image",
        category=CommandCategory.MEDIA,
        triggers=["generate image", "create image", "make a picture",
                  "draw", "image of", "generar imagen", "crear imagen"],
        tool_name="venice_mcp:image",
        tool_args_template={"prompt": "{description}", "model": "fluently-xl", "width": 1024, "height": 1024},
        description="Generate an image via Venice AI",
        examples=["Generate an image of a sunset over the ocean", "Draw a cyberpunk city"],
        slots={"description": "image description"},
    ),

    CommandDef(
        id="speak",
        category=CommandCategory.VOICE,
        triggers=["say", "speak", "read aloud", "read this",
                  "di", "lee en voz alta"],
        tool_name="voice_notify:synthesize",
        tool_args_template={"text": "{text}", "language": "en"},
        description="Synthesize speech from text",
        examples=["Say 'hello world' out loud", "Read this email aloud"],
        slots={"text": "text to speak"},
    ),

    # ── BROWSE ──────────────────────────────────────────────────

    CommandDef(
        id="open_website",
        category=CommandCategory.BROWSE,
        triggers=["open", "go to", "browse", "visit", "navigate to",
                  "abrir", "ir a"],
        tool_name="browser_agent",
        tool_args_template={"message": "Open {url} and describe what you see. End task.", "reset": "true"},
        description="Open a website in the browser",
        examples=["Open github.com", "Go to the Venice AI dashboard"],
        slots={"url": "website URL"},
    ),

    # ── CODE ────────────────────────────────────────────────────

    CommandDef(
        id="run_code",
        category=CommandCategory.CODE,
        triggers=["run code", "execute code", "run python", "run script",
                  "ejecutar código"],
        tool_name="code_execution_tool",
        tool_args_template={"runtime": "python", "code": "{code}"},
        description="Execute Python code",
        examples=["Run this Python script: print('hello')"],
        slots={"code": "code to execute"},
    ),

    CommandDef(
        id="run_terminal",
        category=CommandCategory.CODE,
        triggers=["run command", "terminal", "shell", "bash", "ejecutar comando"],
        tool_name="code_execution_tool",
        tool_args_template={"runtime": "terminal", "code": "{command}"},
        description="Execute a terminal command",
        examples=["Run 'docker ps' in the terminal", "Terminal: ls -la"],
        slots={"command": "shell command"},
    ),

    # ── PRIVATE AI ──────────────────────────────────────────────

    CommandDef(
        id="private_chat",
        category=CommandCategory.SEARCH,
        triggers=["ask venice", "private question", "off the record",
                  "pregunta privada"],
        tool_name="venice_mcp:chat",
        tool_args_template={"prompt": "{prompt}", "model": "llama-3.3-70b"},
        description="Private AI conversation via Venice (no data retention)",
        examples=["Ask Venice about market trends off the record"],
        slots={"prompt": "question to ask privately"},
    ),

    # ── META / HELP ─────────────────────────────────────────────

    CommandDef(
        id="help",
        category=CommandCategory.SYSTEM,
        triggers=["help", "what can you do", "commands", "list commands",
                  "ayuda", "qué puedes hacer"],
        tool_name="response",
        tool_args_template={},
        description="Show available voice commands",
        examples=["What can you do?", "Help", "¿Qué puedes hacer?"],
    ),

    CommandDef(
        id="briefing",
        category=CommandCategory.SYSTEM,
        triggers=["morning briefing", "daily briefing", "briefing",
                  "give me a briefing", "resumen del día"],
        tool_name="scheduler:find_task_by_name",
        tool_args_template={"name": "morning_briefing"},
        description="Run the morning briefing task",
        examples=["Give me my morning briefing", "Daily briefing please"],
    ),
]


class VoiceCommandRouter:
    """Matches voice input to registered commands."""

    def __init__(self, registry: Optional[List[CommandDef]] = None):
        self.registry = registry or COMMAND_REGISTRY
        self._build_index()

    def _build_index(self):
        """Pre-compute normalized triggers for fast matching."""
        self._trigger_map: List[tuple] = []
        for cmd in self.registry:
            for trigger in cmd.triggers:
                normalized = trigger.lower().strip()
                self._trigger_map.append((normalized, cmd))

    def match(self, utterance: str) -> Optional[CommandMatch]:
        """
        Match a voice utterance to a command.

        Uses a simple scoring system:
        1. Exact trigger match → confidence 1.0
        2. Trigger contained in utterance → confidence 0.8
        3. Word overlap scoring → confidence 0.3-0.7

        Returns the highest-confidence match, or None if no match.
        """
        utterance_lower = utterance.lower().strip()
        if not utterance_lower:
            return None

        best_match: Optional[CommandMatch] = None
        best_score = 0.0

        for trigger, cmd in self._trigger_map:
            score = 0.0

            # Exact match
            if utterance_lower == trigger:
                score = 1.0
            # Trigger is a substring of the utterance
            elif trigger in utterance_lower:
                # Score based on how much of the utterance the trigger covers
                coverage = len(trigger) / len(utterance_lower)
                score = 0.6 + (coverage * 0.4)  # 0.6-1.0
            # Word overlap
            else:
                trigger_words = set(trigger.split())
                utterance_words = set(utterance_lower.split())
                overlap = trigger_words & utterance_words
                if overlap and len(trigger_words) > 0:
                    score = (len(overlap) / len(trigger_words)) * 0.6

            if score > best_score:
                best_score = score
                best_match = CommandMatch(
                    command=cmd,
                    confidence=score,
                    extracted_args=dict(cmd.tool_args_template),
                    raw_input=utterance,
                )

        if best_match and best_score >= 0.3:
            # Try to fill slots from the utterance
            best_match.extracted_args = self._fill_slots(
                best_match.command, utterance, best_match.extracted_args
            )
            return best_match

        return None

    def _fill_slots(
        self, cmd: CommandDef, utterance: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attempt to extract slot values from the utterance.

        This is a basic extraction — the agent's LLM will handle
        complex parsing. We just pass the full utterance as context.
        """
        filled = {}
        for key, value in args.items():
            if isinstance(value, str) and "{" in value:
                # Replace slot placeholders with the raw utterance remainder
                # The agent will refine this via its own reasoning
                filled[key] = value  # Keep template — agent fills it
            elif isinstance(value, dict):
                filled[key] = {
                    k: v for k, v in value.items()
                }
            else:
                filled[key] = value
        return filled

    def get_commands_by_category(self) -> Dict[str, List[CommandDef]]:
        """Group commands by category for help display."""
        groups: Dict[str, List[CommandDef]] = {}
        for cmd in self.registry:
            cat = cmd.category.value
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(cmd)
        return groups

    def get_help_text(self) -> str:
        """Generate a human-readable help string of all commands."""
        groups = self.get_commands_by_category()
        lines = ["# SYNTHIA Voice Commands\n"]

        for category, cmds in sorted(groups.items()):
            lines.append(f"\n## {category.upper()}")
            for cmd in cmds:
                triggers = ", ".join(f'"{t}"' for t in cmd.triggers[:3])
                lines.append(f"- **{cmd.description}**")
                lines.append(f"  Say: {triggers}")
                if cmd.confirm:
                    lines.append(f"  ⚠️ Requires confirmation")
            lines.append("")

        return "\n".join(lines)

    def get_command_count(self) -> int:
        return len(self.registry)


# Module-level singleton
_router: Optional[VoiceCommandRouter] = None


def get_router() -> VoiceCommandRouter:
    """Get or create the module-level router singleton."""
    global _router
    if _router is None:
        _router = VoiceCommandRouter()
    return _router
