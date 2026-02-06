### model_switcher:
Switch between AI models or manage the intelligent model router.
The model router automatically selects the best model for each task type.
You can manually switch, lock/unlock auto-routing, or get recommendations.

#### switch - Switch to a specific model
~~~json
{
    "thoughts": ["I need to use Kimi K2 for this code task..."],
    "headline": "Switching to Kimi K2",
    "tool_name": "model_switcher",
    "tool_method": "switch",
    "tool_args": {
        "model": "moonshot/kimi-k2-turbo-preview"
    }
}
~~~

#### status - Show current model and router state
~~~json
{
    "thoughts": ["Let me check which model is active..."],
    "headline": "Checking model status",
    "tool_name": "model_switcher",
    "tool_method": "status",
    "tool_args": {}
}
~~~

#### list - List available models (optionally filter by provider)
~~~json
{
    "thoughts": ["Let me see available models..."],
    "headline": "Listing available models",
    "tool_name": "model_switcher",
    "tool_method": "list",
    "tool_args": {
        "provider": "moonshot"
    }
}
~~~

#### lock - Lock current model (disable auto-routing)
~~~json
{
    "thoughts": ["I want to stay on this model..."],
    "headline": "Locking model",
    "tool_name": "model_switcher",
    "tool_method": "lock",
    "tool_args": {}
}
~~~

#### unlock - Re-enable auto-routing
~~~json
{
    "thoughts": ["Let the router choose automatically again..."],
    "headline": "Unlocking model router",
    "tool_name": "model_switcher",
    "tool_method": "unlock",
    "tool_args": {}
}
~~~

#### recommend - Get model recommendation for a task
~~~json
{
    "thoughts": ["What model should I use for this?"],
    "headline": "Getting model recommendation",
    "tool_name": "model_switcher",
    "tool_method": "recommend",
    "tool_args": {
        "task": "Write a Python web scraper with async support"
    }
}
~~~
