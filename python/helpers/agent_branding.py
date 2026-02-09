"""
Agent Branding & Persona System

Allows deploying the same Agent Zero instance with different:
  - Display names and avatars
  - Voice personas (Twilio + ElevenLabs)
  - System prompt styles
  - Theme colors
  - Per-teammate assignments

Configuration lives in conf/agent_personas.yaml.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import YAML
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not available — agent branding will use defaults")


PERSONAS_CONFIG_PATH = "conf/agent_personas.yaml"
_personas_cache: Optional[dict] = None


def _load_config() -> dict:
    """Load personas config from YAML file."""
    global _personas_cache
    if _personas_cache is not None:
        return _personas_cache

    if not YAML_AVAILABLE:
        _personas_cache = _default_config()
        return _personas_cache

    config_path = Path(PERSONAS_CONFIG_PATH)
    if not config_path.exists():
        logger.warning(f"Personas config not found at {PERSONAS_CONFIG_PATH}")
        _personas_cache = _default_config()
        return _personas_cache

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        _personas_cache = data or _default_config()
        return _personas_cache
    except Exception as e:
        logger.error(f"Failed to load personas config: {e}")
        _personas_cache = _default_config()
        return _personas_cache


def _default_config() -> dict:
    return {
        "default_persona": "agent_claw",
        "personas": {
            "agent_claw": {
                "display_name": "Agent Claw",
                "tagline": "Executive AI Assistant",
                "avatar": "🤖",
                "avatar_image": "",
                "theme_color": "#00d4ff",
                "voice_persona": "professional",
                "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM",
                "greeting": "Hey, Agent Claw here. Ready to get things done.",
                "system_style": "You are Agent Claw, an executive AI assistant.",
            }
        },
        "team_assignments": {"default": "agent_claw"},
    }


def reload_config():
    """Force reload of personas config."""
    global _personas_cache
    _personas_cache = None
    return _load_config()


# ─── Persona Queries ──────────────────────────────────────────

def get_default_persona_name() -> str:
    """Get the default persona name."""
    config = _load_config()
    return config.get("default_persona", "agent_claw")


def get_persona(name: Optional[str] = None) -> dict:
    """
    Get a persona by name. Returns default if name is None.
    
    Returns a dict with: display_name, tagline, avatar, avatar_image,
    theme_color, voice_persona, elevenlabs_voice_id, greeting, system_style
    """
    config = _load_config()
    name = name or config.get("default_persona", "agent_claw")
    personas = config.get("personas", {})
    
    if name in personas:
        return {**personas[name], "persona_key": name}
    
    # Fallback to default
    default_name = config.get("default_persona", "agent_claw")
    if default_name in personas:
        return {**personas[default_name], "persona_key": default_name}
    
    # Ultimate fallback
    return {
        "persona_key": "agent_claw",
        "display_name": "Agent Claw",
        "tagline": "AI Assistant",
        "avatar": "🤖",
        "avatar_image": "",
        "theme_color": "#00d4ff",
        "voice_persona": "professional",
        "elevenlabs_voice_id": "",
        "greeting": "Hello, I'm your AI assistant.",
        "system_style": "You are a helpful AI assistant.",
    }


def list_personas() -> dict:
    """List all available personas (summary info only)."""
    config = _load_config()
    personas = config.get("personas", {})
    result = {}
    for key, p in personas.items():
        result[key] = {
            "display_name": p.get("display_name", key),
            "tagline": p.get("tagline", ""),
            "avatar": p.get("avatar", "🤖"),
            "theme_color": p.get("theme_color", "#00d4ff"),
        }
    return result


def get_persona_for_team_member(member_id: str) -> dict:
    """
    Get the persona assigned to a specific team member.
    Falls back to default if no assignment exists.
    """
    config = _load_config()
    assignments = config.get("team_assignments", {})
    persona_name = assignments.get(member_id, assignments.get("default", get_default_persona_name()))
    return get_persona(persona_name)


# ─── Persona Management ──────────────────────────────────────

def create_persona(
    key: str,
    display_name: str,
    tagline: str = "",
    avatar: str = "⭐",
    theme_color: str = "#00d4ff",
    voice_persona: str = "professional",
    elevenlabs_voice_id: str = "",
    greeting: str = "",
    system_style: str = "",
) -> dict:
    """
    Create or update a persona.
    Saves to the YAML config file.
    """
    config = _load_config()
    
    persona_data = {
        "display_name": display_name,
        "tagline": tagline,
        "avatar": avatar,
        "avatar_image": "",
        "theme_color": theme_color,
        "voice_persona": voice_persona,
        "elevenlabs_voice_id": elevenlabs_voice_id,
        "greeting": greeting or f"Hello, I'm {display_name}.",
        "system_style": system_style or f"You are {display_name}, a helpful AI assistant.",
    }

    if "personas" not in config:
        config["personas"] = {}
    config["personas"][key] = persona_data

    _save_config(config)
    reload_config()

    return {"success": True, "persona_key": key, "persona": persona_data}


def assign_team_member(member_id: str, persona_key: str) -> dict:
    """Assign a persona to a team member."""
    config = _load_config()
    
    # Verify persona exists
    if persona_key not in config.get("personas", {}):
        return {"error": f"Persona '{persona_key}' not found"}

    if "team_assignments" not in config:
        config["team_assignments"] = {}
    config["team_assignments"][member_id] = persona_key

    _save_config(config)
    reload_config()

    return {"success": True, "member": member_id, "persona": persona_key}


def set_default_persona(persona_key: str) -> dict:
    """Set the default persona."""
    config = _load_config()
    if persona_key not in config.get("personas", {}):
        return {"error": f"Persona '{persona_key}' not found"}

    config["default_persona"] = persona_key
    _save_config(config)
    reload_config()

    return {"success": True, "default_persona": persona_key}


def get_team_assignments() -> dict:
    """Get all team member persona assignments."""
    config = _load_config()
    return config.get("team_assignments", {"default": get_default_persona_name()})


def _save_config(config: dict):
    """Save config back to YAML."""
    if not YAML_AVAILABLE:
        logger.error("Cannot save config — PyYAML not available")
        return

    try:
        config_path = Path(PERSONAS_CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logger.error(f"Failed to save personas config: {e}")


# ─── Dashboard Data ──────────────────────────────────────────

def get_branding_data(persona_key: Optional[str] = None) -> dict:
    """
    Get full branding data for the dashboard.
    Used by the frontend to render the correct name, avatar, colors.
    """
    persona = get_persona(persona_key)
    return {
        "persona_key": persona.get("persona_key", "agent_claw"),
        "display_name": persona.get("display_name", "Agent Claw"),
        "tagline": persona.get("tagline", ""),
        "avatar": persona.get("avatar", "🤖"),
        "avatar_image": persona.get("avatar_image", ""),
        "theme_color": persona.get("theme_color", "#00d4ff"),
        "greeting": persona.get("greeting", ""),
    }
