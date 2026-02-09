"""
Intelligent Model Router Extension

Auto-switches the active model based on task type detected in the current prompt.
Routes to the best model for each task category:
  - Code generation/debugging → Kimi K2 (moonshot/kimi-k2-turbo-preview)
  - Deep reasoning/math → Kimi K2 Thinking (moonshot/kimi-k2-thinking)  
  - Vision/multimodal → Gemini 2.5 Pro (gemini/gemini-2.5-pro)
  - Fast/simple tasks → GLM-4 Flash (zhipu/glm-4-flash)
  - Creative/writing → Anthropic Claude (anthropic/claude-sonnet-4-20250514)
  - Default → whatever is configured in settings

Execution order: _20_ (runs after _10_log_for_stream)
"""

import re
from python.helpers.extension import Extension
from agent import LoopData


# Task classification patterns
TASK_PATTERNS = {
    "code": [
        r"\b(write|create|implement|code|program|function|class|method|debug|fix|refactor|syntax|compile|build|deploy|test|unittest|pytest)\b",
        r"\b(python|javascript|typescript|java|rust|go|html|css|react|node|api|endpoint|database|sql|query)\b",
        r"\b(git|commit|push|pull|merge|branch|repo|github)\b",
        r"```",  # Code blocks in prompt
    ],
    "reasoning": [
        r"\b(analyze|reason|think|explain|why|prove|derive|calculate|solve|logic|theorem|proof|hypothesis)\b",
        r"\b(math|equation|formula|integral|derivative|probability|statistics|algebra)\b",
        r"\b(compare|evaluate|assess|critique|review|argument|debate)\b",
        r"\b(step.by.step|chain.of.thought|let.?s think)\b",
    ],
    "vision": [
        r"\b(image|picture|photo|screenshot|diagram|chart|graph|visual|see|look|describe.this)\b",
        r"\b(ocr|read.text|scan|recognize|identify.in.image)\b",
        r"\.(png|jpg|jpeg|gif|webp|svg|bmp)\b",
    ],
    "fast": [
        r"\b(quick|fast|brief|short|simple|yes.or.no|true.or.false|one.word)\b",
        r"\b(translate|convert|format|list|name|count|define)\b",
        r"^.{0,50}$",  # Very short prompts
    ],
    "creative": [
        r"\b(write|compose|draft|story|poem|essay|article|blog|creative|imagine|fiction)\b",
        r"\b(marketing|copy|slogan|tagline|headline|description|bio|profile)\b",
        r"\b(rewrite|rephrase|summarize|paraphrase|tone|style)\b",
    ],
}

# Model routing map — model strings as used by LiteLLM
MODEL_ROUTES = {
    "code":      "moonshot/kimi-k2-turbo-preview",
    "reasoning": "moonshot/kimi-k2-thinking",
    "vision":    "gemini/gemini-2.5-pro",
    "fast":      "openai/glm-4-flash",  # zhipu via openai-compat prefix + api_base
    "creative":  None,  # keep default (usually Claude or GPT)
}

# Environment variable for the zhipu api_base override
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


def classify_task(text: str) -> str:
    """Classify the task type from prompt text. Returns the highest-scoring category."""
    if not text:
        return "default"

    text_lower = text.lower()
    scores = {}

    for category, patterns in TASK_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            score += len(matches)
        scores[category] = score

    if not scores or max(scores.values()) == 0:
        return "default"

    best = max(scores, key=scores.get)

    # Require minimum confidence (at least 2 pattern hits)
    if scores[best] < 2:
        return "default"

    return best


class ModelRouter(Extension):
    """
    Before each main LLM call, inspect the prompt and optionally override
    the model to the best-fit provider for the detected task type.
    
    Respects manual overrides: if the user explicitly set a model in the 
    conversation (via model_switcher tool), this extension will not override.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Skip if manual override is active
        if loop_data.params_temporary.get("model_router_override_locked"):
            return

        # Skip if router is disabled in agent config
        if hasattr(self.agent.config, 'extras') and not self.agent.config.extras.get("model_router_enabled", True):
            return

        # ── Cost-Aware Budget Check (GAP 3 Enhancement) ──
        try:
            from python.helpers.cost_tracker import CostTracker
            tracker = CostTracker.get()
            
            if tracker.is_budget_exceeded():
                # Budget exceeded — force free-tier model
                free_model = tracker.get_recommended_model(self.agent.config.chat_model)
                if free_model != self.agent.config.chat_model:
                    if "model_router_original" not in loop_data.params_temporary:
                        loop_data.params_temporary["model_router_original"] = self.agent.config.chat_model
                    self.agent.config.chat_model = free_model
                    loop_data.params_temporary["model_router_budget_downgrade"] = True
                    return  # Skip further routing, use free model
            
            # Check per-agent budget
            agent_id = f"agent_{self.agent.number}"
            if tracker.is_agent_budget_exceeded(agent_id):
                free_model = tracker.get_recommended_model(self.agent.config.chat_model)
                if free_model != self.agent.config.chat_model:
                    if "model_router_original" not in loop_data.params_temporary:
                        loop_data.params_temporary["model_router_original"] = self.agent.config.chat_model
                    self.agent.config.chat_model = free_model
                    loop_data.params_temporary["model_router_budget_downgrade"] = True
                    return
        except ImportError:
            pass  # cost_tracker not available, skip budget check

        # Gather recent prompt text for classification
        prompt_text = ""
        if loop_data.extras and "prompt" in loop_data.extras:
            prompt_text = str(loop_data.extras["prompt"])
        elif self.agent.history:
            # Use the last user message
            for msg in reversed(self.agent.history):
                if msg.get("role") == "user":
                    prompt_text = str(msg.get("content", ""))
                    break

        if not prompt_text:
            return

        task_type = classify_task(prompt_text)
        
        if task_type == "default":
            return

        target_model = MODEL_ROUTES.get(task_type)
        if not target_model:
            return

        # Store the original model so it can be restored
        if "model_router_original" not in loop_data.params_temporary:
            loop_data.params_temporary["model_router_original"] = self.agent.config.chat_model

        # Only switch if it's actually different
        current = self.agent.config.chat_model
        if current != target_model:
            loop_data.params_temporary["model_router_active"] = task_type
            loop_data.params_temporary["model_router_target"] = target_model
            # Note: actual model switching happens in the LLM call layer.
            # We store the recommendation; the util_model_call_before extension
            # or the models.py code should pick this up.
            self.agent.config.chat_model = target_model
