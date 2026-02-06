### swarm_orchestrator:
Orchestrate parallel execution of multiple agents as a "swarm" to handle complex tasks.
The swarm automatically decomposes tasks and assigns them to specialized agent profiles.

#### launch - Launch a new swarm
Auto-detects strategy (code_review, project_finish, research, general) or use custom tasks.
~~~json
{
    "thoughts": ["This task needs multiple agents working in parallel..."],
    "headline": "Launching agent swarm",
    "tool_name": "swarm_orchestrator",
    "tool_method": "launch",
    "tool_args": {
        "objective": "Complete all open issues in executiveusa/pauli-comic-funnel",
        "name": "project_finisher_swarm",
        "strategy": "project_finish"
    }
}
~~~

#### launch with custom tasks
~~~json
{
    "thoughts": ["I need specific agents for specific sub-tasks..."],
    "headline": "Launching custom swarm",
    "tool_name": "swarm_orchestrator",
    "tool_method": "launch",
    "tool_args": {
        "objective": "Full code review and security audit",
        "tasks": [
            {"description": "Check for SQL injection vulnerabilities", "profile": "hacker", "model": "moonshot/kimi-k2-turbo-preview"},
            {"description": "Review authentication flow", "profile": "developer", "model": "moonshot/kimi-k2-thinking"},
            {"description": "Check dependency versions", "profile": "researcher", "model": "openai/glm-4-flash"}
        ]
    }
}
~~~

#### status - Check swarm progress
~~~json
{
    "thoughts": ["Let me check how the swarm is doing..."],
    "headline": "Checking swarm status",
    "tool_name": "swarm_orchestrator",
    "tool_method": "status",
    "tool_args": {
        "swarm_id": "sw_abc12345"
    }
}
~~~

#### results - Get aggregated results
~~~json
{
    "thoughts": ["The swarm should be done, let me get results..."],
    "headline": "Getting swarm results",
    "tool_name": "swarm_orchestrator",
    "tool_method": "results",
    "tool_args": {
        "swarm_id": "sw_abc12345"
    }
}
~~~

#### cancel - Cancel a running swarm
~~~json
{
    "thoughts": ["Need to cancel this swarm..."],
    "headline": "Cancelling swarm",
    "tool_name": "swarm_orchestrator",
    "tool_method": "cancel",
    "tool_args": {
        "swarm_id": "sw_abc12345"
    }
}
~~~

#### list - List all swarm executions
~~~json
{
    "thoughts": ["Let me see all swarm runs..."],
    "headline": "Listing swarms",
    "tool_name": "swarm_orchestrator",
    "tool_method": "list",
    "tool_args": {}
}
~~~
