"""
Dashboard API — Cost Tracking Panel

Endpoint: /dashboard_cost (POST)
Actions:
  - summary: Get overall cost summary (daily, monthly, per-agent)
  - daily: Get daily cost breakdown
  - agents: Get per-agent cost breakdown
  - models: Get per-model cost breakdown
  - budget: Get/set budget configuration
  - history: Get cost history for date range
"""

import os
import json
from datetime import datetime, timezone, timedelta
from flask import Request
from python.helpers.api import ApiHandler, Input, Output


class DashboardCost(ApiHandler):

    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "summary")

        if action == "summary":
            return await self._summary()
        elif action == "daily":
            return await self._daily()
        elif action == "agents":
            return await self._agents()
        elif action == "models":
            return await self._models()
        elif action == "budget":
            return await self._budget(input)
        elif action == "history":
            return await self._history(input)
        else:
            return {"error": f"Unknown action: {action}", "available": ["summary", "daily", "agents", "models", "budget", "history"]}

    async def _summary(self) -> Output:
        """Get overall cost summary."""
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            return {
                "ok": True,
                "daily_spend": tracker.get_daily_spend(),
                "monthly_spend": tracker.get_monthly_spend(),
                "budget_status": tracker.get_budget_status(),
                "model_breakdown": tracker.get_model_breakdown(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except ImportError:
            return {"ok": False, "error": "Cost tracker not available"}

    async def _daily(self) -> Output:
        """Get today's cost breakdown."""
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            return {
                "ok": True,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "total_spend": tracker.get_daily_spend(),
                "breakdown": tracker.get_daily_breakdown(),
            }
        except ImportError:
            return {"ok": False, "error": "Cost tracker not available"}

    async def _agents(self) -> Output:
        """Get per-agent cost breakdown."""
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()

            # Get agent roster for full picture
            agent_costs = {}
            try:
                from python.helpers.orchestration_config import load_orchestration_config
                config = load_orchestration_config()
                for agent_def in config.agents:
                    agent_costs[agent_def.id] = {
                        "name": agent_def.name,
                        "spend_today": tracker.get_agent_spend(agent_def.id),
                        "budget_exceeded": tracker.is_agent_budget_exceeded(agent_def.id),
                    }
            except ImportError:
                pass

            return {"ok": True, "agent_costs": agent_costs}
        except ImportError:
            return {"ok": False, "error": "Cost tracker not available"}

    async def _models(self) -> Output:
        """Get per-model cost breakdown."""
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            return {
                "ok": True,
                "model_breakdown": tracker.get_model_breakdown(),
            }
        except ImportError:
            return {"ok": False, "error": "Cost tracker not available"}

    async def _budget(self, input: Input) -> Output:
        """Get or set budget configuration."""
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()

            # SET operations
            new_monthly_cap = input.get("monthly_cap")
            if new_monthly_cap is not None:
                tracker.set_monthly_cap(float(new_monthly_cap))

            new_agent_cap = input.get("agent_cap")
            agent_id = input.get("agent_id")
            if new_agent_cap is not None and agent_id:
                tracker.set_agent_cap(agent_id, float(new_agent_cap))

            return {
                "ok": True,
                "budget_status": tracker.get_budget_status(),
            }
        except ImportError:
            return {"ok": False, "error": "Cost tracker not available"}

    async def _history(self, input: Input) -> Output:
        """Get cost history for a date range."""
        days = int(input.get("days", 7))
        cost_dir = "tmp/cost_tracking"
        history = []

        if os.path.exists(cost_dir):
            today = datetime.now(timezone.utc).date()
            for i in range(days):
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                fname = os.path.join(cost_dir, f"costs_{date_str}.json")
                day_total = 0.0
                call_count = 0
                if os.path.exists(fname):
                    try:
                        with open(fname, "r") as f:
                            entries = json.load(f)
                            for entry in entries:
                                day_total += entry.get("estimated_cost", 0)
                                call_count += 1
                    except Exception:
                        pass
                history.append({
                    "date": date_str,
                    "total_cost": round(day_total, 4),
                    "call_count": call_count,
                })

        return {"ok": True, "history": history, "days": days}
