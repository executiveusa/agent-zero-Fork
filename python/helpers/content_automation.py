"""
Content Automation Pipeline — Agent Claw Agency Module

Automates content creation workflows for the AI agency:
  - Blog posts / articles
  - Social media posts
  - Email sequences
  - Landing page copy
  - Client reports
  - Case studies

Each content type has a template + generation pipeline that
leverages the swarm orchestrator for parallel production.
"""

import os
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

CONTENT_DIR = "tmp/content"


@dataclass
class ContentPiece:
    """A generated content piece."""
    content_id: str
    content_type: str  # blog, social, email, landing_page, report, case_study
    title: str
    body: str = ""
    status: str = "draft"  # draft, review, approved, published, archived
    target_channel: str = ""  # blog, twitter, linkedin, email, website
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None
    word_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ContentPiece":
        return ContentPiece(**{k: v for k, v in data.items() if k in ContentPiece.__dataclass_fields__})


def _load_content() -> list:
    content_file = os.path.join(CONTENT_DIR, "content.json")
    if os.path.exists(content_file):
        try:
            with open(content_file, "r") as f:
                return [ContentPiece.from_dict(d) for d in json.load(f)]
        except Exception:
            pass
    return []


def _save_content(pieces: list):
    os.makedirs(CONTENT_DIR, exist_ok=True)
    content_file = os.path.join(CONTENT_DIR, "content.json")
    tmp = content_file + ".tmp"
    with open(tmp, "w") as f:
        json.dump([p.to_dict() for p in pieces], f, indent=2)
    os.replace(tmp, content_file)


# ─── Content Templates ───────────────────────────────────────

CONTENT_TEMPLATES = {
    "blog": {
        "prompt_prefix": "Write a blog post for an AI automation agency. ",
        "target_words": 800,
        "sections": ["introduction", "problem_statement", "solution", "benefits", "call_to_action"],
        "tone": "authoritative yet accessible, data-driven",
    },
    "social_linkedin": {
        "prompt_prefix": "Write a LinkedIn post for an AI agency CEO. ",
        "target_words": 150,
        "sections": ["hook", "insight", "proof_point", "cta"],
        "tone": "professional, thought-leader, inspiring",
    },
    "social_twitter": {
        "prompt_prefix": "Write a tweet thread (5 tweets) for an AI agency. ",
        "target_words": 200,
        "sections": ["hook_tweet", "problem_tweet", "solution_tweet", "proof_tweet", "cta_tweet"],
        "tone": "punchy, confident, value-packed",
    },
    "email_welcome": {
        "prompt_prefix": "Write a welcome email for a new AI agency lead. ",
        "target_words": 200,
        "sections": ["subject_line", "greeting", "value_prop", "next_steps", "sign_off"],
        "tone": "warm, professional, exciting",
    },
    "email_followup": {
        "prompt_prefix": "Write a follow-up email for a warm AI agency lead. ",
        "target_words": 150,
        "sections": ["subject_line", "reminder", "new_value", "urgency", "cta"],
        "tone": "helpful, not pushy, value-first",
    },
    "landing_page": {
        "prompt_prefix": "Write landing page copy for an AI automation service. ",
        "target_words": 500,
        "sections": ["headline", "subheadline", "pain_points", "solution", "features", "social_proof", "pricing_hint", "cta"],
        "tone": "compelling, benefit-focused, conversion-optimized",
    },
    "case_study": {
        "prompt_prefix": "Write a case study for an AI agency client success. ",
        "target_words": 600,
        "sections": ["client_overview", "challenge", "solution_implemented", "results", "testimonial_prompt", "conclusion"],
        "tone": "factual, impressive, results-oriented",
    },
    "report": {
        "prompt_prefix": "Write a monthly performance report for an AI agency client. ",
        "target_words": 400,
        "sections": ["executive_summary", "metrics_overview", "highlights", "issues_resolved", "recommendations", "next_month_plan"],
        "tone": "professional, data-driven, actionable",
    },
}


def get_template(content_type: str) -> dict:
    """Get content generation template."""
    return CONTENT_TEMPLATES.get(content_type, CONTENT_TEMPLATES["blog"])


def create_content(content_type: str, title: str, body: str = "",
                   channel: str = "", tags: list = None) -> ContentPiece:
    """Create a new content piece."""
    pieces = _load_content()
    content_id = f"content_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(pieces)}"
    
    piece = ContentPiece(
        content_id=content_id,
        content_type=content_type,
        title=title,
        body=body,
        target_channel=channel,
        tags=tags or [],
        word_count=len(body.split()) if body else 0,
    )
    
    pieces.append(piece)
    _save_content(pieces)
    return piece


def update_content(content_id: str, **kwargs) -> Optional[ContentPiece]:
    """Update a content piece."""
    pieces = _load_content()
    for i, piece in enumerate(pieces):
        if piece.content_id == content_id:
            for key, value in kwargs.items():
                if hasattr(piece, key):
                    setattr(piece, key, value)
            if "body" in kwargs:
                piece.word_count = len(kwargs["body"].split())
            pieces[i] = piece
            _save_content(pieces)
            return piece
    return None


def get_content(content_type: str = "", status: str = "", limit: int = 50) -> list:
    """Get content pieces with optional filters."""
    pieces = _load_content()
    if content_type:
        pieces = [p for p in pieces if p.content_type == content_type]
    if status:
        pieces = [p for p in pieces if p.status == status]
    pieces.sort(key=lambda p: p.created_at, reverse=True)
    return pieces[:limit]


def get_content_calendar(days: int = 30) -> dict:
    """Get content calendar / pipeline summary."""
    pieces = _load_content()
    summary = {
        "total": len(pieces),
        "by_type": {},
        "by_status": {},
        "by_channel": {},
        "total_words": sum(p.word_count for p in pieces),
    }
    
    for piece in pieces:
        summary["by_type"][piece.content_type] = summary["by_type"].get(piece.content_type, 0) + 1
        summary["by_status"][piece.status] = summary["by_status"].get(piece.status, 0) + 1
        summary["by_channel"][piece.target_channel] = summary["by_channel"].get(piece.target_channel, 0) + 1

    return summary


def generate_content_brief(content_type: str, topic: str, audience: str = "business owners") -> str:
    """
    Generate a content brief that can be sent to the swarm orchestrator
    for parallel content production.
    """
    template = get_template(content_type)
    sections = template.get("sections", [])
    
    brief = f"""CONTENT BRIEF
Type: {content_type}
Topic: {topic}
Target Audience: {audience}
Tone: {template.get('tone', 'professional')}
Target Word Count: {template.get('target_words', 500)}

SECTIONS TO COVER:
{chr(10).join(f'  {i+1}. {s.replace("_", " ").title()}' for i, s in enumerate(sections))}

BRAND CONTEXT:
- Company: Executive USA AI Agency
- Services: AI automation, chatbot development, voice AI, video content, custom agents
- Differentiator: Built on Agent Zero framework, 25+ LLM providers, full-stack AI
- Pricing: Starter $497/mo, Growth $1,497/mo, Enterprise custom
- Target market: SMBs and enterprises wanting AI automation

INSTRUCTIONS:
{template.get('prompt_prefix', '')}
Focus on {topic}. Write for {audience}.
Make it actionable, data-driven where possible, and always end with a clear CTA.
"""
    return brief
