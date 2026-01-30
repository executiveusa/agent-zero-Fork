# Agent Zero OS — Build Task

## Project Setup
- [x] Install Ralphy build system globally: `npm install -g ralphy-cli`
- [x] Load secrets from master.env: `Load-AgentSecrets`
- [x] Initialize Ralphy config: `ralphy --init`
- [x] Verify Docker running: `docker compose ps`

## Core Features
- [ ] Fix MCP server missing mcp-docker-server.js file
- [ ] Verify all 7 Docker containers running stable (22+ hours uptime)
- [ ] Update docker-compose-coolify.yml with reverse proxy labels
- [ ] Deploy web UI dashboard to agent-zero.31.220.58.212.sslip.io

## Coolify Integration
- [ ] Deploy docker-compose-coolify.yml to VPS
- [ ] Configure Traefik labels for all agents
- [ ] Test subdomain routing (claude, cynthia, switchblade, browser, glitchtip)
- [ ] Verify Coolify dashboard integration at port 8000

## Frontend Improvements
- [ ] Test AgentControlPanel voice control interface
- [ ] Verify real-time agent status monitoring
- [ ] Validate glassmorphism design rendering
- [ ] Check API proxy route to Docker backend

## Testing & Verification
- [ ] Run smoke tests on all agent endpoints
- [ ] Test voice control functionality with browser automation
- [ ] Verify GitHub repository sync
- [ ] Check GlitchTip error monitoring
- [ ] Validate PostgreSQL database connectivity

## Deployment
- [ ] Commit Ralphy integration to GitHub
- [ ] Push updated .gitignore with secrets protection
- [ ] Deploy to production VPS (31.220.58.212)
- [ ] Run comprehensive test suite
- [ ] Update project documentation

---

## Usage

Execute with Ralphy:

```bash
# Load secrets
Load-AgentSecrets

# Run build
ralphy --prd PRD.md --sonnet

# Or parallel execution
ralphy --prd PRD.md --parallel --max-parallel 5 --sandbox
```

## Notes
- Secrets loaded from: `E:\THE PAULI FILES\master.env`
- Protected by .gitignore: master.env, *.env, .ralphy/*
- VPS: root@31.220.58.212
- Coolify: http://31.220.58.212:8000
- Repository: https://github.com/executiveusa/agent-zero-Fork
