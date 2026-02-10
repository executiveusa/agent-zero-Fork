"""
Agent Meeting Tool — Convene, Run & Record Agent Meetings

Allows Agent Zero to call structured meetings with sub-agents,
producing minutes that sync to Notion and chat.md.

Methods:
  - agent_meeting:convene      — Start a new meeting with specified agents
  - agent_meeting:discuss      — Add a discussion round on a topic
  - agent_meeting:decide       — Record a decision with owner and beads task
  - agent_meeting:minutes      — Generate and store meeting minutes
  - agent_meeting:history      — List past meetings

Created: 2026-02-10
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle

# ── In-memory meeting state ──────────────────────────────────

_active_meetings: Dict[str, dict] = {}


def _meeting_dir() -> str:
    d = os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "meetings")
    os.makedirs(d, exist_ok=True)
    return d


def _save_meeting(meeting: dict):
    """Persist meeting to disk."""
    path = os.path.join(_meeting_dir(), f"{meeting['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meeting, f, indent=2, default=str)


def _load_meeting(meeting_id: str) -> Optional[dict]:
    path = os.path.join(_meeting_dir(), f"{meeting_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _active_meetings.get(meeting_id)


# ── Core agent roster (from agents.md) ───────────────────────

CORE_AGENTS = {
    "agent_zero": {
        "name": "Agent Zero",
        "role": "CEO / Orchestrator",
        "profile": "default",
        "tags": ["OPENING", "STRATEGY", "DECISION"],
    },
    "synthia": {
        "name": "SYNTHIA",
        "role": "Chief Revenue Officer",
        "profile": "researcher",
        "tags": ["REVENUE", "PIPELINE", "PRICING"],
    },
    "security_officer": {
        "name": "Security Officer",
        "role": "CISO",
        "profile": "hacker",
        "tags": ["SECURITY", "VAULT", "THREATS"],
    },
    "dev_lead": {
        "name": "Dev Lead",
        "role": "CTO",
        "profile": "developer",
        "tags": ["ENGINEERING", "DEPLOYMENT", "ARCHITECTURE"],
    },
    "growth_hacker": {
        "name": "Growth Hacker",
        "role": "CMO",
        "profile": "researcher",
        "tags": ["GROWTH", "CONTENT", "MARKETING"],
    },
}


# ── Tool implementation ──────────────────────────────────────

class AgentMeetingTool(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "convene"

        if method == "convene":
            return await self._convene(**kwargs)
        elif method == "discuss":
            return await self._discuss(**kwargs)
        elif method == "decide":
            return await self._decide(**kwargs)
        elif method == "minutes":
            return await self._minutes(**kwargs)
        elif method == "history":
            return await self._history(**kwargs)
        else:
            return Response(
                message=f"Unknown method 'agent_meeting:{method}'. Use: convene, discuss, decide, minutes, history",
                break_loop=False,
            )

    # ── convene ──────────────────────────────────────────────

    async def _convene(self, **kwargs) -> Response:
        meeting_type = self.args.get("type", "daily_standup")
        topic = self.args.get("topic", "General standup")
        attendees = self.args.get("attendees", list(CORE_AGENTS.keys()))
        urgency = self.args.get("urgency", "normal")

        if isinstance(attendees, str):
            attendees = [a.strip() for a in attendees.split(",")]

        meeting_id = f"mtg_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        meeting = {
            "id": meeting_id,
            "type": meeting_type,
            "topic": topic,
            "attendees": attendees,
            "urgency": urgency,
            "chair": "agent_zero",
            "status": "in_progress",
            "created_at": now.isoformat(),
            "transcript": [],
            "decisions": [],
            "action_items": [],
        }

        _active_meetings[meeting_id] = meeting
        _save_meeting(meeting)

        # Add opening remark from Agent Zero
        opening = {
            "agent": "Agent Zero",
            "timestamp": now.isoformat(),
            "tag": "OPENING",
            "content": f"Meeting convened: {meeting_type} — {topic}. "
                       f"Attendees: {', '.join(attendees)}. Urgency: {urgency}.",
        }
        meeting["transcript"].append(opening)
        _save_meeting(meeting)

        attendee_names = [CORE_AGENTS.get(a, {"name": a})["name"] for a in attendees]

        return Response(
            message=(
                f"Meeting convened!\n"
                f"  ID: {meeting_id}\n"
                f"  Type: {meeting_type}\n"
                f"  Topic: {topic}\n"
                f"  Attendees: {', '.join(attendee_names)}\n"
                f"  Urgency: {urgency}\n\n"
                f"Use agent_meeting:discuss to add discussion rounds.\n"
                f"Use agent_meeting:decide to record decisions.\n"
                f"Use agent_meeting:minutes to finalize and store."
            ),
            break_loop=False,
        )

    # ── discuss ──────────────────────────────────────────────

    async def _discuss(self, **kwargs) -> Response:
        meeting_id = self.args.get("meeting_id", "")
        agent_key = self.args.get("agent", "agent_zero")
        topic_tag = self.args.get("tag", "DISCUSSION")
        content = self.args.get("content", "")
        action = self.args.get("action", "")

        if not meeting_id:
            # Use most recent active meeting
            if _active_meetings:
                meeting_id = list(_active_meetings.keys())[-1]
            else:
                return Response(message="No active meeting. Use agent_meeting:convene first.", break_loop=False)

        meeting = _active_meetings.get(meeting_id) or _load_meeting(meeting_id)
        if not meeting:
            return Response(message=f"Meeting not found: {meeting_id}", break_loop=False)

        agent_info = CORE_AGENTS.get(agent_key, {"name": agent_key})
        now = datetime.now(timezone.utc)

        entry = {
            "agent": agent_info.get("name", agent_key),
            "timestamp": now.isoformat(),
            "tag": topic_tag.upper(),
            "content": content,
        }
        if action:
            entry["action"] = action

        meeting["transcript"].append(entry)
        _active_meetings[meeting_id] = meeting
        _save_meeting(meeting)

        resp = f"[{entry['agent']}] [{topic_tag}] {content[:100]}..."
        if action:
            resp += f"\nAction: {action}"

        return Response(message=resp, break_loop=False)

    # ── decide ───────────────────────────────────────────────

    async def _decide(self, **kwargs) -> Response:
        meeting_id = self.args.get("meeting_id", "")
        decision = self.args.get("decision", "")
        owner = self.args.get("owner", "agent_zero")
        beads_id = self.args.get("beads_id", "TBD")
        due_date = self.args.get("due_date", "")

        if not meeting_id and _active_meetings:
            meeting_id = list(_active_meetings.keys())[-1]

        meeting = _active_meetings.get(meeting_id) or _load_meeting(meeting_id)
        if not meeting:
            return Response(message=f"Meeting not found: {meeting_id}", break_loop=False)

        item = {
            "decision": decision,
            "owner": owner,
            "beads_id": beads_id,
            "due_date": due_date,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        meeting["decisions"].append(item)
        meeting["action_items"].append({
            "action": decision,
            "owner": CORE_AGENTS.get(owner, {"name": owner})["name"],
            "due": due_date,
            "beads_id": beads_id,
            "status": "pending",
        })

        _active_meetings[meeting_id] = meeting
        _save_meeting(meeting)

        return Response(
            message=f"Decision recorded: {decision}\n  Owner: {owner}\n  Beads: {beads_id}\n  Due: {due_date or 'TBD'}",
            break_loop=False,
        )

    # ── minutes ──────────────────────────────────────────────

    async def _minutes(self, **kwargs) -> Response:
        meeting_id = self.args.get("meeting_id", "")

        if not meeting_id and _active_meetings:
            meeting_id = list(_active_meetings.keys())[-1]

        meeting = _active_meetings.get(meeting_id) or _load_meeting(meeting_id)
        if not meeting:
            return Response(message="No meeting to finalize.", break_loop=False)

        meeting["status"] = "completed"
        meeting["completed_at"] = datetime.now(timezone.utc).isoformat()
        _save_meeting(meeting)

        # Build markdown minutes
        md = self._build_minutes_markdown(meeting)

        # Append to chat.md
        try:
            chat_md_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "knowledge", "custom", "main", "chat.md"
            )
            if os.path.exists(chat_md_path):
                with open(chat_md_path, "r", encoding="utf-8") as f:
                    existing = f.read()

                marker = "<!-- agent_meeting.py auto-appends here -->"
                if marker in existing:
                    existing = existing.replace(marker, marker + "\n\n" + md)
                else:
                    existing += "\n\n" + md

                with open(chat_md_path, "w", encoding="utf-8") as f:
                    f.write(existing)
        except Exception as e:
            PrintStyle.error(f"Failed to update chat.md: {e}")

        # Try syncing to Notion
        notion_result = await self._sync_to_notion(meeting)

        # Clean up active state
        _active_meetings.pop(meeting_id, None)

        summary = (
            f"Meeting minutes finalized: {meeting_id}\n"
            f"  Type: {meeting['type']}\n"
            f"  Decisions: {len(meeting['decisions'])}\n"
            f"  Action Items: {len(meeting['action_items'])}\n"
            f"  Saved to: chat.md\n"
            f"  Notion sync: {notion_result}\n\n"
            f"Minutes:\n{md[:1500]}"
        )

        return Response(message=summary, break_loop=False)

    # ── history ──────────────────────────────────────────────

    async def _history(self, **kwargs) -> Response:
        limit = int(self.args.get("limit", 10))
        meeting_dir = _meeting_dir()

        meetings = []
        if os.path.exists(meeting_dir):
            for fname in sorted(os.listdir(meeting_dir), reverse=True)[:limit]:
                if fname.endswith(".json"):
                    path = os.path.join(meeting_dir, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    meetings.append({
                        "id": data.get("id"),
                        "type": data.get("type"),
                        "topic": data.get("topic"),
                        "status": data.get("status"),
                        "created_at": data.get("created_at"),
                        "decisions": len(data.get("decisions", [])),
                    })

        if not meetings:
            return Response(message="No meeting history found.", break_loop=False)

        lines = [f"  {m['id']}: [{m['type']}] {m['topic']} ({m['status']}) — {m['decisions']} decisions"
                 for m in meetings]
        return Response(message="Meeting History:\n" + "\n".join(lines), break_loop=False)

    # ── Helper: build markdown ───────────────────────────────

    def _build_minutes_markdown(self, meeting: dict) -> str:
        lines = []
        lines.append(f"### {meeting['type'].upper().replace('_', ' ')}: {meeting['topic']}")
        lines.append(f"**Date**: {meeting.get('created_at', 'Unknown')}")
        lines.append(f"**Chair**: Agent Zero")
        attendee_names = [CORE_AGENTS.get(a, {"name": a})["name"] for a in meeting.get("attendees", [])]
        lines.append(f"**Attendees**: {', '.join(attendee_names)}")
        lines.append(f"**Meeting ID**: {meeting['id']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("#### Transcript")
        lines.append("")

        for entry in meeting.get("transcript", []):
            ts = entry.get("timestamp", "")[:16]
            lines.append(f"[{entry['agent']}] [{ts}] [{entry.get('tag', '')}]")
            lines.append(entry.get("content", ""))
            if entry.get("action"):
                lines.append(f"Action: {entry['action']}")
            lines.append("")

        if meeting.get("decisions"):
            lines.append("---")
            lines.append("")
            lines.append("#### Decisions")
            for d in meeting["decisions"]:
                lines.append(f"- [ ] {d['decision']} — Owner: {d['owner']} — Beads: {d.get('beads_id', 'TBD')}")
            lines.append("")

        if meeting.get("action_items"):
            lines.append("#### Action Items")
            lines.append("| # | Action | Owner | Due | Beads ID | Status |")
            lines.append("|---|--------|-------|-----|----------|--------|")
            for i, item in enumerate(meeting["action_items"], 1):
                lines.append(
                    f"| {i} | {item['action'][:50]} | {item['owner']} | "
                    f"{item.get('due', 'TBD')} | {item.get('beads_id', 'TBD')} | {item['status']} |"
                )
            lines.append("")

        return "\n".join(lines)

    # ── Helper: sync to Notion ───────────────────────────────

    async def _sync_to_notion(self, meeting: dict) -> str:
        """Try to create a page in Notion Meeting DB."""
        try:
            from python.tools.notion_integration import NotionIntegration
            notion = NotionIntegration()
            if not notion.api_key:
                return "skipped (no API key)"

            # We'll use the meeting DB if env provides it
            db_id = os.environ.get("NOTION_MEETING_DB_ID", "")
            if not db_id:
                return "skipped (no NOTION_MEETING_DB_ID)"

            result = notion.sync_project_to_notion(
                database_id=db_id,
                project_name=f"[{meeting['type']}] {meeting['topic']}",
                project_description=self._build_minutes_markdown(meeting)[:500],
                status=meeting.get("status", "completed"),
                tasks=[d["decision"] for d in meeting.get("decisions", [])],
            )
            return f"synced (page_id: {result.get('page_id', 'unknown')})" if result.get("success") else f"failed: {result.get('error')}"
        except Exception as e:
            return f"error: {e}"
