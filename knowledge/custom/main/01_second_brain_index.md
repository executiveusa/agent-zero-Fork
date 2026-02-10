# Second Brain Index — Agent Zero Knowledge Map

> This file maps all knowledge sources Agent Zero can access.
> Updated: 2026-02-10

---

## 1. Local File System (E: Drive Pipeline)

```
E:\ACTIVE PROJECTS-PIPELINE\ACTIVE PROJECTS-PIPELINE\AGENT ZERO\
├── master.env              # Environment secrets (DO NOT READ — use vault_get())
├── memory/
│   ├── beads/              # Steve Yegge's beads — git-backed issue tracking (Go)
│   │   ├── cmd/bd/         # bd CLI source
│   │   ├── pkg/            # Core packages (config, issue, repo, graph)
│   │   └── README.md       # Beads documentation
│   └── beads_integration.py  # Python wrapper for beads CLI
├── gastown/                # Steve Yegge's multi-agent orchestration (Go)
│   ├── cmd/gt/             # gt CLI source  
│   ├── pkg/                # Mayor, Rigs, Polecats, Hooks, Convoys
│   └── README.md           # Gastown docs
├── mcp_agent_mail/         # MCP Agent Mail — full mail system
│   ├── src/                # TypeScript source (identities, inbox, threads)
│   ├── web/                # Web UI for mail
│   └── README.md           # Agent Mail documentation
├── docker-compose.prod.yml # Production Docker stack (6 services)
├── .github/workflows/      # CI/CD GitHub Actions
└── Dockerfile              # Agent Zero container definition
```

## 2. Agent Zero Fork (C:\Users\execu\agent-zero-Fork\)

```
python/
├── helpers/
│   ├── vault.py            # Fernet AES-256 encrypted secret storage
│   ├── telegram_bot.py     # Telegram bot for @Pauli_the_paulibot
│   ├── secret_interceptor.py  # Auto-detect secrets in text streams
│   ├── security_hardening.py  # Anti-hack, anti-scrape protection
│   ├── cron_bootstrap.py   # 12 recurring cron jobs
│   ├── voice_ai.py         # Twilio voice pipeline
│   ├── mcp_agent_mail_bridge.py  # Bridge MCP Agent Mail ↔ A2A
│   └── ...
├── tools/
│   ├── agent_meeting.py    # Meeting convene/discuss/minutes
│   ├── beads_tool.py       # Beads task management tool
│   ├── a2a_agent_mail.py   # A2A protocol + routing
│   ├── notion_integration.py  # Notion CRUD + meeting DB
│   ├── swarm_orchestrator.py  # Parallel agent swarm execution
│   ├── call_subordinate.py # Core agent delegation
│   └── ...
├── knowledge/custom/main/
│   ├── 00_prime_goal.md    # THIS — prime directive
│   ├── 01_second_brain_index.md  # THIS — knowledge map
│   ├── agents.md           # Agent roles + meeting protocol
│   └── chat.md             # Meeting transcripts
└── secure/.vault/          # Encrypted secrets (35+ .enc files)
```

## 3. Notion Workspace ("Moltbook")

Databases created via API:
- **Meeting DB** — All meeting records with type, date, attendees, decisions
- **Goal Tracker** — Revenue milestones, task ownership, due dates, status
- **Watercooler** — Informal notes, ideas, cross-agent observations

Access: `notion_integration.py` → `vault_get("NOTION_API_TOKEN")`

## 4. External Services

| Service | Purpose | Credential Location |
|---------|---------|-------------------|
| Anthropic | Claude LLM | vault: anthropic_api_key |
| OpenAI | GPT models | vault: openai_api_key |
| Google | Gemini models | vault: google_api_key |
| Twilio | Voice calls + SMS | vault: twilio_* |
| Telegram | Bot messaging | vault: telegram_bot_token |
| Stripe | Payment processing | vault: stripe_secret_key |
| Supabase | Database + auth | vault: supabase_* |
| Coolify | Deployment | vault: coolify_api_token |
| Vercel | Frontend hosting | vault: vercel_token |
| GitHub | Code repos | vault: gh_pat |
| Cloudflare | DNS + tunnels | vault: cloudflare_* |
| HuggingFace | ML models | vault: huggingface_token |

## 5. How to Access Knowledge

```python
# Read vault secrets
from python.helpers.vault import vault_get
api_key = vault_get("ANTHROPIC_API_KEY")

# Query Notion
from python.tools.notion_integration import NotionIntegration
notion = NotionIntegration()
notion.query_notion_database(database_id="...", filter_condition={...})

# Check beads tasks
from python.tools.beads_tool import BeadsTool
# Use via tool system: beads_tool:ready, beads_tool:create, etc.

# Read local files
# Agent Zero has file system access via shell tools
```
