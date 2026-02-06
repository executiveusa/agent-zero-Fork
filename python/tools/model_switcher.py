"""
Model Switcher Tool

Allows the agent (or user via chat) to manually switch the active LLM model
or query the current model routing status. Also provides a way to lock/unlock
automatic model routing.

Methods:
  - model_switcher:switch       — Switch to a specific model
  - model_switcher:status       — Show current model and router state
  - model_switcher:list         — List available models by provider
  - model_switcher:lock         — Lock current model (disable auto-routing)
  - model_switcher:unlock       — Unlock (re-enable auto-routing)
  - model_switcher:recommend    — Get router recommendation for a task description
"""

import json
from python.helpers.tool import Tool, Response

# Known models organized by provider for quick reference
KNOWN_MODELS = {
    "moonshot": {
        "provider": "Moonshot/Kimi",
        "api_base": "https://api.moonshot.ai/v1",
        "models": [
            {"id": "moonshot/kimi-k2-turbo-preview", "ctx": "262K", "best_for": "code, general"},
            {"id": "moonshot/kimi-k2.5", "ctx": "262K", "best_for": "multimodal, vision+thinking"},
            {"id": "moonshot/kimi-k2-thinking", "ctx": "262K", "best_for": "deep reasoning, math"},
            {"id": "moonshot/moonshot-v1-128k", "ctx": "128K", "best_for": "long context"},
        ],
    },
    "zhipu": {
        "provider": "Zhipu AI/GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "openai/glm-4-plus", "ctx": "128K", "best_for": "general, Chinese"},
            {"id": "openai/glm-4-flash", "ctx": "128K", "best_for": "fast, cheap"},
        ],
    },
    "google": {
        "provider": "Google Gemini",
        "models": [
            {"id": "gemini/gemini-2.5-pro", "ctx": "1M", "best_for": "vision, reasoning, code"},
            {"id": "gemini/gemini-2.5-flash", "ctx": "1M", "best_for": "fast, balanced"},
        ],
    },
    "anthropic": {
        "provider": "Anthropic",
        "models": [
            {"id": "anthropic/claude-sonnet-4-20250514", "ctx": "200K", "best_for": "creative, analysis"},
            {"id": "anthropic/claude-3.5-haiku-20241022", "ctx": "200K", "best_for": "fast, cheap"},
        ],
    },
    "openai": {
        "provider": "OpenAI",
        "models": [
            {"id": "openai/gpt-4o", "ctx": "128K", "best_for": "general purpose"},
            {"id": "openai/gpt-4o-mini", "ctx": "128K", "best_for": "fast, cheap"},
            {"id": "openai/o1", "ctx": "200K", "best_for": "reasoning"},
        ],
    },
    "deepseek": {
        "provider": "DeepSeek",
        "models": [
            {"id": "deepseek/deepseek-chat", "ctx": "64K", "best_for": "code, general"},
            {"id": "deepseek/deepseek-reasoner", "ctx": "64K", "best_for": "reasoning"},
        ],
    },
}


class ModelSwitcherTool(Tool):

    async def execute(self, **kwargs) -> Response:
        method = self.method or "status"

        if method == "switch":
            return await self._switch(**kwargs)
        elif method == "status":
            return await self._status(**kwargs)
        elif method == "list":
            return await self._list(**kwargs)
        elif method == "lock":
            return await self._lock(**kwargs)
        elif method == "unlock":
            return await self._unlock(**kwargs)
        elif method == "recommend":
            return await self._recommend(**kwargs)
        else:
            return Response(
                message=f"Unknown method 'model_switcher:{method}'. Use: switch, status, list, lock, unlock, recommend",
                break_loop=False,
            )

    async def _switch(self, **kwargs) -> Response:
        model = self.args.get("model", "")
        if not model:
            return Response(message="Provide 'model' argument (e.g. 'moonshot/kimi-k2-turbo-preview')", break_loop=False)

        old_model = self.agent.config.chat_model
        self.agent.config.chat_model = model

        # Lock routing so the router doesn't override this manual choice
        if self.loop_data:
            self.loop_data.params_temporary["model_router_override_locked"] = True

        return Response(
            message=f"Model switched: {old_model} → {model}\nAuto-routing locked until unlocked.",
            break_loop=False,
        )

    async def _status(self, **kwargs) -> Response:
        locked = False
        router_active = "none"
        if self.loop_data:
            locked = self.loop_data.params_temporary.get("model_router_override_locked", False)
            router_active = self.loop_data.params_temporary.get("model_router_active", "none")

        status = {
            "current_chat_model": self.agent.config.chat_model,
            "current_utility_model": self.agent.config.utility_model,
            "router_locked": locked,
            "router_last_classification": router_active,
            "agent_name": self.agent.agent_name,
            "profile": self.agent.config.profile or "default",
        }
        return Response(message=json.dumps(status, indent=2), break_loop=False)

    async def _list(self, **kwargs) -> Response:
        provider_filter = self.args.get("provider", "")
        
        if provider_filter:
            filtered = {k: v for k, v in KNOWN_MODELS.items() if provider_filter.lower() in k.lower() or provider_filter.lower() in v["provider"].lower()}
        else:
            filtered = KNOWN_MODELS

        lines = []
        for key, info in filtered.items():
            lines.append(f"\n## {info['provider']}")
            if "api_base" in info:
                lines.append(f"  API: {info['api_base']}")
            for m in info["models"]:
                lines.append(f"  - {m['id']}  (ctx: {m['ctx']}, best for: {m['best_for']})")

        return Response(message="\n".join(lines) if lines else "No models found matching filter.", break_loop=False)

    async def _lock(self, **kwargs) -> Response:
        if self.loop_data:
            self.loop_data.params_temporary["model_router_override_locked"] = True
        return Response(message=f"Auto-routing LOCKED. Current model: {self.agent.config.chat_model}", break_loop=False)

    async def _unlock(self, **kwargs) -> Response:
        if self.loop_data:
            self.loop_data.params_temporary["model_router_override_locked"] = False
        return Response(message="Auto-routing UNLOCKED. Model router will now auto-switch based on task type.", break_loop=False)

    async def _recommend(self, **kwargs) -> Response:
        task_desc = self.args.get("task", "")
        if not task_desc:
            return Response(message="Provide 'task' argument with a description.", break_loop=False)

        # Import the classifier from the router extension
        try:
            from python.extensions.before_main_llm_call._20_model_router import classify_task, MODEL_ROUTES
            task_type = classify_task(task_desc)
            recommended = MODEL_ROUTES.get(task_type, "default (keep current)")
            return Response(
                message=f"Task type: {task_type}\nRecommended model: {recommended}",
                break_loop=False,
            )
        except ImportError:
            return Response(message="Model router extension not available.", break_loop=False)
