### parallel_delegate

Spawn multiple subordinate agents that run **concurrently** and return all results at once.

Use this instead of `call_subordinate` whenever work can be split into independent pieces.
Each subtask gets its own isolated context -- no shared state, no ordering constraints.

**when to use:**
- you have 2+ subtasks that do not depend on each other's output
- you want maximum throughput (all subtasks finish as fast as the slowest one)
- examples: scan + design in parallel, write code + write tests in parallel

**when NOT to use:**
- subtasks depend on each other (use sequential call_subordinate instead)
- there is only one subtask (use call_subordinate)

**tasks array:**
Each item in `tasks` is an object with:
  - `message`  (required): the full instruction for that subtask, including role context
  - `profile`  (optional): agent profile to use (e.g. "developer", "github-repo-scanner", "researcher")
  - `attachments` (optional): list of file paths or URLs

**limits:**
- maximum 8 concurrent subtasks per call
- each subtask has the same timeout as a normal subordinate

example usage:
~~~json
{
    "thoughts": [
        "The task has three independent parts.",
        "I can scan, design, and research simultaneously.",
    ],
    "tool_name": "parallel_delegate",
    "tool_args": {
        "tasks": [
            {
                "message": "Scan the authentication module for security vulnerabilities. Return a structured list of findings.",
                "profile": "github-repo-scanner"
            },
            {
                "message": "Design a modern login page component following the project design system. Return the React component code.",
                "profile": "developer"
            },
            {
                "message": "Research current best practices for OAuth2 PKCE flows and summarise the key points.",
                "profile": "researcher"
            }
        ]
    }
}
~~~

**response format:**
Results come back as a numbered list separated by `---`.
Each entry shows [Task N DONE] or [Task N FAILED] with the subtask result or error.
Parse the results and act on them in your next step.
