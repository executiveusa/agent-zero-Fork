# 🧠 ArchonX OS Ecosystem - Complete Architecture

## Executive Summary

This document describes the complete integration architecture for the ArchonX OS ecosystem, where:

- **ArchonX OS** = Main brain/kernel managing the entire ecosystem
- **Agent Zero** = Primary orchestration agent (powered by Composio framework)
- **Dashboard Agent Swarm** = Web UI for control and monitoring (FlowWise-based)
- **PersonapleX Voice** = Multilingual voice I/O (Spanish/English)
- **MCP Servers** = Data access layer (BrightData + FireCrawl, CLI mode)
- **Microsoft Lightning Agent** = Monitoring and continuous improvement
- **Supabase (Self-hosted)** = Persistent memory database

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACES                             │
├─────────────────────────────────────────────────────────────────────┤
│  📱 Telegram Bot  │  🌐 Dashboard (FlowWise)  │  🎤 Voice (Personaplex)
└───────────┬─────────────────┬──────────────────────┬────────────────┘
            │                 │                      │
            ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT ZERO                                   │
│                  (Primary Orchestration Layer)                       │
│                   Based on Composio Framework                        │
├─────────────────────────────────────────────────────────────────────┤
│  • Receives user commands from all interfaces                        │
│  • Delegates tasks to specialized agents                             │
│  • Coordinates workflow execution                                    │
│  • Reports back to user via appropriate interface                    │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ARCHONX OS BRAIN                             │
│                    (Kernel / Operating System)                       │
├─────────────────────────────────────────────────────────────────────┤
│  • Graph Memory: Tracks connections across all repos                │
│  • Cron Jobs: Nightly improvement scans                             │
│  • CLI Tools Manager: Gemini CLI, Claude CLI, etc.                  │
│  • Resource Optimizer: Minimizes token usage                        │
│  • Repository Manager: Monitors all executiveusa/* repos            │
└─────┬───────────────┬─────────────┬──────────────┬─────────────────┘
      │               │             │              │
      ▼               ▼             ▼              ▼
┌──────────┐  ┌────────────┐  ┌───────────┐  ┌──────────────┐
│  GitHub  │  │ MCP Server │  │ Supabase  │  │  Lightning   │
│  Repos   │  │   Layer    │  │ (Memory)  │  │   Monitor    │
│  Graph   │  │            │  │           │  │              │
└──────────┘  └────────────┘  └───────────┘  └──────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
  ┌─────────────┐      ┌──────────────┐
  │ BrightData  │      │  FireCrawl   │
  │  (CLI Mode) │      │  (CLI Mode)  │
  └─────────────┘      └──────────────┘
```

---

## 🔄 Data Flow

### 1. User Request Flow

```
User → Interface (Telegram/Dashboard/Voice)
         ↓
      Agent Zero
         ↓
      ArchonX OS Brain
         ↓
    Execute via:
    - CLI Tools (Gemini CLI, Claude CLI)
    - MCP Servers (BrightData, FireCrawl)
    - GitHub APIs
    - Supabase Memory
         ↓
      Results
         ↓
      Agent Zero
         ↓
      User Interface
```

### 2. Background Processing Flow

```
ArchonX OS Cron Job (Nightly)
         ↓
Scan all executiveusa/* repos
         ↓
Identify improvement opportunities:
  - Code quality issues
  - Missing documentation
  - Outdated dependencies
  - Integration opportunities
         ↓
Create tasks in Agent Zero queue
         ↓
Agent Zero processes overnight
         ↓
Store results in Supabase
         ↓
Report to Dashboard (morning)
```

---

## 🧩 Component Details

### 1. ArchonX OS (Main Brain)

**Repository**: `git@github.com:executiveusa/archonx-os.git`

**Purpose**: Central intelligence and coordination system

**Key Features**:
- **Graph Memory**: Maintains relationship graph of all repos
- **CLI Tools Manager**: Orchestrates Gemini CLI, Claude CLI, etc.
- **Cron Scheduler**: Runs nightly improvement scans
- **Resource Optimizer**: Minimizes API costs via CLI tools
- **Repository Monitor**: Tracks all executiveusa GitHub repos

**Technology Stack**:
- Python 3.11+
- NetworkX (graph database)
- Supabase (persistent storage)
- Celery (background tasks)
- Redis (task queue)

**APIs Exposed**:
- `POST /api/v1/repos/scan` - Scan repository for insights
- `GET /api/v1/graph/connections` - Get repo connections
- `POST /api/v1/tasks/schedule` - Schedule background task
- `GET /api/v1/insights/{repo}` - Get repo insights
- `POST /api/v1/improve/{repo}` - Trigger improvements

---

### 2. Agent Zero (Orchestration Agent)

**Repository**: `https://github.com/executiveusa/agent-zero-Fork.git`

**Purpose**: Primary orchestration layer, handles all user requests

**Based On**: Composio Agent Orchestrator framework

**Key Features**:
- Multi-agent delegation
- Workflow management
- Context preservation
- Tool integration
- Voice/text/dashboard interfaces

**Communication Channels**:
- REST API (port 8001)
- WebSocket (real-time updates)
- Telegram Bot API
- Voice interface (via PersonapleX)

**Integration Points**:
- ↕️ ArchonX OS (brain)
- ↕️ Dashboard Agent Swarm (UI)
- ↕️ PersonapleX Voice (audio)
- ↕️ MCP Servers (data)
- ↕️ Supabase (memory)
- ↕️ Lightning Agent (monitoring)

---

### 3. Dashboard Agent Swarm (Web UI)

**Repository**: `git@github.com:executiveusa/dashboard-agent-swarm.git`

**Purpose**: Visual control center and monitoring interface

**Technology**: FlowWise-based visual workflow builder

**Key Features**:
- Real-time agent status
- Task management
- Workflow visualization
- Performance metrics
- Log viewing
- Manual task creation

**Connection to Agent Zero**:
```javascript
// Dashboard → Agent Zero API
const response = await fetch('http://agent-zero:8001/api/task/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${AGENT_ZERO_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    task: 'Analyze repository for improvements',
    repo: 'executiveusa/project-x',
    priority: 'high'
  })
});
```

**WebSocket for Real-time Updates**:
```javascript
const ws = new WebSocket('ws://agent-zero:8001/ws');
ws.on('message', (data) => {
  // Update dashboard with agent status
  updateDashboard(JSON.parse(data));
});
```

---

### 4. PersonapleX Voice (Multilingual Voice I/O)

**Repository**: `https://github.com/NVIDIA/personaplex.git`

**Purpose**: Natural voice interaction in Spanish and English

**Features**:
- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Language detection
- Emotional tone
- Natural conversations

**Integration**:
```python
# Agent Zero → PersonapleX Voice
from personaplex import VoiceAgent

voice = VoiceAgent(
    languages=['es-MX', 'en-US'],
    tts_model='nvidia/parakeet-tdt-1.1b'
)

# Listen for user input
transcription = voice.listen(language='auto')

# Send to Agent Zero
response = agent_zero.process(transcription)

# Speak response
voice.speak(response, language='es-MX' if is_spanish else 'en-US')
```

**Voice Models**:
- **Spanish**: `es-MX-DaliaNeural` (Azure) or NVIDIA Parakeet
- **English**: `en-US-JennyNeural` (Azure) or NVIDIA Parakeet

---

### 5. MCP Servers (Data Access Layer)

#### 5.1 BrightData MCP Server

**Repository**: `git@github.com:executiveusa/pauli-brightdata-mcp.git`

**Purpose**: Web scraping and data collection via BrightData proxies

**CLI Mode** (Cost Optimized):
```bash
# Instead of MCP protocol (token-heavy), use CLI
brightdata-cli scrape \
  --url "https://example.com" \
  --proxy-zone "residential_proxy_1" \
  --output json \
  --customer-id "$BRIGHTDATA_CUSTOMER_ID"
```

**Integration with Agent Zero**:
```python
import subprocess
import json

def scrape_website(url: str) -> dict:
    result = subprocess.run([
        'brightdata-cli', 'scrape',
        '--url', url,
        '--output', 'json'
    ], capture_output=True, text=True)

    return json.loads(result.stdout)
```

#### 5.2 FireCrawl MCP Server

**Repository**: `https://github.com/firecrawl/firecrawl-mcp-server.git`

**Purpose**: Advanced web crawling and content extraction

**CLI Mode**:
```bash
# Use FireCrawl CLI instead of MCP
firecrawl crawl \
  --url "https://docs.example.com" \
  --depth 3 \
  --extract-markdown \
  --output-dir ./output
```

---

### 6. Composio Agent Orchestrator

**Repository**: `https://github.com/ComposioHQ/agent-orchestrator.git`

**Purpose**: Framework for Agent Zero's orchestration capabilities

**Key Features**:
- Multi-agent coordination
- Task delegation
- Parallel execution
- Context sharing
- Tool integration

**Integration**:
```python
from composio_agent_orchestrator import Orchestrator, Agent

# Initialize orchestrator
orchestrator = Orchestrator(
    brain=archonx_os,  # Connect to ArchonX OS
    memory=supabase,    # Persistent storage
    monitoring=lightning_agent
)

# Register agents
orchestrator.register_agent(
    Agent(name='coder', skills=['python', 'javascript'])
)
orchestrator.register_agent(
    Agent(name='researcher', skills=['web-search', 'analysis'])
)

# Delegate task
result = orchestrator.delegate_task(
    task='Build new feature',
    strategy='parallel'  # Run agents in parallel
)
```

---

### 7. Microsoft Lightning Agent (Monitoring)

**Purpose**: Continuous monitoring and improvement

**Features**:
- Performance metrics
- Error tracking
- Usage analytics
- Automatic optimization
- Anomaly detection

**Integration**:
```python
from lightning_agent import Monitor

monitor = Monitor(
    workspace_id=LIGHTNING_WORKSPACE_ID,
    api_key=LIGHTNING_API_KEY
)

# Track agent execution
with monitor.track('agent_execution'):
    result = agent_zero.execute_task(task)

# Get insights
insights = monitor.get_insights(
    metric='response_time',
    period='24h'
)

# Auto-optimize based on insights
if insights['avg_response_time'] > 5000:  # ms
    monitor.recommend_optimizations()
```

---

### 8. Supabase (Self-Hosted Persistent Memory)

**Purpose**: Long-term memory and data persistence

**Features**:
- PostgreSQL database
- Real-time subscriptions
- RESTful API
- GraphQL support
- Row-level security

**Schema Design**:
```sql
-- Agent conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    input TEXT,
    output TEXT,
    agent_id TEXT,
    metadata JSONB
);

-- Repository insights
CREATE TABLE repo_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_name TEXT NOT NULL,
    scan_date TIMESTAMPTZ DEFAULT NOW(),
    insights JSONB,
    improvement_suggestions JSONB,
    connections JSONB
);

-- Task queue
CREATE TABLE task_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type TEXT NOT NULL,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_for TIMESTAMPTZ,
    payload JSONB
);

-- Agent performance metrics
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔗 Integration Points & Webhooks

### 1. ArchonX OS ↔ Agent Zero

**Webhook URL**: `https://agent-zero.yourdomain.com/webhooks/archonx`

**Trigger**: When ArchonX OS identifies improvement opportunity

```json
POST /webhooks/archonx
{
  "event": "improvement_found",
  "repo": "executiveusa/project-x",
  "insights": {
    "type": "code_quality",
    "severity": "medium",
    "description": "Outdated dependencies found",
    "suggested_action": "Update npm packages"
  }
}
```

**Agent Zero Response**:
```json
{
  "status": "accepted",
  "task_id": "task_123456",
  "estimated_completion": "2024-03-04T02:00:00Z"
}
```

---

### 2. Agent Zero ↔ Dashboard

**WebSocket Connection**: `wss://agent-zero.yourdomain.com/ws/dashboard`

**Real-time Events**:
```javascript
{
  "event": "task_started",
  "task_id": "task_123456",
  "agent": "coder",
  "description": "Updating dependencies in project-x"
}

{
  "event": "task_progress",
  "task_id": "task_123456",
  "progress": 45,
  "current_step": "Running tests"
}

{
  "event": "task_completed",
  "task_id": "task_123456",
  "result": "success",
  "output": "All dependencies updated, tests passing"
}
```

---

### 3. Dashboard ↔ User

**REST API**: `https://dashboard.yourdomain.com/api/v1`

**Endpoints**:
- `GET /api/v1/agents/status` - Get all agent statuses
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks/create` - Create new task
- `GET /api/v1/metrics` - Get performance metrics
- `POST /api/v1/repos/scan` - Trigger repo scan

---

### 4. GitHub → ArchonX OS

**Webhook URL**: `https://archonx.yourdomain.com/webhooks/github`

**Events**:
- `push` - Code pushed to repo
- `pull_request` - PR opened/merged
- `issues` - Issue created/closed
- `release` - New release published

```json
POST /webhooks/github
{
  "event": "push",
  "repo": "executiveusa/project-x",
  "branch": "main",
  "commits": [
    {
      "message": "feat: add new feature",
      "author": "user@example.com"
    }
  ]
}
```

**ArchonX OS Action**:
1. Update repository graph
2. Analyze changes for impact
3. Check for issues/opportunities
4. Queue tasks if needed

---

## 🚀 Deployment Architecture

### Hostinger VPS Setup

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hostinger VPS (Ubuntu)                        │
│                          (4-8GB RAM)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  ArchonX OS  │  │ Agent Zero   │  │  Dashboard   │          │
│  │  Port: 9000  │  │  Port: 8001  │  │  Port: 3000  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Supabase    │  │    Redis     │  │PersonapleX   │          │
│  │  Port: 5432  │  │  Port: 6379  │  │  Port: 8080  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │              Nginx Reverse Proxy                 │          │
│  │                  Port: 80/443                     │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Docker Compose Structure

```yaml
version: '3.9'

services:
  archonx-os:
    build: ./archonx-os
    ports:
      - "9000:9000"
    environment:
      - SUPABASE_URL=http://supabase:8000
      - REDIS_URL=redis://redis:6379
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    depends_on:
      - supabase
      - redis

  agent-zero:
    build: ./agent-zero
    ports:
      - "8001:8001"
    environment:
      - ARCHONX_URL=http://archonx-os:9000
      - GEMINI_CLI_ENABLED=true
    depends_on:
      - archonx-os

  dashboard:
    build: ./dashboard-agent-swarm
    ports:
      - "3000:3000"
    environment:
      - AGENT_ZERO_URL=http://agent-zero:8001
      - FLOWISE_USERNAME=${FLOWISE_USERNAME}
      - FLOWISE_PASSWORD=${FLOWISE_PASSWORD}

  personaplex:
    build: ./personaplex
    ports:
      - "8080:8080"
    environment:
      - AGENT_ZERO_URL=http://agent-zero:8001

  supabase:
    image: supabase/postgres:latest
    ports:
      - "5432:5432"
    volumes:
      - supabase-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt

volumes:
  supabase-data:
```

---

## 💡 Cost Optimization Strategy

### CLI Tools vs MCP Servers

**Problem**: MCP servers can be token-heavy and expensive

**Solution**: Use CLI tools wherever possible

| Service | MCP Server Cost | CLI Tool Cost | Savings |
|---------|----------------|---------------|---------|
| Gemini | $X per 1M tokens | FREE (OAuth) | 100% |
| Claude | $3-15 per 1M tokens | $3-15 per 1M tokens | 0% |
| BrightData | Context overhead | Direct API | ~30% |
| FireCrawl | Context overhead | Direct CLI | ~30% |

**Implementation**:
```python
# BEFORE (MCP - Token Heavy)
from mcp import BrightDataServer
data = await brightdata_server.scrape(url)  # Sends full context

# AFTER (CLI - Lightweight)
import subprocess
result = subprocess.run(['brightdata-cli', 'scrape', url])
data = json.loads(result.stdout)  # No context overhead
```

---

## 📊 Monitoring & Analytics

### Microsoft Lightning Agent Integration

```python
# In every agent operation
from lightning_agent import track

@track(name='agent_task', category='orchestration')
def execute_task(task):
    # Lightning automatically tracks:
    # - Execution time
    # - Resource usage
    # - Success/failure
    # - Error traces
    return process_task(task)

# View insights in Lightning dashboard
# lightning.microsoft.com/workspace/{WORKSPACE_ID}
```

### Metrics Tracked

- **Performance**: Response time, throughput, latency
- **Reliability**: Success rate, error rate, uptime
- **Cost**: API calls, token usage, compute time
- **Usage**: Tasks per day, users, popular features

---

## 🔄 Cron Jobs (Nightly Improvements)

### ArchonX OS Scheduler

```python
# archonx_os/scheduler.py

from celery import Celery
from celery.schedules import crontab

app = Celery('archonx-scheduler')

# Every night at 2 AM
@app.task
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Scan all repos
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        scan_all_repos.s(),
        name='nightly-repo-scan'
    )

    # Generate improvement suggestions
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        generate_improvements.s(),
        name='nightly-improvements'
    )

@app.task
def scan_all_repos():
    repos = github.get_organization_repos('executiveusa')

    for repo in repos:
        insights = analyze_repo(repo)
        store_insights(repo, insights)

        if insights['opportunities']:
            create_agent_zero_tasks(insights['opportunities'])

@app.task
def generate_improvements():
    insights = get_all_insights()

    # Use ArchonX graph memory to find connections
    improvements = archonx.graph.suggest_improvements(insights)

    for improvement in improvements:
        agent_zero.create_task(improvement)
```

### Example Nightly Flow

```
2:00 AM - Scan all executiveusa/* repos
          ├─ Check for outdated dependencies
          ├─ Analyze code quality
          ├─ Check documentation completeness
          └─ Identify integration opportunities

3:00 AM - Generate improvement suggestions
          ├─ Create Agent Zero tasks
          ├─ Prioritize by impact
          └─ Schedule for execution

4:00 AM - Agent Zero begins processing
          ├─ Update dependencies
          ├─ Fix linting issues
          ├─ Generate documentation
          └─ Create PRs

6:00 AM - Morning report ready
          └─ Dashboard shows overnight improvements
```

---

## 🔐 Security Considerations

### 1. Secrets Management

- All secrets encrypted with Age/GPG
- Never commit unencrypted secrets
- Use environment variables
- Rotate secrets every 90 days

### 2. API Authentication

```python
# All APIs require authentication
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/task/create")
async def create_task(
    token: str = Security(security),
    task: TaskCreate
):
    if not validate_token(token):
        raise HTTPException(401, "Invalid token")

    return agent_zero.create_task(task)
```

### 3. Network Security

- All services behind nginx reverse proxy
- SSL/TLS for all external connections
- Firewall rules (ufw)
- Rate limiting
- DDoS protection (Cloudflare)

---

## 🎯 Next Steps

### Phase 1: Foundation (Week 1)
1. ✅ Setup secrets management
2. ⏳ Clone all repositories
3. ⏳ Deploy Supabase (self-hosted)
4. ⏳ Deploy ArchonX OS brain
5. ⏳ Setup Redis task queue

### Phase 2: Core Integration (Week 2)
1. ⏳ Integrate Composio framework into Agent Zero
2. ⏳ Connect Agent Zero to ArchonX OS
3. ⏳ Setup CLI tools (Gemini CLI, Claude CLI)
4. ⏳ Integrate MCP servers (CLI mode)
5. ⏳ Setup Microsoft Lightning monitoring

### Phase 3: UI & Voice (Week 3)
1. ⏳ Deploy Dashboard Agent Swarm
2. ⏳ Connect Dashboard to Agent Zero
3. ⏳ Integrate PersonapleX voice
4. ⏳ Setup Telegram bot
5. ⏳ Configure webhooks

### Phase 4: Automation (Week 4)
1. ⏳ Setup cron jobs in ArchonX OS
2. ⏳ Implement repository graph
3. ⏳ Configure nightly scans
4. ⏳ Setup automated improvements
5. ⏳ Deploy to production

---

## 📞 Providing SSH Access (Secure Method)

### Option 1: Temporary SSH Key

```bash
# On your Hostinger VPS
ssh-keygen -t ed25519 -f /tmp/claude-deploy-key -N ""

# Add to authorized_keys
cat /tmp/claude-deploy-key.pub >> ~/.ssh/authorized_keys

# Share the private key (encrypted!)
./encrypt-secrets.sh /tmp/claude-deploy-key
# This creates /tmp/claude-deploy-key.encrypted.age

# Provide to Claude:
# - Encrypted private key
# - Server IP
# - Username (root)
# - Port (22 or custom)

# AFTER deployment, remove the key:
sed -i '/claude-deploy-key/d' ~/.ssh/authorized_keys
rm /tmp/claude-deploy-key*
```

### Option 2: SSH Config

```bash
# Create ~/.ssh/config entry
Host archonx-vps
    HostName YOUR_VPS_IP
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

---

## 📝 Configuration Checklist

Before deployment, ensure you have:

- [ ] Filled in `secrets.json` with all credentials
- [ ] Encrypted secrets file
- [ ] Backed up encryption keys
- [ ] SSH access to Hostinger VPS
- [ ] Domain names (if using)
- [ ] GitHub tokens
- [ ] BrightData API credentials
- [ ] FireCrawl API credentials
- [ ] Gemini CLI setup (OAuth)
- [ ] Microsoft Lightning Agent workspace
- [ ] Telegram bot token
- [ ] Voice API keys (if using premium voices)

---

## 🆘 Support

For issues during deployment:

1. Check this architecture document
2. Review component READMEs
3. Check logs: `docker-compose logs -f`
4. Contact: archonx@executiveusa.com

---

**Status**: Architecture designed, ready for implementation
**Next**: Await SSH credentials to begin deployment
