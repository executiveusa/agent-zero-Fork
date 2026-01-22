# 📚 Agent Zero - Skills Reference Documentation

**Complete skill documentation for all agents in the Agent Zero ecosystem.**

---

## Table of Contents

1. [Agent Capabilities](#agent-capabilities)
2. [Design Skills](#design-skills)
3. [Development Skills](#development-skills)
4. [Operational Skills](#operational-skills)
5. [Available Tools](#available-tools)
6. [Skill Rules & Constraints](#skill-rules--constraints)
7. [Anti-Patterns](#anti-patterns)
8. [Integration Points](#integration-points)

---

## Agent Capabilities

### ClaudeCode (MASTER) 🧠

**Type:** Long-Running Development Agent  
**Model:** Claude 3.5 Sonnet (Extended Context)  
**Cycle Time:** 30+ minutes  
**Concurrency:** Single-threaded, sequential tasks  
**Memory:** Byte Rover state persistence  

**Core Capabilities:**
- ✅ Full-stack architecture design
- ✅ Complex code refactoring
- ✅ Multi-phase project builds
- ✅ Database schema design & migration
- ✅ Security hardening & code review
- ✅ Performance optimization
- ✅ Documentation generation
- ✅ Test suite creation

**Skill Domains:**
- React/Next.js/Vue advanced patterns
- Python/Node.js backend development
- Docker/Kubernetes orchestration
- PostgreSQL advanced queries
- API design (REST, GraphQL)
- TypeScript advanced typing
- System architecture
- Code quality & testing

**Integration:** 
- Reads task from `/memory/tasks/current-task.json`
- Updates status in `/memory/orchestrator/state.json`
- Outputs code to `/workspace`
- Logs to `/logs/claudecode.log`

**When to Use:**
- "Build a complete SaaS application"
- "Refactor our entire frontend architecture"
- "Design and implement a new microservice"
- "Create a comprehensive testing strategy"

---

### Cynthia (DESIGNER) 🎨

**Type:** Design & Frontend Architecture Agent  
**Model:** GLM-4-7 (Google)  
**Cycle Time:** 2-30 minutes  
**Concurrency:** Can handle multiple design tasks  
**Specialization:** UI/UX, Design Systems, Frontend  

**Core Capabilities:**
- ✅ Design system generation (100 industry rules)
- ✅ Landing page architecture
- ✅ Component library design
- ✅ Color palette selection (95 options)
- ✅ Typography pairing (56 combinations)
- ✅ UI style selection (57 styles)
- ✅ Accessibility auditing (WCAG AA)
- ✅ Responsive design strategy
- ✅ Animation & micro-interactions
- ✅ Visual hierarchy optimization

**Skill Domains:**
- UI/UX Pro Max integration (see below)
- Design tokens & CSS variables
- Shadcn/ui component patterns
- Tailwind CSS best practices
- Figma/design tool workflows
- Brand guidelines creation
- Design system persistence (Master + Overrides)
- Accessibility standards (WCAG AA/AAA)

**Design System Capabilities:**
```
Input: "Build a landing page for a beauty spa"
↓
Design System Generated:
├── Pattern: Hero-Centric + Social Proof
├── Style: Soft UI Evolution
├── Colors: 5-7 semantic roles (95 palettes)
├── Typography: Curated pairs (56 fonts)
├── Layout: 24 proven patterns
├── Effects: Animations (200-300ms)
└── Checklist: Pre-delivery validation
```

**UI/UX Pro Max Features:**
- 57 UI Styles (Glassmorphism, Claymorphism, Minimalism, etc.)
- 95 Color Palettes (industry-specific)
- 56 Font Pairings (Google Fonts curated)
- 24 Chart Types (dashboard recommendations)
- 100 Reasoning Rules (industry-specific generation)
- 98 UX Guidelines (best practices + anti-patterns)

**Integration:**
- Reads design requirements from `/memory/tasks`
- Uses `design-system-specification.json` as reference
- Outputs Figma links or React components
- References `DESIGN_SYSTEM.md` and `COMPONENT_LIBRARY.md`

**When to Use:**
- "Design a modern SaaS dashboard"
- "Create a landing page for our new product"
- "Build a design system for our brand"
- "Make our site more accessible"
- "Improve our mobile UI/UX"

---

### Switchblade (TACTICAL) 🗡️

**Type:** Quick-Response Operations Agent  
**Model:** Claude 3.5 Sonnet (Optimized for Speed)  
**Cycle Time:** < 2 minutes  
**Concurrency:** Multi-threaded, parallel tasks  
**Integration:** VS Code, PowerShell, Docker  

**Core Capabilities:**
- ✅ Container spawn & management
- ✅ Task routing & orchestration
- ✅ Real-time log streaming
- ✅ Health checks & diagnostics
- ✅ Git operations & CI/CD
- ✅ PowerShell automation
- ✅ System configuration
- ✅ Quick code fixes

**Skill Domains:**
- Docker API & container lifecycle
- Kubernetes basic operations
- PowerShell scripting
- Bash/shell automation
- Git workflows & branching
- GitHub Actions CI/CD
- System monitoring & alerts
- Log aggregation (GlitchTip)

**Operational Commands:**
```powershell
# Built-in capabilities
docker ps, docker logs, docker run
git status, git push, git pull
python3 agent-router.py "task description"
./byte-rover-memory-sync.ps1 -SyncType FULL
curl http://localhost:8100/health
```

**Integration:**
- Directly controls Docker daemon (`/var/run/docker.sock`)
- Executes PowerShell scripts
- Triggers VS Code commands
- Manages task queue in `/memory/tasks`
- Updates memory with `byte_rover_atomic.py`

**When to Use:**
- "Restart the orchestrator"
- "Check agent status"
- "Deploy this to Docker"
- "Fix the build pipeline"
- "Check the logs"

---

### Orchestrator (Agent Zero) 🐉

**Type:** Master Autonomous Controller  
**Architecture:** Ralph Wiggins Autonomous Loop  
**Cycle Time:** 30 seconds  
**Concurrency:** Manages all other agents  
**Persistence:** Byte Rover memory system  

**Core Capabilities:**
- ✅ Task routing (intelligent decision trees)
- ✅ Agent orchestration & load balancing
- ✅ Memory state management
- ✅ Health monitoring of all services
- ✅ Autonomous task processing
- ✅ Error recovery & retry logic
- ✅ Performance analytics
- ✅ Resource optimization

**Routing Logic:**
```
┌─────────────────────────────────────────┐
│ New Task Received                       │
└────────────────┬────────────────────────┘
                 ▼
    ┌────────────────────────────┐
    │ Estimate Duration & Scope  │
    └────────────┬───────────────┘
                 ▼
        ┌────────────────────┐
        │ Route to Agent:    │
        │ < 2 min   → SB     │ (Switchblade)
        │ 2-30 min  → CY/SB  │ (Cynthia/Switchblade)
        │ 30+ min   → CC     │ (ClaudeCode)
        │ Design    → CY     │ (Cynthia)
        │ DevOps    → SB     │ (Switchblade)
        └────────────────────┘
```

**Memory Domains:**
```
/memory/
├── tasks/
│   ├── current-task.json        # What's being worked on
│   ├── queue.json               # Pending tasks
│   └── history.json             # Completed tasks
├── agents/
│   ├── claudecode.json          # CC state
│   ├── cynthia.json             # Cy state
│   ├── switchblade.json         # SB state
│   └── health.json              # All agent health
├── orchestrator/
│   ├── state.json               # Master state
│   ├── decisions.log            # Decision history
│   └── performance.json         # Metrics
└── results/
    └── [task-id]/results.json   # Task outputs
```

**Health Endpoints:**
- `GET http://localhost:8100/health` - Orchestrator status
- `GET http://localhost:3001/health` - MCP Server status  
- `GET http://localhost:3000/health` - Frontend health

**When to Use:**
- Runs continuously (no manual activation)
- Automatically routes tasks
- Manages agent workload
- Recovers from failures
- Never stops unless explicitly shut down

---

## Design Skills

### 1. Design System Generation

**Category:** Design  
**Used By:** Cynthia, ClaudeCode  
**Difficulty:** Advanced  

**What it does:**
Generates complete, industry-specific design systems using AI reasoning engine (100 rules).

**How to trigger:**
```
"Generate a design system for [industry]"
"What design system should we use for [product type]?"
```

**Output includes:**
- Pattern recommendation (24 landing page patterns)
- UI Style (57 styles)
- Color Palette (95 options)
- Typography Pairing (56 fonts)
- Key Effects (animations, transitions)
- Anti-Patterns (what to avoid)
- Pre-delivery Checklist

**File Reference:** `skills/design-system-generation.md`

---

### 2. UI/UX Pro Max Integration

**Category:** Design  
**Used By:** Cynthia  
**Difficulty:** Intermediate  

**Included Resources:**

**57 UI Styles:**
- Glassmorphism - Frosted glass effect
- Claymorphism - Soft, sculpted appearance
- Minimalism - Clean, reduced elements
- Brutalism - Raw, bold design
- Neumorphism - Soft, extrusions
- Bento Grid - Organized card layout
- Dark Mode - Low-light optimized
- AI-Native UI - Purple/pink gradients
- And 49 more...

**95 Color Palettes** (organized by industry):
- SaaS: Trust, innovation (blues, teals)
- E-commerce: Conversion-focused (warm, action colors)
- Healthcare: Trust, safety (greens, blues)
- Fintech: Security, stability (dark blues, gold)
- Beauty/Spa: Calming, premium (soft, warm)
- And 90 more...

**56 Font Pairings:**
- Elegant/Sophisticated: Cormorant Garamond + Montserrat
- Modern/Clean: Inter + Geist Sans
- Bold/Strong: Poppins + IBM Plex
- And 53 more...

**24 Chart Types:**
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distributions
- Heatmaps for density
- And 20 more...

**100 Reasoning Rules:**

| Industry | Pattern | Style | Colors | Typography |
|----------|---------|-------|--------|------------|
| SaaS | Hero + Features | Modern | Blues/Teals | Clean Sans |
| E-commerce | Product Grid | Bold | Warm | Friendly |
| Healthcare | Trust-Centric | Minimal | Greens/Blues | Professional |
| Beauty | Luxe/Premium | Soft UI | Pastels | Serif |
| Fintech | Security | Dark | Navy/Gold | Strong |

**File Reference:** `skills/ui-ux-pro-max-mastery.md`

---

### 3. Responsive Design & Mobile-First

**Category:** Design  
**Used By:** Cynthia, ClaudeCode  
**Difficulty:** Intermediate  

**Breakpoints:**
- Mobile: 375px, 480px
- Tablet: 768px, 1024px
- Desktop: 1440px+
- Ultra-wide: 1920px+

**Mobile-First Approach:**
1. Design for 375px first
2. Add enhancements at each breakpoint
3. No horizontal scrolling on mobile
4. Touch targets: 44px minimum
5. Typography scales responsively

**File Reference:** `skills/responsive-design.md`

---

### 4. Accessibility & WCAG AA

**Category:** Design  
**Used By:** Cynthia  
**Difficulty:** Intermediate  

**Standards:**
- WCAG AA: 4.5:1 contrast (normal text)
- WCAG AA: 3:1 contrast (large text 18pt+)
- Focus indicators: Always visible
- Keyboard navigation: Full support
- Screen reader: Semantic HTML
- `prefers-reduced-motion`: Respected

**Checklist:**
- [ ] Text contrast ≥ 4.5:1
- [ ] Focus visible on all interactive elements
- [ ] Keyboard accessible (Tab, Enter, Escape)
- [ ] Alt text on all images
- [ ] Proper ARIA labels
- [ ] Form labels associated
- [ ] Color not only differentiation
- [ ] Animation respects prefers-reduced-motion

**File Reference:** `skills/accessibility-wcag-aa.md`

---

### 5. Component Library Design

**Category:** Design  
**Used By:** Cynthia, ClaudeCode  
**Difficulty:** Advanced  

**Preferred Libraries:**
- **shadcn/ui** - Base components (buttons, forms, dialogs)
- **Radix UI** - Primitives & accessibility
- **Tailwind CSS** - Utility styling
- **Motion Primitives** - Animations
- **Lucide Icons** - Icon system

**Component System:**
```
design-system/
├── MASTER.md              # Global source of truth
│   ├── Colors (12-15 semantic)
│   ├── Typography (1-2 families, 6-8 sizes)
│   ├── Spacing (8pt scale: 0, 4, 8, 16, 24...)
│   ├── Border Radius (0, 4px, 8px, 12px, 16px...)
│   ├── Shadows (4 levels: soft, medium, strong, elevated)
│   └── Components (30-50 reusable)
└── pages/
    └── [page-name].md     # Page-specific overrides
```

**Token Usage:**
```css
/* Colors */
var(--color-primary): #0066FF
var(--color-secondary): #222222
var(--color-success): #10B981

/* Typography */
var(--font-heading): 'Geist Serif'
var(--font-body): 'Inter'
var(--font-size-lg): 18px

/* Spacing */
var(--space-1): 4px
var(--space-2): 8px
var(--space-3): 16px
```

**File Reference:** `skills/component-library-design.md`

---

## Development Skills

### 1. Full-Stack Architecture

**Category:** Development  
**Used By:** ClaudeCode  
**Difficulty:** Advanced  

**Frontend Patterns:**
- React Server Components (Next.js)
- State Management (Zustand, Pinia)
- API Client (TanStack Query, SWR)
- Component Architecture (compound components, render props)

**Backend Patterns:**
- API Design (REST, OpenAPI, GraphQL)
- Database (PostgreSQL with migrations)
- Authentication (Better Auth, JWT)
- File Handling (S3, local uploads)
- Webhooks & Events (async processing)

**Infrastructure:**
- Docker containerization
- Docker Compose orchestration
- PostgreSQL databases
- Redis caching
- Nginx reverse proxy
- GitHub Actions CI/CD

**File Reference:** `skills/full-stack-architecture.md`

---

### 2. React/Next.js Mastery

**Category:** Development  
**Used By:** ClaudeCode, Cynthia  
**Difficulty:** Advanced  

**Next.js 15 Patterns:**
- App Router (React 19 supported)
- Server/Client Components
- API Routes & API Handlers
- Streaming & Suspense
- Middleware & Auth Guards
- Static/Dynamic Rendering
- Image Optimization
- Font Optimization

**React 19 Features:**
- Server Components (RSCs)
- Form Actions
- useFormStatus Hook
- useOptimistic Hook
- Async Server Components
- Enhanced TypeScript Support

**Performance:**
- Code splitting (automatic)
- Tree-shaking unused code
- Minification & compression
- Image lazy-loading
- Font loading optimization
- Bundle analysis

**File Reference:** `skills/react-next-mastery.md`

---

### 3. Python/Node.js Scripting

**Category:** Development  
**Used By:** Switchblade, ClaudeCode  
**Difficulty:** Intermediate  

**Python Scripts:**
- `agent-zero-autonomous-orchestrator.py` - Master controller
- `agent-router.py` - Task routing engine
- `byte_rover_atomic.py` - Memory synchronization
- `add-sample-task.py` - Task creation

**Node.js Scripts:**
- `mcp-docker-server.js` - Docker orchestration
- `verify-scaffold.js` - Validation

**PowerShell Automation:**
- `activate-agent.ps1` - Agent startup
- `route-task.ps1` - Task routing CLI
- `view-agent-status.ps1` - Status dashboard
- `byte-rover-memory-sync.ps1` - Memory sync

**File Reference:** `skills/scripting-automation.md`

---

### 4. Docker & Containerization

**Category:** Development  
**Used By:** Switchblade, ClaudeCode  
**Difficulty:** Intermediate  

**Multi-stage Builds:**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

**Docker Compose:**
- Service orchestration (10+ services)
- Volume management (workspace, memory, logs)
- Environment variables
- Health checks & dependency management
- Network bridges
- Resource limits

**Best Practices:**
- Minimal images (Alpine, Distroless)
- Non-root users
- Health checks
- Graceful shutdowns
- Logging to stdout
- Single process per container

**File Reference:** `skills/docker-mastery.md`

---

### 5. Database Design

**Category:** Development  
**Used By:** ClaudeCode  
**Difficulty:** Intermediate  

**PostgreSQL Patterns:**
- Migrations (Drizzle, Flyway)
- Constraints (PK, FK, UNIQUE, CHECK)
- Indexes (B-tree, BRIN, GiST)
- Transactions & ACID
- Connection pooling
- Query optimization
- Replication & HA

**Schema Design:**
- Normal forms (3NF recommended)
- Temporal data (created_at, updated_at)
- Soft deletes (deleted_at)
- Audit trails
- Partitioning (large tables)

**File Reference:** `skills/database-design.md`

---

## Operational Skills

### 1. Container Management

**Category:** Operational  
**Used By:** Switchblade, Orchestrator  
**Difficulty:** Intermediate  

**Docker Commands:**
```bash
docker ps                 # List containers
docker logs -f <id>       # Stream logs
docker restart <id>       # Restart container
docker exec -it <id> /bin/bash  # Enter container
docker inspect <id>       # Container details
docker stats              # Resource usage
```

**Compose Operations:**
```bash
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose logs -f    # Stream all logs
docker-compose restart    # Restart all
docker-compose exec <svc> <cmd>  # Execute in service
```

**Health Checks:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**File Reference:** `skills/container-management.md`

---

### 2. Monitoring & Logging

**Category:** Operational  
**Used By:** Switchblade, Orchestrator  
**Difficulty:** Intermediate  

**Log Locations:**
- `/logs/claudecode.log` - ClaudeCode execution
- `/logs/cynthia.log` - Cynthia design tasks
- `/logs/switchblade.log` - Switchblade operations
- `/logs/orchestrator.log` - Master controller
- `docker-compose logs` - All container output

**Monitoring Stack:**
- **GlitchTip** (localhost:3100) - Error tracking
- **Portainer** (localhost:9000) - Container UI
- **Docker Stats** - Resource monitoring
- **PostgreSQL Logs** - Database operations
- **Health Endpoints** - Service status

**Real-time Dashboards:**
- Agent status (running, idle, error)
- CPU/memory per container
- Task queue length
- Error rates & alerts
- Response times
- Uptime metrics

**File Reference:** `skills/monitoring-logging.md`

---

### 3. Task Routing & Orchestration

**Category:** Operational  
**Used By:** Orchestrator, Switchblade  
**Difficulty:** Advanced  

**Task Structure:**
```json
{
  "task_id": "task_20260122_001",
  "objective": "Build a landing page",
  "agent_type": "design",
  "priority": "high",
  "estimated_duration": "20-30 minutes",
  "tags": ["frontend", "design", "urgent"],
  "created_at": "2026-01-22T10:30:00Z",
  "status": "routed_to_cynthia"
}
```

**Routing Decision Tree:**
```python
if duration < 2 minutes:
    agent = Switchblade  # Quick tasks
elif task_type == "design":
    agent = Cynthia      # Design-specific
elif duration < 30 minutes:
    agent = Cynthia or Switchblade
else:
    agent = ClaudeCode   # Long-running
```

**File Reference:** `skills/task-routing.md`

---

### 4. Memory Management (Byte Rover)

**Category:** Operational  
**Used By:** All agents  
**Difficulty:** Intermediate  

**Memory Structure:**
```
/memory/
├── tasks/           # Current & pending tasks
├── agents/          # Agent states & health
├── orchestrator/    # Master orchestrator state
├── results/         # Completed task outputs
└── config/          # Shared configuration
```

**Memory Operations:**
```powershell
# Write task
./byte-rover-memory-sync.ps1 -Operation WRITE -Domain tasks -Data @{...}

# Read state
./byte-rover-memory-sync.ps1 -Operation READ -Domain agents

# Full sync
./byte-rover-memory-sync.ps1 -Operation FULL

# Update task
./byte-rover-memory-sync.ps1 -Operation UPDATE -Domain tasks -TaskId task_123
```

**File Reference:** `skills/memory-management.md`

---

### 5. Deployment & DevOps

**Category:** Operational  
**Used By:** Switchblade, ClaudeCode  
**Difficulty:** Intermediate  

**Deployment Options:**

**Option A: Docker Desktop (Local)**
```bash
docker-compose up -d
```

**Option B: VPS (Self-hosted)**
```bash
# Copy files
scp -r docker-compose.yml master.env root@server:/opt/agent-zero/

# Start services
ssh root@server 'cd /opt/agent-zero && docker-compose up -d'
```

**Option C: Vercel (Frontend)**
```bash
vercel --prod
```

**Option D: Coolify (One-click)**
- Deploy via Coolify UI
- Auto SSL certificates
- Auto scaling

**CI/CD Pipeline (GitHub Actions):**
```yaml
name: Deploy Agent Zero
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build & push Docker
        run: docker-compose build && docker push
      - name: Deploy to VPS
        run: ssh deploy@server 'cd /opt/agent-zero && docker-compose pull && docker-compose up -d'
```

**File Reference:** `skills/deployment-devops.md`

---

## Available Tools

### Development Tools

| Tool | Purpose | Access | Agent |
|------|---------|--------|-------|
| **React** | Frontend framework | `npm install` | ClaudeCode, Cynthia |
| **Next.js** | Full-stack React | `npm install next` | ClaudeCode |
| **TypeScript** | Type-safe JavaScript | Built-in | All |
| **Tailwind CSS** | Utility CSS framework | `npm install` | Cynthia, ClaudeCode |
| **shadcn/ui** | Component library | `npm install` | Cynthia, ClaudeCode |
| **Vite** | Build tool | `npm install` | ClaudeCode |
| **Drizzle ORM** | TypeScript ORM | `npm install` | ClaudeCode |
| **PostgreSQL** | Database | Docker | ClaudeCode |

### Automation Tools

| Tool | Purpose | Access | Agent |
|------|---------|--------|-------|
| **Python 3.11** | Scripting | Runtime | ClaudeCode, Switchblade |
| **Node.js 20** | Runtime | Docker | All |
| **PowerShell** | Automation | Windows | Switchblade |
| **Bash** | Shell scripting | Linux/Mac | Switchblade |
| **Docker** | Containerization | `/var/run/docker.sock` | Switchblade |
| **Docker Compose** | Orchestration | CLI | Switchblade |
| **Git** | Version control | CLI | Switchblade, ClaudeCode |

### Monitoring Tools

| Tool | Purpose | Access | Agent |
|------|---------|--------|-------|
| **GlitchTip** | Error tracking | localhost:3100 | All |
| **Portainer** | Container UI | localhost:9000 | Switchblade |
| **PostgreSQL** | Database | localhost:5432 | ClaudeCode |
| **Docker Stats** | Monitoring | CLI | Switchblade |
| **Health Endpoints** | Status checks | HTTP | All |

### APIs & Integrations

| API | Purpose | Agent | Example |
|-----|---------|-------|---------|
| **MCP Docker Server** | Container control | Switchblade | `http://localhost:3001` |
| **Orchestrator API** | Task routing | Orchestrator | `http://localhost:8100` |
| **PostgreSQL** | Data storage | ClaudeCode | `:5432/agent_zero` |
| **Memory System** | State persistence | All | `/memory` volume |
| **GitHub API** | Version control | ClaudeCode | `GITHUB_TOKEN` env |
| **OpenAI API** | Optional enhancement | ClaudeCode | `OPENAI_API_KEY` |

---

## Skill Rules & Constraints

### Design Rules
1. **No emojis as icons** - Use SVG (Heroicons, Lucide)
2. **Accessibility first** - WCAG AA minimum (4.5:1 contrast)
3. **Mobile-first** - Start at 375px, enhance up
4. **Responsive breakpoints** - 375px, 768px, 1024px, 1440px
5. **Design tokens** - Use CSS variables, never hardcode colors
6. **No AI purple** - Avoid clichéd AI gradients (unless SaaS-specific)
7. **Smooth transitions** - 150-300ms animations
8. **Prefer Tailwind** - For consistency & perf
9. **Component reuse** - Build systems, not one-offs
10. **Type-safe** - TypeScript for all frontends

### Development Rules
1. **TypeScript required** - Strict mode enabled
2. **No `any` types** - Use `unknown` or explicit types
3. **Minimal dependencies** - Prefer native APIs
4. **Security first** - Validate all inputs, no SQL injection
5. **Docker required** - All services containerized
6. **Environment variables** - Never hardcode secrets
7. **Error handling** - Graceful failure, no silent errors
8. **Testing** - Unit tests for critical logic
9. **Performance** - Lazy-load, code-split, optimize
10. **Documentation** - Comment why, not what

### Operational Rules
1. **Health checks always** - All containers have `healthcheck`
2. **Logs to stdout** - No file logging in containers
3. **Resource limits** - CPU/memory bounds on services
4. **Graceful shutdown** - Respond to SIGTERM
5. **No hardcoded IPs** - Use service names (Docker DNS)
6. **Volume mounts** - For persistence only
7. **Non-root user** - Containers run unprivileged
8. **Single process** - One service per container (mostly)
9. **Secrets in env** - Never in Dockerfile or git
10. **Monitoring enabled** - GlitchTip integration required

---

## Anti-Patterns

### Design Anti-Patterns ❌
- ❌ Bright neon colors (hard on eyes)
- ❌ Auto-playing videos (UX nightmare)
- ❌ Unreadable text (contrast < 3:1)
- ❌ Hover-only critical info (mobile fails)
- ❌ Moving backgrounds (accessibility breach)
- ❌ Infinite scroll on desktop (pagination better)
- ❌ Blinking elements (seizure risk)
- ❌ Flashing animations (prefers-reduced-motion)
- ❌ Comic Sans anywhere (ever)
- ❌ 5+ fonts (branding chaos)

### Development Anti-Patterns ❌
- ❌ `console.log()` in production (pollutes logs)
- ❌ `setTimeout()` for delays (use proper async)
- ❌ Global variables (scope pollution)
- ❌ Callback hell (use async/await)
- ❌ Hard-coded URLs (use env vars)
- ❌ Unhandled promises (causes silent failures)
- ❌ Inline styles (CSS > inline)
- ❌ String concatenation for HTML (use templates)
- ❌ Synchronous I/O (always async)
- ❌ Comments that lie (outdated docs)

### Operational Anti-Patterns ❌
- ❌ `docker run` without health checks
- ❌ Volumes with no backups
- ❌ Logs in containers (use stdout)
- ❌ Root user in containers (security risk)
- ❌ Hardcoded secrets in Dockerfile
- ❌ No monitoring (flying blind)
- ❌ Manual deployments (error-prone)
- ❌ No rollback strategy (stuck if broken)
- ❌ Ignoring warnings (debt accumulates)
- ❌ No staging environment (test in prod = bad)

---

## Integration Points

### Dashboard Integration

When integrated into your dashboard command center:

**Frontend Dashboard Features:**
- Agent status widget (real-time health)
- Task creation form (auto-suggest agent)
- Skill library (searchable, categorized)
- Live logs (filtered by agent/task)
- Memory browser (inspect JSON state)
- Container manager (start/stop/restart)
- Performance metrics (CPU, memory, response times)
- Deployment history (who, what, when)

**Backend Integration Points:**
```typescript
// Agent routes
GET /api/agents            // List agents
GET /api/agents/:id        // Agent details
POST /api/agents/:id/execute  // Trigger task

// Task routes
GET /api/tasks            // List tasks
POST /api/tasks           // Create task
GET /api/tasks/:id        // Task details
PUT /api/tasks/:id        // Update task

// Container routes
GET /api/containers       // List containers
GET /api/containers/:id   // Container details
POST /api/containers/:id/restart  // Restart
DELETE /api/containers/:id        // Stop

// Logs & monitoring
GET /api/logs            // Stream logs
WS /ws/logs              // WebSocket logs
GET /api/metrics         // Performance metrics
```

**WebSocket Events:**
```javascript
// Real-time updates
ws.on('agent:status:changed', handler)
ws.on('task:completed', handler)
ws.on('container:health', handler)
ws.on('memory:updated', handler)
```

---

## Summary Table

| Agent | Role | Cycle | Agents | Skills | Trigger |
|-------|------|-------|--------|--------|---------|
| **ClaudeCode** | Long-running dev | 30+ min | Architecture, Code, DB, API, Performance | `/activate ClaudeCode` |
| **Cynthia** | Design & UX | 2-30 min | Design System, UI/UX, Components, Accessibility | `/activate Cynthia` |
| **Switchblade** | Quick ops | < 2 min | Containers, Automation, Monitoring, Git | `/activate Switchblade` |
| **Orchestrator** | Master control | 30 sec loop | Task Routing, Health, Memory, Auto-loop | Always running |

---

**Created:** January 22, 2026  
**Version:** 1.0.0  
**Owner:** Agent Zero  
**Status:** PRODUCTION READY  
**Last Updated:** January 22, 2026
