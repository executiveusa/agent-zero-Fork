"""
MCP Agent Mail Bridge — Connect MCP Agent Mail HTTP API with Agent Zero A2A

Bridges the MCP Agent Mail system (TypeScript, SQLite+FTS5, Git persistence)
with Agent Zero's internal A2A protocol, enabling:
- Cross-system message delivery (A2A ↔ MCP Agent Mail)
- Identity mapping (Agent Zero agents ↔ MCP Agent Mail identities)
- Thread persistence across both systems
- File reservation coordination

MCP Agent Mail API base: http://localhost:3001 (default)
Docs: E:\\...\\mcp_agent_mail\\README.md

Created: 2026-02-10
"""

import json
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)

# MCP Agent Mail API endpoint
AGENT_MAIL_BASE = os.environ.get("MCP_AGENT_MAIL_URL", "http://localhost:3001")


class MCPAgentMailBridge:
    """
    Bridge between MCP Agent Mail and Agent Zero's A2A system.

    MCP Agent Mail concepts:
    - Identity: An agent with a unique name (like an email address)
    - Inbox/Outbox: Per-identity message queues
    - Threads: Conversation chains with in-reply-to links
    - File Reservations: Atomic file lock system for multi-agent writes
    """

    def __init__(self, base_url: str = AGENT_MAIL_BASE):
        self.base_url = base_url.rstrip("/")
        self.timeout = 15

    def _get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        if not requests:
            return {"error": "requests library not installed"}
        try:
            resp = requests.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, data: Dict = None) -> Dict[str, Any]:
        if not requests:
            return {"error": "requests library not installed"}
        try:
            resp = requests.post(
                f"{self.base_url}{path}",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    # ── Identity Management ──────────────────────────────────

    def register_identity(self, agent_name: str, description: str = "") -> Dict[str, Any]:
        """
        Register an Agent Zero agent as an MCP Agent Mail identity.

        Args:
            agent_name: Agent Zero agent identifier (e.g., "agent_zero", "synthia")
            description: Human-readable description of the agent's role
        """
        return self._post("/identities", {
            "name": agent_name,
            "description": description or f"Agent Zero agent: {agent_name}",
        })

    def list_identities(self) -> List[Dict[str, Any]]:
        """List all registered identities in MCP Agent Mail."""
        result = self._get("/identities")
        return result.get("identities", []) if not result.get("error") else []

    # ── Message Operations ───────────────────────────────────

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Send a message from one agent to another via MCP Agent Mail.

        This creates a proper mail record with:
        - Sender/Recipient identities
        - Subject line and body
        - Thread threading (in_reply_to)
        - Git persistence (committed to repo)
        """
        payload = {
            "from": from_agent,
            "to": to_agent,
            "subject": subject,
            "body": body,
            "priority": priority,
        }
        if thread_id:
            payload["thread_id"] = thread_id
        if in_reply_to:
            payload["in_reply_to"] = in_reply_to

        return self._post("/messages", payload)

    def get_inbox(self, agent_name: str, unread_only: bool = True) -> List[Dict[str, Any]]:
        """Get inbox messages for an agent identity."""
        params = {"identity": agent_name}
        if unread_only:
            params["unread"] = "true"
        result = self._get("/inbox", params)
        return result.get("messages", []) if not result.get("error") else []

    def get_outbox(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get sent messages for an agent identity."""
        result = self._get("/outbox", {"identity": agent_name})
        return result.get("messages", []) if not result.get("error") else []

    def mark_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        return self._post(f"/messages/{message_id}/read", {})

    # ── Thread Operations ────────────────────────────────────

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get full thread conversation."""
        return self._get(f"/threads/{thread_id}")

    def list_threads(self, agent_name: str) -> List[Dict[str, Any]]:
        """List all threads involving an agent."""
        result = self._get("/threads", {"identity": agent_name})
        return result.get("threads", []) if not result.get("error") else []

    # ── File Reservations ────────────────────────────────────

    def reserve_file(self, agent_name: str, file_path: str, reason: str = "") -> Dict[str, Any]:
        """
        Reserve a file for atomic writes (prevents other agents from writing).

        Used when an agent needs exclusive access to modify a file.
        """
        return self._post("/files/reserve", {
            "identity": agent_name,
            "path": file_path,
            "reason": reason or f"Reserved by {agent_name}",
        })

    def release_file(self, agent_name: str, file_path: str) -> Dict[str, Any]:
        """Release a file reservation."""
        return self._post("/files/release", {
            "identity": agent_name,
            "path": file_path,
        })

    def list_reservations(self) -> List[Dict[str, Any]]:
        """List all active file reservations."""
        result = self._get("/files/reservations")
        return result.get("reservations", []) if not result.get("error") else []

    # ── Search ───────────────────────────────────────────────

    def search_messages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search across all messages (uses SQLite FTS5)."""
        result = self._get("/search", {"q": query, "limit": str(limit)})
        return result.get("results", []) if not result.get("error") else []

    # ── Bridge: A2A ↔ MCP Agent Mail ─────────────────────────

    def bridge_a2a_to_mail(
        self,
        a2a_message: Dict[str, Any],
        from_agent: str = "agent_zero",
    ) -> Dict[str, Any]:
        """
        Convert an A2A protocol message to MCP Agent Mail format and send it.

        Args:
            a2a_message: A2A format message with 'role', 'parts', etc.
            from_agent: Sender identity in MCP Agent Mail
        """
        # Extract text from A2A parts
        content = ""
        for part in a2a_message.get("parts", []):
            if part.get("kind") == "text":
                content += part.get("text", "")

        to_agent = a2a_message.get("metadata", {}).get("target_agent", "agent_zero")
        subject = a2a_message.get("metadata", {}).get("subject", "A2A Message")
        priority = a2a_message.get("metadata", {}).get("priority", "normal")

        return self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            subject=subject,
            body=content,
            priority=priority,
        )

    def bridge_mail_to_a2a(self, mail_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an MCP Agent Mail message to A2A protocol format.

        Returns an A2A-compatible message dict.
        """
        return {
            "role": "user",
            "parts": [
                {
                    "kind": "text",
                    "text": mail_message.get("body", ""),
                }
            ],
            "metadata": {
                "source": "mcp_agent_mail",
                "message_id": mail_message.get("id", ""),
                "from": mail_message.get("from", ""),
                "to": mail_message.get("to", ""),
                "subject": mail_message.get("subject", ""),
                "thread_id": mail_message.get("thread_id", ""),
                "timestamp": mail_message.get("timestamp", ""),
                "priority": mail_message.get("priority", "normal"),
            },
        }


# ── Convenience functions ────────────────────────────────────

_bridge_instance: Optional[MCPAgentMailBridge] = None


def get_bridge() -> MCPAgentMailBridge:
    """Get or create singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = MCPAgentMailBridge()
    return _bridge_instance


def register_core_agents():
    """Register all Agent Zero core agents in MCP Agent Mail."""
    bridge = get_bridge()
    agents = {
        "agent_zero": "CEO / Orchestrator — Agent Zero",
        "synthia": "Chief Revenue Officer — SYNTHIA",
        "security_officer": "CISO — Security Officer",
        "dev_lead": "CTO — Dev Lead",
        "growth_hacker": "CMO — Growth Hacker",
    }
    results = {}
    for name, desc in agents.items():
        results[name] = bridge.register_identity(name, desc)
    return results


def check_agent_inbox(agent_name: str = "agent_zero") -> List[Dict[str, Any]]:
    """Quick check for unread messages."""
    return get_bridge().get_inbox(agent_name, unread_only=True)


def send_meeting_summary(meeting: Dict[str, Any], from_agent: str = "agent_zero"):
    """Send meeting summary to all attendees via MCP Agent Mail."""
    bridge = get_bridge()
    results = []
    for attendee in meeting.get("attendees", []):
        if attendee != from_agent:
            result = bridge.send_message(
                from_agent=from_agent,
                to_agent=attendee,
                subject=f"Meeting Minutes: {meeting.get('topic', 'Unknown')}",
                body=json.dumps(meeting.get("decisions", []), indent=2),
                priority="normal",
            )
            results.append({attendee: result})
    return results
