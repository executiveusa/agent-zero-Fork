"""
Self-Improvement Extension — Learning from Tool Execution Results

Runs after every tool execution. Analyzes the result for failures or
suboptimal outcomes and stores learned patterns in agent memory for
future reference.

Features:
  - Detect tool failures and log improvement hints
  - Track repeated error patterns
  - Auto-suggest alternative approaches after N failures
  - Build a persistent knowledge base of what works

Execution order: _20_ (runs after _10_mask_secrets)
"""

import json
import re
from datetime import datetime
from python.helpers.extension import Extension
from python.helpers.tool import Response


# In-memory failure tracker (reset on restart; persistent learning goes to memory_save)
_failure_tracker: dict = {}

# Error patterns to learn from
ERROR_PATTERNS = {
    "rate_limit": {
        "patterns": [r"rate.?limit", r"429", r"too many requests", r"quota exceeded"],
        "action": "Switch to a different model or add delay between requests.",
    },
    "auth_error": {
        "patterns": [r"401", r"403", r"unauthorized", r"forbidden", r"invalid.*key", r"authentication"],
        "action": "Check API key validity. Try refreshing token from vault.",
    },
    "timeout": {
        "patterns": [r"timeout", r"timed.?out", r"deadline exceeded", r"connection.*reset"],
        "action": "Increase timeout, retry with smaller payload, or switch to faster model.",
    },
    "context_length": {
        "patterns": [r"context.*length", r"max.*tokens", r"too long", r"token limit"],
        "action": "Truncate input, summarize context, or switch to model with larger context window.",
    },
    "not_found": {
        "patterns": [r"not.?found", r"404", r"does not exist", r"no such"],
        "action": "Verify the resource path/name. Check if the target was moved or deleted.",
    },
    "parse_error": {
        "patterns": [r"json.*parse", r"syntax.*error", r"unexpected token", r"invalid.*format"],
        "action": "Fix output format. Ensure valid JSON. Use utility model for formatting.",
    },
}


def detect_error_type(message: str) -> tuple:
    """Detect the type of error from a response message. Returns (type, action) or (None, None)."""
    if not message:
        return None, None

    lower = message.lower()
    for err_type, info in ERROR_PATTERNS.items():
        for pattern in info["patterns"]:
            if re.search(pattern, lower):
                return err_type, info["action"]
    return None, None


class SelfImprovement(Extension):
    """
    After each tool execution, analyze the result and store learnings
    in the agent's temporary parameters and optionally in long-term memory.
    """

    async def execute(self, response: Response | None = None, **kwargs):
        if not response:
            return

        tool = kwargs.get("tool")
        tool_name = tool.name if tool else "unknown"
        tool_method = tool.method if tool else ""
        full_name = f"{tool_name}:{tool_method}" if tool_method else tool_name

        message = response.message or ""

        # Check for error patterns
        err_type, suggested_action = detect_error_type(message)

        if err_type:
            # Track failure count
            key = f"{full_name}:{err_type}"
            _failure_tracker[key] = _failure_tracker.get(key, 0) + 1
            count = _failure_tracker[key]

            # Log the learning
            learning = {
                "tool": full_name,
                "error_type": err_type,
                "occurrence": count,
                "suggestion": suggested_action,
                "timestamp": datetime.now().isoformat(),
                "snippet": message[:200],
            }

            # Store in agent's temporary params for immediate use
            if self.agent and hasattr(self.agent, 'context'):
                learnings = getattr(self.agent.context, '_self_improvement_log', [])
                learnings.append(learning)
                self.agent.context._self_improvement_log = learnings[-50:]  # Keep last 50

            # After 3 failures of same type, inject hint into agent's awareness
            if count >= 3:
                hint = (
                    f"\n[Self-Improvement Hint] Tool '{full_name}' has failed {count} times "
                    f"with '{err_type}'. Suggestion: {suggested_action}"
                )
                response.message = response.message + hint

            # After 5 failures, try to save to long-term memory
            if count == 5 and self.agent:
                try:
                    memory_note = (
                        f"LEARNED: Tool '{full_name}' frequently fails with '{err_type}'. "
                        f"Root cause pattern: {message[:100]}. "
                        f"Best action: {suggested_action}"
                    )
                    # This will be picked up by memory_save if the agent decides to act on it
                    if hasattr(response, 'additional') and response.additional is None:
                        response.additional = {}
                    if response.additional is not None:
                        response.additional["self_improvement_memory"] = memory_note
                except Exception:
                    pass  # Non-critical, don't break execution

        # Track success patterns too — reset failure counter on success
        elif not any(word in message.lower() for word in ["error", "failed", "exception"]):
            # Success — reduce failure tracking stress
            for key in list(_failure_tracker.keys()):
                if key.startswith(f"{full_name}:"):
                    _failure_tracker[key] = max(0, _failure_tracker[key] - 1)
