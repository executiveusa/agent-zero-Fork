"""
Perplexity API Integration with LiteLLM Compatibility
Enhanced wrapper for Perplexity search with cost tracking and retry logic.
"""

import time
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from openai import OpenAI, APIError, RateLimitError, APITimeoutError
import models

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PerplexityModel:
    """Perplexity model configurations."""
    name: str
    context_window: int
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for given token usage."""
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output
        return input_cost + output_cost


@dataclass
class PerplexityResult:
    """Result from Perplexity search."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    response_time_ms: int
    timestamp: datetime
    citations: Optional[List[str]] = None


# ============================================================================
# Model Registry
# ============================================================================

PERPLEXITY_MODELS: Dict[str, PerplexityModel] = {
    "llama-3.1-sonar-small-128k-online": PerplexityModel(
        name="llama-3.1-sonar-small-128k-online",
        context_window=128000,
        max_tokens=8192,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0002
    ),
    "llama-3.1-sonar-large-128k-online": PerplexityModel(
        name="llama-3.1-sonar-large-128k-online",
        context_window=128000,
        max_tokens=8192,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.001
    ),
    "llama-3.1-sonar-huge-128k-online": PerplexityModel(
        name="llama-3.1-sonar-huge-128k-online",
        context_window=128000,
        max_tokens=8192,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.005
    ),
}


# ============================================================================
# Cost Tracker
# ============================================================================

class PerplexityCostTracker:
    """Track Perplexity API usage and costs."""
    
    def __init__(self):
        self.total_requests: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost: float = 0.0
        self.session_start: datetime = datetime.now()
    
    def record_usage(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int, 
        cost: float
    ):
        """Record API usage."""
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        
        logger.info(
            f"Perplexity usage - Model: {model}, "
            f"Input: {input_tokens}, Output: {output_tokens}, "
            f"Cost: ${cost:.6f}"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        duration = (datetime.now() - self.session_start).total_seconds()
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "session_duration_seconds": round(duration, 2),
            "avg_cost_per_request": round(
                self.total_cost / self.total_requests, 6
            ) if self.total_requests > 0 else 0
        }
    
    def reset(self):
        """Reset counters."""
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.session_start = datetime.now()


# Global cost tracker instance
cost_tracker = PerplexityCostTracker()


# ============================================================================
# Enhanced Perplexity Search
# ============================================================================

def perplexity_search_litellm(
    query: str,
    model: str = "llama-3.1-sonar-large-128k-online",
    api_key: Optional[str] = None,
    base_url: str = "https://api.perplexity.ai",
    max_retries: int = 3,
    initial_delay: float = 1.0,
    temperature: float = 0.0,
    system_prompt: Optional[str] = None,
    stream: bool = False,
    enable_cost_tracking: bool = True
) -> PerplexityResult:
    """
    Enhanced Perplexity search with LiteLLM compatibility.
    
    Args:
        query: Search query
        model: Perplexity model name
        api_key: API key (auto-fetched if None)
        base_url: API base URL
        max_retries: Maximum retry attempts
        initial_delay: Initial delay between retries (exponential backoff)
        temperature: Response temperature (0.0 = focused, higher = diverse)
        system_prompt: Optional system prompt
        stream: Enable streaming response
        enable_cost_tracking: Track usage costs
    
    Returns:
        PerplexityResult with content and metadata
    """
    start_time = time.time()
    
    # Validate model
    if model not in PERPLEXITY_MODELS:
        logger.warning(f"Unknown model {model}, using default")
        model = "llama-3.1-sonar-large-128k-online"
    
    model_config = PERPLEXITY_MODELS[model]
    
    # Get API key
    api_key = api_key or models.get_api_key("perplexity")
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": query
    })
    
    # Retry loop with exponential backoff
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            if not stream:
                response = client.chat.completions.create(**kwargs)
                
                content = response.choices[0].message.content or ""
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                
                # Calculate cost
                cost = model_config.estimate_cost(input_tokens, output_tokens)
                
                # Track cost
                if enable_cost_tracking:
                    cost_tracker.record_usage(model, input_tokens, output_tokens, cost)
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                return PerplexityResult(
                    content=content,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.now()
                )
            else:
                # Handle streaming
                return _handle_streaming(
                    client, kwargs, model_config, start_time,
                    model, enable_cost_tracking
                )
                
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded (attempt {attempt + 1}): {e}")
            last_error = e
            time.sleep(delay * 2)
            
        except APITimeoutError as e:
            logger.warning(f"API timeout (attempt {attempt + 1}): {e}")
            last_error = e
            time.sleep(delay)
            
        except APIError as e:
            logger.warning(f"API error (attempt {attempt + 1}): {e}")
            last_error = e
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            last_error = e
            break
        
        delay *= 2  # Exponential backoff
    
    # All retries exhausted
    error_msg = f"Perplexity search failed after {max_retries + 1} attempts: {last_error}"
    logger.error(error_msg)
    
    return PerplexityResult(
        content=f"Error: {error_msg}",
        model=model,
        input_tokens=0,
        output_tokens=0,
        cost=0.0,
        response_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now()
    )


def _handle_streaming(
    client: OpenAI,
    kwargs: Dict[str, Any],
    model_config: PerplexityModel,
    start_time: float,
    model: str,
    enable_cost_tracking: bool
) -> PerplexityResult:
    """Handle streaming response from Perplexity."""
    content_chunks = []
    input_tokens = 0
    
    try:
        response = client.chat.completions.create(**kwargs)
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                content_chunks.append(chunk.choices[0].delta.content)
        
        content = "".join(content_chunks)
        output_tokens = len(content.split()) * 1.3  # Rough estimate
        
        cost = model_config.estimate_cost(input_tokens, int(output_tokens))
        
        if enable_cost_tracking:
            cost_tracker.record_usage(model, input_tokens, int(output_tokens), cost)
        
        return PerplexityResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=int(output_tokens),
            cost=cost,
            response_time_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        return PerplexityResult(
            content=f"Error: {str(e)}",
            model=model,
            input_tokens=input_tokens,
            output_tokens=0,
            cost=0.0,
            response_time_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now()
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def perplexity_search(
    query: str,
    model: str = "llama-3.1-sonar-large-128k-online",
    api_key: Optional[str] = None
) -> str:
    """
    Simple Perplexity search (backward compatible).
    
    Args:
        query: Search query
        model: Model name
        api_key: API key (optional)
    
    Returns:
        Response text
    """
    result = perplexity_search_litellm(
        query=query,
        model=model,
        api_key=api_key,
        enable_cost_tracking=False
    )
    return result.content


def get_perplexity_models() -> List[str]:
    """Get list of available Perplexity models."""
    return list(PERPLEXITY_MODELS.keys())


def get_model_info(model: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific model."""
    if model not in PERPLEXITY_MODELS:
        return None
    
    config = PERPLEXITY_MODELS[model]
    return {
        "name": config.name,
        "context_window": config.context_window,
        "max_tokens": config.max_tokens,
        "cost_per_1k_input": config.cost_per_1k_input,
        "cost_per_1k_output": config.cost_per_1k_output,
        "estimated_cost_1k_tokens": config.estimate_cost(500, 500)
    }


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "perplexity_search",
    "perplexity_search_litellm",
    "get_perplexity_models",
    "get_model_info",
    "cost_tracker",
    "PerplexityCostTracker",
    "PerplexityResult",
    "PerplexityModel"
]
