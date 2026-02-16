<div align="center">

> [![Built by The Pauli Effect](https://img.shields.io/badge/Built%20by-The%20Pauli%20Effect-blueviolet?style=for-the-badge)](https://github.com/executiveusa) [![Agent Fleet](https://img.shields.io/badge/Agent%20Fleet-v1.0-ff6b6b?style=for-the-badge)](https://github.com/executiveusa/dashboard-agent-swarm/blob/main/AGENTS.md) [![Run on Docker](https://img.shields.io/badge/Run%20on-Docker-2496ED?style=for-the-badge&logo=docker)](https://github.com/executiveusa/agent-zero-Fork#docker)
>
> **`AZ-001` · Root Orchestrator** — Part of the 17-agent Pauli Effect fleet

</div>

---

<div align="center">

# `Agent Zero`

<p align="center">
    <a href="https://trendshift.io/repositories/11745" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11745" alt="frdel%2Fagent-zero | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

[![Agent Zero Website](https://img.shields.io/badge/Website-agent--zero.ai-0A192F?style=for-the-badge&logo=vercel&logoColor=white)](https://agent-zero.ai) [![Thanks to Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-Thanks%20to%20Sponsors-FF69B4?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/agent0ai) [![Follow on X](https://img.shields.io/badge/X-Follow-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/Agent0ai) [![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/B8KZKNsPpj) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@AgentZeroFW) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jan-tomasek/) [![Follow on Warpcast](https://img.shields.io/badge/Warpcast-Follow-5A32F3?style=for-the-badge)](https://warpcast.com/agent-zero) 


## Documentation:

[Introduction](#a-personal-organic-agentic-framework-that-grows-and-learns-with-you) •
[Installation](./docs/installation.md) •
[Development](./docs/development.md) •
[Extensibility](./docs/extensibility.md) •
[Connectivity](./docs/connectivity.md) •
[How to update](./docs/installation.md#how-to-update-agent-zero) •
[Documentation](./docs/README.md) •
[Usage](./docs/usage.md)

Or see DeepWiki generated documentation:

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/agent0ai/agent-zero)

</div>


<div align="center">

> ### 🚨 **PROJECTS!** 🚨
Agent Zero now supports **Projects** – isolated workspaces with their own prompts, files, memory, and secrets, so you can create dedicated setups for each use case without mixing contexts.
</div>



[![Showcase](/docs/res/showcase-thumb.png)](https://youtu.be/MdzLhWWoxEs)



## A personal, organic agentic framework that grows and learns with you



- Agent Zero is not a predefined agentic framework. It is designed to be dynamic, organically growing, and learning as you use it.
- Agent Zero is fully transparent, readable, comprehensible, customizable, and interactive.
- Agent Zero uses the computer as a tool to accomplish its (your) tasks.

# 💡 Key Features

1. **General-purpose Assistant**

- Agent Zero is not pre-programmed for specific tasks (but can be). It is meant to be a general-purpose personal assistant. Give it a task, and it will gather information, execute commands and code, cooperate with other agent instances, and do its best to accomplish it.
- It has a persistent memory, allowing it to memorize previous solutions, code, facts, instructions, etc., to solve tasks faster and more reliably in the future.

![Agent 0 Working](/docs/res/ui-screen-2.png)

2. **Computer as a Tool**

- Agent Zero uses the operating system as a tool to accomplish its tasks. It has no single-purpose tools pre-programmed. Instead, it can write its own code and use the terminal to create and use its own tools as needed.
- The only default tools in its arsenal are online search, memory features, communication (with the user and other agents), and code/terminal execution. Everything else is created by the agent itself or can be extended by the user.
- Tool usage functionality has been developed from scratch to be the most compatible and reliable, even with very small models.
- **Default Tools:** Agent Zero includes tools like knowledge, code execution, and communication.
- **Creating Custom Tools:** Extend Agent Zero's functionality by creating your own custom tools.
- **Instruments:** Instruments are a new type of tool that allow you to create custom functions and procedures that can be called by Agent Zero.

3. **Multi-agent Cooperation**

- Every agent has a superior agent giving it tasks and instructions. Every agent then reports back to its superior.
- In the case of the first agent in the chain (Agent 0), the superior is the human user; the agent sees no difference.
- Every agent can create its subordinate agent to help break down and solve subtasks. This helps all agents keep their context clean and focused.

![Multi-agent](docs/res/physics.png)
![Multi-agent 2](docs/res/physics-2.png)

4. **Completely Customizable and Extensible**

- Almost nothing in this framework is hard-coded. Nothing is hidden. Everything can be extended or changed by the user.
- The whole behavior is defined by a system prompt in the **prompts/default/agent.system.md** file. Change this prompt and change the framework dramatically.
- The framework does not guide or limit the agent in any way. There are no hard-coded rails that agents have to follow.
- Every prompt, every small message template sent to the agent in its communication loop can be found in the **prompts/** folder and changed.
- Every default tool can be found in the **python/tools/** folder and changed or copied to create new predefined tools.

![Prompts](/docs/res/prompts.png)

5. **Communication is Key**

- Give your agent a proper system prompt and instructions, and it can do miracles.
- Agents can communicate with their superiors and subordinates, asking questions, giving instructions, and providing guidance. Instruct your agents in the system prompt on how to communicate effectively.
- The terminal interface is real-time streamed and interactive. You can stop and intervene at any point. If you see your agent heading in the wrong direction, just stop and tell it right away.
- There is a lot of freedom in this framework. You can instruct your agents to regularly report back to superiors asking for permission to continue. You can instruct them to use point-scoring systems when deciding when to delegate subtasks. Superiors can double-check subordinates' results and dispute. The possibilities are endless.

## 🚀 Things you can build with Agent Zero

- **Development Projects** - `"Create a React dashboard with real-time data visualization"`

- **Data Analysis** - `"Analyze last quarter's NVIDIA sales data and create trend reports"`

- **Content Creation** - `"Write a technical blog post about microservices"`

- **System Admin** - `"Set up a monitoring system for our web servers"`

- **Research** - `"Gather and summarize five recent AI papers about CoT prompting"`



# ⚙️ Installation

Click to open a video to learn how to install Agent Zero:

[![Easy Installation guide](/docs/res/easy_ins_vid.png)](https://www.youtube.com/watch?v=w5v5Kjx51hs)

A detailed setup guide for Windows, macOS, and Linux with a video can be found in the Agent Zero Documentation at [this page](./docs/installation.md).

### ⚡ Quick Start

```bash
# Pull and run with Docker

docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero

# Visit http://localhost:50001 to start
```

## 🐳 Fully Dockerized, with Speech-to-Text and TTS

![Settings](docs/res/settings-page-ui.png)

- Customizable settings allow users to tailor the agent's behavior and responses to their needs.
- The Web UI output is very clean, fluid, colorful, readable, and interactive; nothing is hidden.
- You can load or save chats directly within the Web UI.
- The same output you see in the terminal is automatically saved to an HTML file in **logs/** folder for every session.

![Time example](/docs/res/time_example.jpg)

- Agent output is streamed in real-time, allowing users to read along and intervene at any time.
- No coding is required; only prompting and communication skills are necessary.
- With a solid system prompt, the framework is reliable even with small models, including precise tool usage.

## 🚀 ARCHONX Configuration

Agent Zero now includes **ARCHONX** - an advanced configuration profile with enhanced capabilities for autonomous operations:

```bash
# Quick setup
python3 setup_archonx.py
```

ARCHONX provides:
- ✅ **Advanced Planning**: Strategic thinking and roadmap development
- ✅ **Autonomous Operation**: Self-directed task execution  
- ✅ **Multi-Agent Coordination**: Intelligent delegation and collaboration
- ✅ **Enhanced Security**: Vault-based credential management

📖 **[See the full ARCHONX Setup Guide](./ARCHONX_SETUP_GUIDE.md)** for detailed configuration options.

## 👀 Keep in Mind

1. **Agent Zero Can Be Dangerous!**

- With proper instruction, Agent Zero is capable of many things, even potentially dangerous actions concerning your computer, data, or accounts. Always run Agent Zero in an isolated environment (like Docker) and be careful what you wish for.

2. **Agent Zero Is Prompt-based.**

- The whole framework is guided by the **prompts/** folder. Agent guidelines, tool instructions, messages, utility AI functions, it's all there.


## 📚 Read the Documentation

| Page | Description |
|-------|-------------|
| [Installation](./docs/installation.md) | Installation, setup and configuration |
| [Usage](./docs/usage.md) | Basic and advanced usage |
| [Development](./docs/development.md) | Development and customization |
| [Extensibility](./docs/extensibility.md) | Extending Agent Zero |
| [Connectivity](./docs/connectivity.md) | External API endpoints, MCP server connections, A2A protocol |
| [Architecture](./docs/architecture.md) | System design and components |
| [Contributing](./docs/contribution.md) | How to contribute |
| [Troubleshooting](./docs/troubleshooting.md) | Common issues and their solutions |
| [Loveable.dev Testing Solutions](./LOVEABLE_SOLUTIONS_GUIDE.md) | Multiple deployment approaches for browser automation testing |


## 🎯 Changelog

### v0.9.7 - Projects
[Release video](https://youtu.be/RrTDp_v9V1c)
- Projects management
    - Support for custom instructions
    - Integration with memory, knowledge, files
    - Project specific secrets 
- New Welcome screen/Dashboard
- New Wait tool
- Subordinate agent configuration override support
- Support for multiple documents at once in document_query_tool
- Improved context on interventions
- Openrouter embedding support
- Frontend components refactor and polishing
- SSH metadata output fix
- Support for windows powershell in local TTY utility
- More efficient selective streaming for LLMs
- UI output length limit improvements



### v0.9.6 - Memory Dashboard
[Release video](https://youtu.be/sizjAq2-d9s)
- Memory Management Dashboard
- Kali update
- Python update + dual installation
- Browser Use update
- New login screen
- LiteLLM retry on temporary errors
- Github Copilot provider support


### v0.9.5 - Secrets
[Release video](https://www.youtube.com/watch?v=VqxUdt7pjd8)
- Secrets management - agent can use credentials without seeing them
- Agent can copy paste messages and files without rewriting them
- LiteLLM global configuration field
- Custom HTTP headers field for browser agent
- Progressive web app support
- Extra model params support for JSON
- Short IDs for files and memories to prevent LLM errors
- Tunnel component frontend rework
- Fix for timezone change bug
- Notifications z-index fix

### v0.9.4 - Connectivity, UI
[Release video](https://www.youtube.com/watch?v=C2BAdDOduIc)
- External API endpoints
- Streamable HTTP MCP A0 server
- A2A (Agent to Agent) protocol - server+client
- New notifications system
- New local terminal interface for stability
- Rate limiter integration to models
- Delayed memory recall
- Smarter autoscrolling in UI
- Action buttons in messages
- Multiple API keys support
- Download streaming
- Tunnel URL QR code
- Internal fixes and optimizations

### v0.9.3 - Subordinates, memory, providers Latest
[Release video](https://www.youtube.com/watch?v=-LfejFWL34k)
- Faster startup/restart
- Subordinate agents can have dedicated prompts, tools and system extensions
- Streamable HTTP MCP server support
- Memory loading enhanced by AI filter
- Memory AI consolidation when saving memories
- Auto memory system configuration in settings
- LLM providers available are set by providers.yaml configuration file
- Venice.ai LLM provider supported
- Initial agent message for user + as example for LLM
- Docker build support for local images
- File browser fix


### v0.9.2 - Kokoro TTS, Attachments
[Release video](https://www.youtube.com/watch?v=sPot_CAX62I)

- Kokoro text-to-speech integration
- New message attachments system
- Minor updates: log truncation, hyperlink targets, component examples, api cleanup


### v0.9.1 - LiteLLM, UI improvements
[Release video](https://youtu.be/crwr0M4Spcg)
- Langchain replaced with LiteLLM
    - Support for reasoning models streaming
    - Support for more providers
    - Openrouter set as default instead of OpenAI
- UI improvements
    - New message grouping system
    - Communication smoother and more efficient
    - Collapsible messages by type
    - Code execution tool output improved
    - Tables and code blocks scrollable
    - More space efficient on mobile
- Streamable HTTP MCP servers support
- LLM API URL added to models config for Azure, local and custom providers
    

### v0.9.0 - Agent roles, backup/restore
[Release video](https://www.youtube.com/watch?v=rMIe-TC6H-k)
- subordinate agents can use prompt profiles for different roles
- backup/restore functionality for easier upgrades
- security and bug fixes

### v0.8.7 - Formatting, Document RAG Latest
[Release video](https://youtu.be/OQJkfofYbus)
- markdown rendering in responses
- live response rendering
- document Q&A tool

### v0.8.6 - Merge and update
[Release video](https://youtu.be/l0qpK3Wt65A)
- Merge with Hacking Edition
- browser-use upgrade and integration re-work
- tunnel provider switch

### v0.8.5 - **MCP Server + Client**
[Release video](https://youtu.be/pM5f4Vz3_IQ)

- Agent Zero can now act as MCP Server
- Agent Zero can use external MCP servers as tools

### v0.8.4.1 - 2
Default models set to gpt-4.1
- Code execution tool improvements
- Browser agent improvements
- Memory improvements
- Various bugfixes related to context management
- Message formatting improvements
- Scheduler improvements
- New model provider
- Input tool fix
- Compatibility and stability improvements

### v0.8.4
[Release video](https://youtu.be/QBh_h_D_E24)

- **Remote access (mobile)**

### v0.8.3.1
[Release video](https://youtu.be/AGNpQ3_GxFQ)

- **Automatic embedding**


### v0.8.3
[Release video](https://youtu.be/bPIZo0poalY)

- ***Planning and scheduling***

### v0.8.2
[Release video](https://youtu.be/xMUNynQ9x6Y)

- **Multitasking in terminal**
- **Chat names**

### v0.8.1
[Release video](https://youtu.be/quv145buW74)

- **Browser Agent**
- **UX Improvements**

### v0.8
[Release video](https://youtu.be/cHDCCSr1YRI)

- **Docker Runtime**
- **New Messages History and Summarization System**
- **Agent Behavior Change and Management**
- **Text-to-Speech (TTS) and Speech-to-Text (STT)**
- **Settings Page in Web UI**
- **SearXNG Integration Replacing Perplexity + DuckDuckGo**
- **File Browser Functionality**
- **KaTeX Math Visualization Support**
- **In-chat File Attachments**

### v0.7
[Release video](https://youtu.be/U_Gl0NPalKA)

- **Automatic Memory**
- **UI Improvements**
- **Instruments**
- **Extensions Framework**
- **Reflection Prompts**
- **Bug Fixes**

## 🧪 Loveable.dev Testing Solutions

Agent Zero includes comprehensive solutions for testing Loveable.dev login credentials in various deployment environments:

### Available Solutions

| Solution | Environment | Best For | Link |
|----------|-------------|----------|------|
| Docker Containerization | Any system with Docker | Local development, CI/CD pipelines | [Dockerfile.loveable](./Dockerfile.loveable) |
| Hostinger VPS Direct | VPS with full network access | Production environments | [run_loveable_test_hostinger.sh](./deployment/run_loveable_test_hostinger.sh) |
| SSH Deployment Automation | VPS via SSH | Automated deployment workflows | [deploy_loveable_test.py](./deployment/deploy_loveable_test.py) |
| PyPuppeteer Alternative | Lightweight browser automation | Fallback when Playwright unavailable | [test_loveable_pyppeteer.py](./test_loveable_pyppeteer.py) |
| GitHub Actions | GitHub CI/CD | Scheduled or event-triggered testing | See [Solutions Guide](./LOVEABLE_SOLUTIONS_GUIDE.md) |
| AWS Lambda | Serverless compute | Cost-effective scalable testing | See [Solutions Guide](./LOVEABLE_SOLUTIONS_GUIDE.md) |
| Kubernetes | Container orchestration | Enterprise deployments | See [Solutions Guide](./LOVEABLE_SOLUTIONS_GUIDE.md) |

### Quick Start

```bash
# Using Docker (recommended for local testing)
docker build -f Dockerfile.loveable -t loveable-test:latest .
docker run -e EMAIL="user@example.com" \
           -e PASSWORD1="password1" \
           -e PASSWORD2="password2" \
           -v /tmp/results:/results \
           loveable-test:latest

# Results saved to /tmp/results/loveable_login_results.json
cat /tmp/results/loveable_login_results.json
```

### Features

✅ Tests both password attempts automatically
✅ Extracts first 10 projects from Loveable.dev account
✅ JSON output format for easy parsing
✅ Error handling and retry logic
✅ Support for multiple deployment environments
✅ Comprehensive troubleshooting guide

For complete documentation and troubleshooting, see [LOVEABLE_SOLUTIONS_GUIDE.md](./LOVEABLE_SOLUTIONS_GUIDE.md).

---

# 🦞 Agent Claw — Autonomous Agency Layer

**Agent Claw** is an autonomous agency layer built on top of Agent Zero, integrating multi-platform messaging (via OpenClaw/ClawdBot), voice control (SYNTHIA), swarm orchestration, and a React mobile dashboard.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Dashboard Agent Swarm               │
│        (Vite + React + shadcn/ui + Tailwind)         │
│         AgentClaw.tsx ← agentClawApi.ts              │
│              ↕ proxy: /agent-claw                    │
├─────────────────────────────────────────────────────┤
│                  Agent Zero (Flask :50001)            │
│  ┌──────────┬──────────┬──────────┬───────────┐      │
│  │ Voice    │ Venice   │ A2A Chat │ Swarm     │      │
│  │ Command  │ MCP      │ Tool     │ Orch.     │      │
│  └──────────┴──────────┴──────────┴───────────┘      │
│  ┌──────────────────────────────────────────────┐    │
│  │ OpenClaw WS Connector (ws://127.0.0.1:18789) │    │
│  │ → auto-reconnect, frame routing, handshake   │    │
│  └──────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────┐    │
│  │ SYNTHIA Voice Router (22 cmds, 9 categories) │    │
│  │ → fuzzy matching, slot extraction, bilingual │    │
│  └──────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│           OpenClaw Gateway (Node.js :18789)           │
│   WhatsApp · Telegram · Discord · Slack · Signal     │
│   Teams · iMessage · Voice · SMS · 7 more channels   │
└─────────────────────────────────────────────────────┘
```

## Agent Claw Components

### Sprint 1 — Core Integration Layer
| File | Purpose |
|------|---------|
| `python/tools/voice_notify.py` | ElevenLabs TTS + Twilio voice calls |
| `python/tools/venice_mcp.py` | Venice AI privacy-first LLM tool |
| `python/helpers/elevenlabs_client.py` | TTS client wrapper |
| `python/helpers/cron_bootstrap.py` | 5 default cron jobs (briefing, health, compaction, sync, backup) |
| `python/helpers/agent_lightning_integration.py` | AGL tracing (Linux) |
| `mcp_docker_server.js` | Node MCP server (6 tools, port 18800) |
| `prompts/default/agent.system.synthia.md` | SYNTHIA persona prompt |

### Sprint 1.5 — Voice Command System
| File | Purpose |
|------|---------|
| `python/helpers/voice_command_router.py` | 22 commands, 9 categories, fuzzy matching |
| `python/tools/voice_command.py` | Tool subclass wrapping the router |
| `prompts/agent.system.tool.voice_command.md` | Command vocabulary prompt |

### Sprint 2 — Dashboard & Deployment
| File | Purpose |
|------|---------|
| `webui/js/master-dashboard/synthia-voice.js` | Mic, STT, command history panel |
| `webui/js/master-dashboard/cron-panel.js` | Cron job CRUD panel |
| `webui/css/synthia-panels.css` | Panel styling |
| `python/api/voice_command_route.py` | REST endpoint for voice commands |
| `python/api/voice_command_help.py` | REST endpoint for command help |
| `docker-compose.prod.yml` | Production Coolify deployment (5 services) |
| `Dockerfile.agent` | Agent Zero container image |
| `coolify.json` | Coolify environment config |

### Phase 4 — OpenClaw Bridge
| File | Purpose |
|------|---------|
| `python/helpers/openclaw_ws_connector.py` | WebSocket bridge with auto-reconnect, frame routing |

### Phase 7 — Security
| File | Purpose |
|------|---------|
| `python/helpers/api_rate_limit.py` | Per-IP rate limiting (burst/min/hr) + API key auth + rotation |

### Phase 8-9 — Testing & Polish
| File | Purpose |
|------|---------|
| `tests/test_agent_claw.py` | 33-test integration suite (all passing) |
| `python/helpers/startup_validator.py` | Pre-flight checks for all Agent Claw components |

### Modified Existing Files
| File | Changes |
|------|---------|
| `initialize.py` | Added `initialize_crons()`, `initialize_agent_lightning()`, `initialize_openclaw()`, `validate_agent_claw()` |
| `run_ui.py` | Wired all 4 Agent Claw init functions into startup |
| `requirements.txt` | Added `websockets>=12.0`, `requests>=2.31.0`, `agentlightning[apo]` (Linux) |
| `conf/model_providers.yaml` | Venice AI provider config |
| `webui/master-dashboard.html` | Rebranded "Agent Claw — SYNTHIA Control", added panels |
| `webui/js/master-dashboard/main.js` | Wired SYNTHIA + cron panels |

## Dashboard (Separate Repo)

The React mobile dashboard lives at `github.com/executiveusa/dashboard-agent-swarm`:
- `src/pages/AgentClaw.tsx` — Full SYNTHIA control page
- `src/services/agentClawApi.ts` — Typed API service (health, poll, message, scheduler, voice)
- `src/components/AppSidebar.tsx` — Agent Claw nav entry
- `src/App.tsx` — Route at `/agent-claw`
- `vite.config.ts` — Proxy to `localhost:50001`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ELEVENLABS_API_KEY` | Optional | ElevenLabs TTS/voice calls |
| `VENICE_API_KEY` | Optional | Venice AI privacy LLM |
| `OPENCLAW_WS_URL` | Optional | OpenClaw gateway (default: `ws://127.0.0.1:18789`) |
| `AGENT_CLAW_API_KEYS` | Optional | Comma-separated API keys for external access |

## Running Tests

```bash
cd agent-zero-Fork
python tests/test_agent_claw.py  # 33 tests, ~0.5s
```

## Coolify Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🤝 Community and Support

- [Join our Discord](https://discord.gg/B8KZKNsPpj) for live discussions or [visit our Skool Community](https://www.skool.com/agent-zero).
- [Follow our YouTube channel](https://www.youtube.com/@AgentZeroFW) for hands-on explanations and tutorials
- [Report Issues](https://github.com/agent0ai/agent-zero/issues) for bug fixes and features
