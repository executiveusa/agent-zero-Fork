"""
Cost-Aware Model Routing — Cost Tracker

Singleton cost tracker that:
- Hooks into LiteLLM calls to log token count + cost per call
- Enforces configurable monthly budget cap ($50 default)
- Tracks per-agent and per-model spend
- Auto-downgrades to free-tier models when budget exceeded
- Persists to tmp/cost_tracking/ using Byte Rover atomic writes

Follows Ralphie loop Perception phase:
  Read cost data → assess budget remaining → inform routing decisions

Created: 2026-02-09
"""

import os
import json
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass, field, asdict
from python.helpers.print_style import PrintStyle
from python.helpers.tkgm_memory import ByteRoverAtomic


# ─── Configuration ───────────────────────────────────────────

COST_TRACKING_DIR = "tmp/cost_tracking"

# Default budget caps
DEFAULT_MONTHLY_CAP = 50.0  # USD
DEFAULT_AGENT_CAP = 20.0    # USD per agent per month

# Free-tier fallback models (OpenRouter free tier)
FREE_TIER_MODELS = [
    "openrouter/zhipu-ai/glm-4-flash",
    "openrouter/zhipu-ai/glm-4",
    "openai/glm-4-flash",  # via zhipu api_base
]

# Known model costs (per 1M tokens, USD) - fallback when LiteLLM cost unavailable
KNOWN_COSTS = {
    "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic/claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
    "openai/gpt-4o": {"input": 2.5, "output": 10.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "moonshot/kimi-k2-turbo-preview": {"input": 0.0, "output": 0.0},  # Free tier
    "moonshot/kimi-k2-thinking": {"input": 0.0, "output": 0.0},
    "gemini/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "openai/glm-4-flash": {"input": 0.0, "output": 0.0},  # Free on OpenRouter
    "openrouter/zhipu-ai/glm-4-flash": {"input": 0.0, "output": 0.0},
    "openrouter/zhipu-ai/glm-4": {"input": 0.0, "output": 0.0},
}


# ─── Cost Entry Dataclass ────────────────────────────────────

@dataclass
class CostEntry:
    timestamp: str
    model: str
    agent_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ─── Singleton Cost Tracker ──────────────────────────────────

class CostTracker:
    """
    Thread-safe singleton cost tracker.
    Persists daily cost logs as JSON files.
    """
    
    _instance: Optional["CostTracker"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.monthly_cap = DEFAULT_MONTHLY_CAP
        self.agent_caps: dict[str, float] = {}
        self._today_entries: list[dict] = []
        self._today_date = ""
        self._load_today()
    
    @classmethod
    def get(cls) -> "CostTracker":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = CostTracker()
        return cls._instance
    
    def _day_file(self, date_str: str = "") -> str:
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(COST_TRACKING_DIR, f"costs_{date_str}.json")
    
    def _load_today(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._today_date:
            self._today_date = today
            self._today_entries = ByteRoverAtomic.read(
                self._day_file(today), default=[]
            )
    
    def _save_today(self):
        ByteRoverAtomic.write(self._day_file(self._today_date), self._today_entries)
    
    # ── Recording ────────────────────────────────────────────
    
    def record_call(
        self,
        model: str,
        agent_id: str = "unknown",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ):
        """Record a single LLM call's cost."""
        self._load_today()
        
        # If cost not provided, estimate from known costs
        if cost_usd == 0.0 and (input_tokens > 0 or output_tokens > 0):
            cost_usd = self._estimate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "agent_id": agent_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 6),
        }
        
        with self._lock:
            self._today_entries.append(entry)
            self._save_today()
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost from known per-model rates."""
        rates = KNOWN_COSTS.get(model, {})
        if not rates:
            # Try partial match
            model_lower = model.lower()
            for known_model, known_rates in KNOWN_COSTS.items():
                if known_model.lower() in model_lower or model_lower in known_model.lower():
                    rates = known_rates
                    break
        
        if not rates:
            # Unknown model, assume moderate cost
            rates = {"input": 1.0, "output": 5.0}
        
        input_cost = (input_tokens / 1_000_000) * rates.get("input", 0)
        output_cost = (output_tokens / 1_000_000) * rates.get("output", 0)
        return input_cost + output_cost
    
    # ── Queries ──────────────────────────────────────────────
    
    def get_daily_spend(self, date_str: str = "") -> float:
        """Total spend for a given day (default: today)."""
        if not date_str:
            self._load_today()
            entries = self._today_entries
        else:
            entries = ByteRoverAtomic.read(self._day_file(date_str), default=[])
        return sum(e.get("cost_usd", 0) for e in entries)
    
    def get_monthly_spend(self) -> float:
        """Total spend for the current month."""
        now = datetime.now(timezone.utc)
        total = 0.0
        
        for day in range(1, now.day + 1):
            date_str = f"{now.strftime('%Y-%m')}-{day:02d}"
            entries = ByteRoverAtomic.read(self._day_file(date_str), default=[])
            total += sum(e.get("cost_usd", 0) for e in entries)
        
        return total
    
    def get_agent_spend(self, agent_id: str, days: int = 30) -> float:
        """Total spend for a specific agent over N days."""
        now = datetime.now(timezone.utc)
        total = 0.0
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            entries = ByteRoverAtomic.read(self._day_file(date_str), default=[])
            total += sum(
                e.get("cost_usd", 0) 
                for e in entries 
                if e.get("agent_id") == agent_id
            )
        
        return total
    
    def get_model_breakdown(self, days: int = 30) -> dict[str, float]:
        """Cost breakdown by model over N days."""
        now = datetime.now(timezone.utc)
        breakdown: dict[str, float] = {}
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            entries = ByteRoverAtomic.read(self._day_file(date_str), default=[])
            for e in entries:
                model = e.get("model", "unknown")
                breakdown[model] = breakdown.get(model, 0) + e.get("cost_usd", 0)
        
        return breakdown
    
    def get_daily_breakdown(self, days: int = 7) -> list[dict]:
        """Daily spend for the last N days."""
        now = datetime.now(timezone.utc)
        result = []
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            entries = ByteRoverAtomic.read(self._day_file(date_str), default=[])
            total = sum(e.get("cost_usd", 0) for e in entries)
            calls = len(entries)
            result.append({
                "date": date_str,
                "total_cost": round(total, 4),
                "call_count": calls,
            })
        
        return result
    
    # ── Budget Enforcement ───────────────────────────────────
    
    def is_budget_exceeded(self) -> bool:
        """Check if monthly budget cap has been exceeded."""
        return self.get_monthly_spend() >= self.monthly_cap
    
    def is_agent_budget_exceeded(self, agent_id: str) -> bool:
        """Check if an agent's budget cap has been exceeded."""
        cap = self.agent_caps.get(agent_id, DEFAULT_AGENT_CAP)
        return self.get_agent_spend(agent_id) >= cap
    
    def get_budget_status(self) -> dict:
        """Get full budget status overview."""
        monthly = self.get_monthly_spend()
        return {
            "monthly_spend": round(monthly, 4),
            "monthly_cap": self.monthly_cap,
            "budget_remaining": round(max(0, self.monthly_cap - monthly), 4),
            "budget_utilization_pct": round((monthly / self.monthly_cap) * 100, 1) if self.monthly_cap > 0 else 0,
            "is_exceeded": self.is_budget_exceeded(),
            "today_spend": round(self.get_daily_spend(), 4),
        }
    
    def get_recommended_model(self, preferred_model: str = "") -> str:
        """
        Get cost-appropriate model recommendation.
        If budget is tight, downgrade to free tier.
        """
        if not self.is_budget_exceeded():
            return preferred_model
        
        # Budget exceeded — find best free-tier alternative
        if FREE_TIER_MODELS:
            return FREE_TIER_MODELS[0]
        
        return preferred_model  # No free alternative available
    
    # ── Config ───────────────────────────────────────────────
    
    def set_monthly_cap(self, cap: float):
        self.monthly_cap = cap
    
    def set_agent_cap(self, agent_id: str, cap: float):
        self.agent_caps[agent_id] = cap
