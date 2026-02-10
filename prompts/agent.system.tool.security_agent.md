## security_agent: Agent Claw Security Operations

The security agent is a comprehensive security tool that monitors, audits, and protects the Agent Claw platform.
It can be invoked directly or runs automatically via scheduled cron jobs.

### Methods

#### security_agent (default: audit)
Run a comprehensive security audit including vault status, leaked secrets scan, .gitignore coverage, and dependency checks.
Returns a security score (0-100) with letter grade and prioritized issue list.

~~~json
{
    "thoughts": [
        "The user wants a security check of the system",
        "I'll run the full security audit which covers vault, secrets, gitignore, and dependencies"
    ],
    "headline": "Running full security audit",
    "tool_name": "security_agent",
    "tool_args": {}
}
~~~

#### security_agent:vault
Manage the encrypted vault — list secrets, bootstrap migration from .env, audit health, store/delete keys.

##### Actions:
- `list` — List all encrypted secrets in the vault
- `bootstrap` — Auto-migrate .env secrets into encrypted vault
- `audit` — Detailed vault health audit (JSON)
- `store` — Store a new secret: requires `key` and `value`
- `delete` — Delete a secret: requires `key`

~~~json
{
    "thoughts": [
        "I need to check what secrets are currently encrypted in the vault"
    ],
    "headline": "Listing vault secrets",
    "tool_name": "security_agent:vault",
    "tool_args": {
        "action": "list"
    }
}
~~~

~~~json
{
    "thoughts": [
        "I need to migrate all .env secrets into the encrypted vault"
    ],
    "headline": "Bootstrapping vault migration",
    "tool_name": "security_agent:vault",
    "tool_args": {
        "action": "bootstrap"
    }
}
~~~

~~~json
{
    "thoughts": [
        "I need to store a new API key in the encrypted vault"
    ],
    "headline": "Storing secret in vault",
    "tool_name": "security_agent:vault",
    "tool_args": {
        "action": "store",
        "key": "NEW_API_KEY",
        "value": "sk-abc123..."
    }
}
~~~

#### security_agent:scan
Scan a directory for leaked secrets, hardcoded API keys, passwords, and tokens in source code.

##### Arguments:
- `path` — Directory to scan (default: current working directory)
- `max_files` — Maximum files to scan (default: 500)

~~~json
{
    "thoughts": [
        "I should scan the codebase for any accidentally committed secrets"
    ],
    "headline": "Scanning for leaked secrets",
    "tool_name": "security_agent:scan",
    "tool_args": {
        "path": ".",
        "max_files": 500
    }
}
~~~

#### security_agent:gitignore
Verify that .gitignore covers all required security patterns (vault keys, .env files, PEM certs, credentials).

~~~json
{
    "thoughts": [
        "I need to verify .gitignore covers all sensitive file patterns"
    ],
    "headline": "Checking .gitignore security coverage",
    "tool_name": "security_agent:gitignore",
    "tool_args": {}
}
~~~

#### security_agent:deps
Check dependencies for pinning status and suggest vulnerability scanning with `pip audit`.

~~~json
{
    "thoughts": [
        "I should check if our dependencies have known vulnerabilities"
    ],
    "headline": "Checking dependency security",
    "tool_name": "security_agent:deps",
    "tool_args": {}
}
~~~

#### security_agent:rotate
Check which vault secrets may need rotation based on age (default: 90 days).

##### Arguments:
- `max_age_days` — Rotation threshold in days (default: 90)

~~~json
{
    "thoughts": [
        "I should check if any API keys need to be rotated"
    ],
    "headline": "Checking secret rotation status",
    "tool_name": "security_agent:rotate",
    "tool_args": {
        "max_age_days": 90
    }
}
~~~

#### security_agent:report
Generate a full formatted security report (same as audit with full detail).

~~~json
{
    "thoughts": [
        "The user wants a complete security report"
    ],
    "headline": "Generating security report",
    "tool_name": "security_agent:report",
    "tool_args": {}
}
~~~

### Security Cron Schedule
The following security tasks run automatically:
- **Vault Audit** — Every 6 hours (*/6 hour)
- **Secret Leak Scan** — Daily at 4:00 AM
- **Full Security Report** — Daily at 6:00 AM
- **Secret Rotation Check** — Weekly on Sundays at 5:00 AM
