"""
Lead Generation & CRM Pipeline — Agent Claw Agency Module

Tracks leads from initial contact through qualification, proposal,
and close. Integrates with the customer-service agent for automated
follow-up and the TKGM memory system for relationship tracking.

Lead Lifecycle:
  New → Contacted → Qualified → Proposal → Negotiation → Closed Won/Lost

Scoring Model:
  - Budget fit (0-25 pts)
  - Timeline urgency (0-25 pts)
  - Service match (0-25 pts)
  - Engagement level (0-25 pts)
  Total: 0-100, where >70 = HOT, 40-70 = WARM, <40 = COLD
"""

import os
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional

# Atomic persistence
LEADS_DIR = "tmp/leads"
LEADS_FILE = os.path.join(LEADS_DIR, "leads.json")


@dataclass
class Lead:
    """A potential client lead."""
    lead_id: str
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    source_channel: str = ""  # whatsapp, telegram, discord, web_chat, voice, referral
    status: str = "new"  # new, contacted, qualified, proposal, negotiation, closed_won, closed_lost
    score: int = 0  # 0-100
    temperature: str = "cold"  # cold, warm, hot
    services_interested: list = field(default_factory=list)
    budget_range: str = ""  # e.g., "$500-1500/mo"
    timeline: str = ""  # e.g., "immediate", "1-3 months", "exploring"
    notes: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_contact: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    next_followup: Optional[str] = None
    assigned_agent: str = "customer-service"
    conversation_ids: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Lead":
        return Lead(**{k: v for k, v in data.items() if k in Lead.__dataclass_fields__})


def _load_leads() -> list:
    """Load leads from disk."""
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r") as f:
                data = json.load(f)
                return [Lead.from_dict(d) for d in data]
        except Exception:
            pass
    return []


def _save_leads(leads: list):
    """Save leads atomically."""
    os.makedirs(LEADS_DIR, exist_ok=True)
    tmp_path = LEADS_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump([l.to_dict() for l in leads], f, indent=2)
    os.replace(tmp_path, LEADS_FILE)


def score_lead(lead: Lead) -> int:
    """
    Score a lead based on qualification criteria.
    Returns 0-100 score.
    """
    score = 0

    # Budget fit (0-25)
    budget = lead.budget_range.lower()
    if any(x in budget for x in ["$1500", "$2000", "$5000", "enterprise", "custom"]):
        score += 25
    elif any(x in budget for x in ["$500", "$1000", "$497", "$1497"]):
        score += 15
    elif budget:
        score += 5

    # Timeline urgency (0-25)
    timeline = lead.timeline.lower()
    if any(x in timeline for x in ["immediate", "asap", "now", "this week"]):
        score += 25
    elif any(x in timeline for x in ["this month", "1 month", "soon"]):
        score += 15
    elif any(x in timeline for x in ["1-3 month", "quarter"]):
        score += 10
    elif timeline:
        score += 5

    # Service match (0-25)
    if len(lead.services_interested) >= 3:
        score += 25
    elif len(lead.services_interested) >= 2:
        score += 15
    elif len(lead.services_interested) >= 1:
        score += 10

    # Engagement level (0-25)
    if len(lead.notes) >= 5:
        score += 25
    elif len(lead.notes) >= 3:
        score += 15
    elif len(lead.notes) >= 1:
        score += 10

    # Bonus: has email AND phone
    if lead.email and lead.phone:
        score = min(100, score + 5)

    return score


def classify_temperature(score: int) -> str:
    """Classify lead temperature from score."""
    if score >= 70:
        return "hot"
    elif score >= 40:
        return "warm"
    return "cold"


def create_lead(name: str, channel: str = "", email: str = "", phone: str = "",
                company: str = "", notes: str = "") -> Lead:
    """Create a new lead and persist."""
    leads = _load_leads()
    lead_id = f"lead_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(leads)}"
    
    lead = Lead(
        lead_id=lead_id,
        name=name,
        email=email,
        phone=phone,
        company=company,
        source_channel=channel,
    )
    if notes:
        lead.notes.append({"text": notes, "timestamp": datetime.now(timezone.utc).isoformat()})

    lead.score = score_lead(lead)
    lead.temperature = classify_temperature(lead.score)

    leads.append(lead)
    _save_leads(leads)
    return lead


def update_lead(lead_id: str, **kwargs) -> Optional[Lead]:
    """Update a lead's fields and re-score."""
    leads = _load_leads()
    for i, lead in enumerate(leads):
        if lead.lead_id == lead_id:
            for key, value in kwargs.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            lead.score = score_lead(lead)
            lead.temperature = classify_temperature(lead.score)
            lead.last_contact = datetime.now(timezone.utc).isoformat()
            leads[i] = lead
            _save_leads(leads)
            return lead
    return None


def add_note(lead_id: str, note_text: str) -> Optional[Lead]:
    """Add a note to a lead."""
    leads = _load_leads()
    for i, lead in enumerate(leads):
        if lead.lead_id == lead_id:
            lead.notes.append({
                "text": note_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            lead.score = score_lead(lead)
            lead.temperature = classify_temperature(lead.score)
            leads[i] = lead
            _save_leads(leads)
            return lead
    return None


def get_leads(status: str = "", temperature: str = "", limit: int = 50) -> list:
    """Get leads filtered by status and/or temperature."""
    leads = _load_leads()
    if status:
        leads = [l for l in leads if l.status == status]
    if temperature:
        leads = [l for l in leads if l.temperature == temperature]
    # Sort by score descending
    leads.sort(key=lambda l: l.score, reverse=True)
    return leads[:limit]


def get_followups_due() -> list:
    """Get leads with followups due today or overdue."""
    leads = _load_leads()
    now = datetime.now(timezone.utc).isoformat()
    return [
        l for l in leads
        if l.next_followup and l.next_followup <= now
        and l.status not in ("closed_won", "closed_lost")
    ]


def get_pipeline_summary() -> dict:
    """Get pipeline summary statistics."""
    leads = _load_leads()
    summary = {
        "total": len(leads),
        "by_status": {},
        "by_temperature": {"hot": 0, "warm": 0, "cold": 0},
        "by_channel": {},
        "avg_score": 0,
        "followups_due": len(get_followups_due()),
    }
    
    total_score = 0
    for lead in leads:
        summary["by_status"][lead.status] = summary["by_status"].get(lead.status, 0) + 1
        summary["by_temperature"][lead.temperature] = summary["by_temperature"].get(lead.temperature, 0) + 1
        summary["by_channel"][lead.source_channel] = summary["by_channel"].get(lead.source_channel, 0) + 1
        total_score += lead.score

    if leads:
        summary["avg_score"] = round(total_score / len(leads))

    return summary
