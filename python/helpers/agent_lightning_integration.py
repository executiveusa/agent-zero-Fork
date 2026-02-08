"""
Agent Lightning Integration — Microsoft's agent optimization framework

Provides:
- Span tracing for agent actions (tool calls, LLM calls)
- Automatic Prompt Optimization (APO) hooks
- Reward signal emission for reinforcement learning

Integration is optional — gracefully degrades when agentlightning is not installed.
See: https://github.com/microsoft/agent-lightning

NOTE: Agent Lightning officially supports Linux. On Windows, use WSL2 or
set AGL_ENABLED=false to disable.
"""

import os
import logging
import time
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Agent Lightning
AGL_AVAILABLE = False
try:
    import agentlightning as agl
    AGL_AVAILABLE = True
    logger.info("Agent Lightning loaded successfully")
except ImportError:
    logger.info("Agent Lightning not installed — optimization features disabled")


def is_enabled() -> bool:
    """Check if Agent Lightning is available and enabled."""
    if not AGL_AVAILABLE:
        return False
    return os.environ.get("AGL_ENABLED", "true").lower() != "false"


class AGLTracer:
    """
    Lightweight tracing wrapper for Agent Lightning.

    Usage:
        tracer = AGLTracer()
        with tracer.span("tool_call", {"tool": "voice_notify"}):
            result = await tool.execute()
        tracer.emit_reward(0.9, "task_completed")
    """

    def __init__(self, project_name: str = "agent-claw"):
        self.project_name = project_name
        self._active = is_enabled()
        self._span_stack: list = []

        if self._active:
            try:
                # Initialize AGL store if available
                store_path = os.environ.get(
                    "AGL_STORE_PATH", "tmp/agl_store"
                )
                os.makedirs(store_path, exist_ok=True)
                logger.info(f"AGL tracing active, store: {store_path}")
            except Exception as e:
                logger.warning(f"AGL initialization failed: {e}")
                self._active = False

    @contextmanager
    def span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracing a span (tool call, LLM call, etc).

        Args:
            name: Span name (e.g., "tool_call", "llm_inference")
            metadata: Optional key-value metadata for the span
        """
        start_time = time.time()
        span_data = {
            "name": name,
            "start_time": start_time,
            "metadata": metadata or {},
        }
        self._span_stack.append(span_data)

        try:
            if self._active:
                try:
                    agl.start_span(name, **(metadata or {}))
                except Exception:
                    pass  # AGL span start failed, continue silently
            yield span_data
        except Exception as e:
            span_data["error"] = str(e)
            raise
        finally:
            span_data["duration_ms"] = (time.time() - start_time) * 1000
            self._span_stack.pop()

            if self._active:
                try:
                    agl.end_span()
                except Exception:
                    pass  # AGL span end failed, continue silently

            logger.debug(
                f"Span '{name}' completed in {span_data['duration_ms']:.1f}ms"
            )

    def emit_reward(self, score: float, reason: str = ""):
        """
        Emit a reward signal for RL-based optimization.

        Args:
            score: Reward value (0.0-1.0, where 1.0 is best)
            reason: Human-readable reason for the reward
        """
        if not self._active:
            return

        try:
            agl.emit_reward(score, reason=reason)
            logger.debug(f"AGL reward emitted: {score} ({reason})")
        except Exception as e:
            logger.debug(f"AGL reward emission failed: {e}")

    def log_tool_call(
        self,
        tool_name: str,
        method: str,
        args: Dict[str, Any],
        result: str,
        success: bool = True,
        duration_ms: float = 0,
    ):
        """
        Log a tool call event for optimization analysis.

        Args:
            tool_name: Name of the tool
            method: Tool method called
            args: Arguments passed
            result: Result text (truncated)
            success: Whether the call succeeded
            duration_ms: Call duration in milliseconds
        """
        if not self._active:
            return

        metadata = {
            "tool": tool_name,
            "method": method,
            "args_keys": list(args.keys()) if args else [],
            "result_length": len(result),
            "success": success,
            "duration_ms": duration_ms,
        }

        try:
            with self.span("tool_call", metadata):
                pass  # Span is just for logging
        except Exception:
            pass

    def log_llm_call(
        self,
        model: str,
        provider: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0,
    ):
        """
        Log an LLM inference call.

        Args:
            model: Model name
            provider: Provider name
            input_tokens: Input token count
            output_tokens: Output token count
            duration_ms: Call duration in milliseconds
        """
        if not self._active:
            return

        metadata = {
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
        }

        try:
            with self.span("llm_call", metadata):
                pass
        except Exception:
            pass


def trace_tool(func: Callable) -> Callable:
    """
    Decorator to automatically trace tool execute() methods.

    Usage:
        class MyTool(Tool):
            @trace_tool
            async def execute(self, **kwargs):
                ...
    """

    @wraps(func)
    async def wrapper(self, **kwargs):
        tracer = get_tracer()
        start = time.time()
        tool_name = getattr(self, "name", func.__qualname__)
        method = getattr(self, "method", "execute")

        try:
            with tracer.span("tool_execute", {"tool": tool_name, "method": method}):
                result = await func(self, **kwargs)

            duration = (time.time() - start) * 1000
            tracer.log_tool_call(
                tool_name=tool_name,
                method=method,
                args=getattr(self, "args", {}),
                result=getattr(result, "message", "")[:200],
                success=True,
                duration_ms=duration,
            )
            return result

        except Exception as e:
            duration = (time.time() - start) * 1000
            tracer.log_tool_call(
                tool_name=tool_name,
                method=method,
                args=getattr(self, "args", {}),
                result=str(e)[:200],
                success=False,
                duration_ms=duration,
            )
            raise

    return wrapper


# Module-level singleton
_tracer: Optional[AGLTracer] = None


def get_tracer(project_name: str = "agent-claw") -> AGLTracer:
    """Get or create the module-level tracer singleton."""
    global _tracer
    if _tracer is None:
        _tracer = AGLTracer(project_name=project_name)
    return _tracer
