# Vercel Next.js BFF Project - Implementation Tasks

## Project Overview

Build a Vercel-hosted Next.js dashboard with Backend-for-Frontend (BFF) that proxies to Agent Zero backend, providing mobile-first UI with full feature coverage.

---

## Environment Setup & Architecture

### Task 1: Project Initialization
- [ ] Create `apps/vercel-dashboard/` directory in repo root
- [ ] Initialize Next.js 14+ project with App Router
- [ ] Set up TypeScript configuration
- [ ] Configure ESLint and Prettier
- [ ] Create basic folder structure:
  ```
  apps/vercel-dashboard/
  ├── src/
  │   ├── app/              # Next.js App Router pages
  │   ├── components/       # React components
  │   ├── lib/             # Utilities and API clients
  │   ├── styles/          # Global styles
  │   └── types/           # TypeScript types
  ├── public/              # Static assets
  ├── .env.example         # Environment variables template
  ├── next.config.js       # Next.js configuration
  ├── package.json
  └── README.md
  ```

### Task 2: Environment Variables Setup
Create `.env.example` with:
- [ ] `AZ_BASE_URL` - Agent Zero backend URL
- [ ] `AZ_API_KEY` - mcp_server_token for API key endpoints
- [ ] `AZ_AUTH_LOGIN` - Backend session login (optional)
- [ ] `AZ_AUTH_PASSWORD` - Backend session password (optional)
- [ ] `DASH_AUTH_SECRET` - NextAuth secret for dashboard login
- [ ] `DASH_ALLOWED_EMAILS` - Comma-separated email allowlist (optional)
- [ ] `UPSTASH_REDIS_URL` - Redis for session storage (recommended)
- [ ] `UPSTASH_REDIS_TOKEN` - Redis token
- [ ] `NEXTAUTH_URL` - Dashboard URL
- [ ] `NEXTAUTH_SECRET` - Auth secret

---

## Authentication Layer

### Task 3: Dashboard Authentication (NextAuth.js)
- [ ] Install `next-auth` package
- [ ] Create `/api/auth/[...nextauth]/route.ts`
- [ ] Implement CredentialsProvider (email/password)
- [ ] Optional: Add OAuth providers (Google, GitHub)
- [ ] Set up session strategy (JWT)
- [ ] Create middleware for protected routes
- [ ] Create login/logout pages
- [ ] Implement HttpOnly cookie sessions

### Task 4: Backend Session Management
- [ ] Create utility to fetch CSRF token from `/csrf_token`
- [ ] Implement backend login via `/login` endpoint
- [ ] Store backend session cookies in server-side store (Redis/memory)
- [ ] Create session refresh logic (auto-relogin on 403/302)
- [ ] Implement cookie jar per dashboard user session

---

## BFF API Layer (Server-Side Proxying)

### Task 5: API Route Structure
Create `/api/az/` routes for all endpoints:

#### Core Operations
- [ ] `/api/az/health/route.ts` → `/health`
- [ ] `/api/az/poll/route.ts` → `/poll`
- [ ] `/api/az/message/route.ts` → `/message`
- [ ] `/api/az/message-async/route.ts` → `/message_async`
- [ ] `/api/az/pause/route.ts` → `/pause`
- [ ] `/api/az/nudge/route.ts` → `/nudge`

#### Chat Management
- [ ] `/api/az/chat/create/route.ts` → `/chat_create`
- [ ] `/api/az/chat/load/route.ts` → `/chat_load`
- [ ] `/api/az/chat/reset/route.ts` → `/chat_reset`
- [ ] `/api/az/chat/remove/route.ts` → `/chat_remove`
- [ ] `/api/az/chat/export/route.ts` → `/chat_export`
- [ ] `/api/az/history/get/route.ts` → `/history_get`

#### Scheduler
- [ ] `/api/az/scheduler/list/route.ts` → `/scheduler_tasks_list`
- [ ] `/api/az/scheduler/create/route.ts` → `/scheduler_task_create`
- [ ] `/api/az/scheduler/update/route.ts` → `/scheduler_task_update`
- [ ] `/api/az/scheduler/run/route.ts` → `/scheduler_task_run`
- [ ] `/api/az/scheduler/delete/route.ts` → `/scheduler_task_delete`
- [ ] `/api/az/scheduler/tick/route.ts` → `/scheduler_tick`

#### Files
- [ ] `/api/az/files/list/route.ts` → `/get_work_dir_files`
- [ ] `/api/az/files/info/route.ts` → `/file_info`
- [ ] `/api/az/files/delete/route.ts` → `/delete_work_dir_file`
- [ ] `/api/az/files/download/route.ts` → `/download_work_dir_file`
- [ ] `/api/az/files/upload/route.ts` → `/upload`
- [ ] `/api/az/image/route.ts` → `/image_get`

#### Memory & Knowledge
- [ ] `/api/az/memory/dashboard/route.ts` → `/memory_dashboard`
- [ ] `/api/az/knowledge/import/route.ts` → `/import_knowledge`
- [ ] `/api/az/knowledge/reindex/route.ts` → `/knowledge_reindex`
- [ ] `/api/az/knowledge/path/route.ts` → `/knowledge_path_get`

#### Backups
- [ ] `/api/az/backup/defaults/route.ts` → `/backup_get_defaults`
- [ ] `/api/az/backup/create/route.ts` → `/backup_create`
- [ ] `/api/az/backup/preview-grouped/route.ts` → `/backup_preview_grouped`
- [ ] `/api/az/backup/inspect/route.ts` → `/backup_inspect`
- [ ] `/api/az/backup/restore-preview/route.ts` → `/backup_restore_preview`
- [ ] `/api/az/backup/restore/route.ts` → `/backup_restore`
- [ ] `/api/az/backup/test/route.ts` → `/backup_test`

#### MCP
- [ ] `/api/az/mcp/status/route.ts` → `/mcp_servers_status`
- [ ] `/api/az/mcp/apply/route.ts` → `/mcp_servers_apply`
- [ ] `/api/az/mcp/detail/route.ts` → `/mcp_server_get_detail`
- [ ] `/api/az/mcp/log/route.ts` → `/mcp_server_get_log`

#### Projects & Notifications
- [ ] `/api/az/projects/route.ts` → `/projects`
- [ ] `/api/az/notifications/create/route.ts` → `/notification_create`
- [ ] `/api/az/notifications/history/route.ts` → `/notifications_history`
- [ ] `/api/az/notifications/mark-read/route.ts` → `/notifications_mark_read`
- [ ] `/api/az/notifications/clear/route.ts` → `/notifications_clear`

#### Settings & Other
- [ ] `/api/az/settings/get/route.ts` → `/settings_get`
- [ ] `/api/az/settings/set/route.ts` → `/settings_set`
- [ ] `/api/az/tunnel/route.ts` → `/tunnel`
- [ ] `/api/az/tunnel-proxy/route.ts` → `/tunnel_proxy`
- [ ] `/api/az/transcribe/route.ts` → `/transcribe`
- [ ] `/api/az/synthesize/route.ts` → `/synthesize`

### Task 6: Proxy Utilities
- [ ] Create `lib/proxy.ts` with base proxy function
- [ ] Implement API-key mode (for `/api_*` endpoints)
- [ ] Implement session+CSRF mode (for authenticated endpoints)
- [ ] Add automatic error handling and retries
- [ ] Implement request/response logging
- [ ] Add timeout handling
- [ ] Create response redaction for secrets

---

## Frontend Components

### Task 7: Layout & Navigation
- [ ] Create `app/layout.tsx` with main layout
- [ ] Build top status bar component (connection, progress, context selector)
- [ ] Create left navigation sidebar component
- [ ] Implement mobile hamburger menu
- [ ] Add right inspector panel (collapsible on mobile)
- [ ] Create three-panel ops grid layout
- [ ] Implement responsive breakpoints

### Task 8: Mission Control Panel
- [ ] Create `app/page.tsx` (Mission Control)
- [ ] Build "Now Playing" card with real-time progress
- [ ] Create "Critical Alerts" card
- [ ] Build "Active Contexts" list
- [ ] Create "Running Tasks" card
- [ ] Add "System Health" metrics
- [ ] Implement workflow template selector
- [ ] Add RUN button with command execution

### Task 9: Beads Timeline Component
- [ ] Create `app/beads/page.tsx`
- [ ] Build bead item component with color-coding
- [ ] Implement type filters (9 types)
- [ ] Add search functionality
- [ ] Create "hide temporary" toggle
- [ ] Build export to JSON feature
- [ ] Add "jump to latest" button
- [ ] Implement pin errors feature
- [ ] Create bead detail modal/inspector

### Task 10: Live View Component
- [ ] Create `app/live-view/page.tsx`
- [ ] Build screenshot viewer component
- [ ] Implement img:// to /image_get conversion
- [ ] Create step narration sidebar
- [ ] Build "Current Tool" card
- [ ] Add "Blockers" panel
- [ ] Implement auto-refresh toggle
- [ ] Add screenshot download feature
- [ ] Create full-size image modal

### Task 11: Chats Panel
- [ ] Create `app/chats/page.tsx`
- [ ] Build chat list sidebar
- [ ] Create chat message display
- [ ] Implement message composer with attachments
- [ ] Add action buttons (new, load, reset, remove, export)
- [ ] Build pause/resume/nudge controls
- [ ] Implement async message sending with polling

### Task 12: Scheduler Panel
- [ ] Create `app/scheduler/page.tsx`
- [ ] Build tasks table with sorting
- [ ] Implement type/state filters
- [ ] Add search functionality
- [ ] Create task creation modals (adhoc, scheduled, planned)
- [ ] Build task editor modal
- [ ] Add run now, enable/disable, delete actions
- [ ] Implement tick trigger button
- [ ] Create cron expression builder for scheduled tasks
- [ ] Build datetime picker for planned tasks

### Task 13: Projects Panel
- [ ] Create `app/projects/page.tsx`
- [ ] Build project grid with color tags
- [ ] Implement filter by project
- [ ] Add project creation (if API exists)

### Task 14: Memory & Knowledge Panels
- [ ] Create `app/memory/page.tsx`
- [ ] Build memory dashboard viewer
- [ ] Add human approval warnings
- [ ] Create confirmation modals for edits
- [ ] Create `app/knowledge/page.tsx`
- [ ] Build knowledge path display
- [ ] Add import modal/flow
- [ ] Implement reindex with progress indicator

### Task 15: Files Panel
- [ ] Create `app/files/page.tsx`
- [ ] Build file grid/list view toggle
- [ ] Implement sort and filter controls
- [ ] Add file upload with drag-and-drop
- [ ] Create download functionality
- [ ] Build delete with confirmation
- [ ] Implement image preview
- [ ] Add file type icons

### Task 16: MCP Panel
- [ ] Create `app/mcp/page.tsx`
- [ ] Build server status table
- [ ] Create config editor (JSON)
- [ ] Add apply config button
- [ ] Build logs viewer modal
- [ ] Implement server detail view

### Task 17: A2A / Agent Mail Panel (NEW)
- [ ] Create `app/a2a/page.tsx`
- [ ] Build message threads view
- [ ] Create send message composer
- [ ] Add broadcast functionality
- [ ] Build metrics display
- [ ] Add "NEW" badge
- [ ] Implement graceful degradation if backend incomplete

### Task 18: Backups Panel
- [ ] Create `app/backups/page.tsx`
- [ ] Build wizard flow (defaults → create → inspect → restore)
- [ ] Add confirmation modals for destructive operations
- [ ] Create backup preview
- [ ] Implement restore preview
- [ ] Add test functionality
- [ ] Build progress indicators

### Task 19: Notifications Panel
- [ ] Create `app/notifications/page.tsx`
- [ ] Build notification list with unread badges
- [ ] Implement mark as read
- [ ] Add clear all functionality
- [ ] Create notification cards with types
- [ ] Add real-time updates from poll

### Task 20: Settings Panel
- [ ] Create `app/settings/page.tsx`
- [ ] Build settings viewer/editor
- [ ] Add security warnings
- [ ] Create tunnel controls
- [ ] Implement speech toggles
- [ ] Add save/reset buttons
- [ ] Build confirmation for critical changes

---

## Real-Time & State Management

### Task 21: Polling System
- [ ] Create React hook `usePolling` with adaptive rates
- [ ] Implement 500ms (active), 750ms (normal), 1500ms (idle)
- [ ] Add connection status detection
- [ ] Build error recovery logic
- [ ] Create centralized poll data distribution

### Task 22: State Management
- [ ] Set up Zustand or React Context for global state
- [ ] Create stores for:
  - [ ] Connection status
  - [ ] Active context
  - [ ] Contexts and tasks lists
  - [ ] Logs (beads)
  - [ ] Notifications
  - [ ] Progress
  - [ ] Errors
- [ ] Implement state persistence (localStorage for UI preferences)

### Task 23: Toast Notification System
- [ ] Create toast component library
- [ ] Implement success, error, warning, info types
- [ ] Add auto-dismiss with configurable timeout
- [ ] Build toast queue (max 3 visible)
- [ ] Create toast close button

---

## UI/UX Enhancements

### Task 24: Design System Implementation
- [ ] Create color system CSS variables (7 operational states)
- [ ] Build component library (buttons, inputs, cards, modals)
- [ ] Implement dark theme (primary)
- [ ] Optional: Add light theme toggle
- [ ] Create typography scale
- [ ] Build spacing system
- [ ] Add animation/transition utilities

### Task 25: Mobile Optimization
- [ ] Implement responsive breakpoints
- [ ] Create mobile navigation drawer
- [ ] Build touch-friendly controls
- [ ] Add swipe gestures for panels
- [ ] Optimize for small screens
- [ ] Test on iOS Safari and Android Chrome

### Task 26: Accessibility
- [ ] Add ARIA labels to all interactive elements
- [ ] Implement keyboard navigation (Tab, Arrow keys, Esc)
- [ ] Create focus indicators
- [ ] Add screen reader support
- [ ] Build skip navigation links
- [ ] Test with Lighthouse accessibility audit

---

## Security & Guardrails

### Task 27: Security Implementation
- [ ] Implement CSRF protection on all mutations
- [ ] Add rate limiting to API routes
- [ ] Create input validation and sanitization
- [ ] Build XSS prevention (escape user content)
- [ ] Implement Content Security Policy headers
- [ ] Add secrets redaction in logs/displays
- [ ] Create audit logging for sensitive operations

### Task 28: Confirmation Gates
- [ ] Build reusable confirmation modal component
- [ ] Add confirmations for:
  - [ ] Delete operations
  - [ ] Backup restore
  - [ ] Settings changes
  - [ ] Task deletion
  - [ ] Context removal
  - [ ] Memory edits
- [ ] Implement typed confirmation phrases for destructive ops

### Task 29: Autonomy Level UI
- [ ] Create autonomy slider component (T0-T4)
- [ ] Add tier descriptions on hover
- [ ] Implement UI warnings for high-tier actions
- [ ] Build approval queue UI (if backend supports)
- [ ] Add policy tier badges to actions

---

## Testing & Quality

### Task 30: Unit Tests
- [ ] Set up Jest and React Testing Library
- [ ] Write tests for API proxy functions
- [ ] Test React components (render, interactions)
- [ ] Test state management logic
- [ ] Test authentication flows
- [ ] Aim for 80%+ code coverage

### Task 31: Integration Tests
- [ ] Test BFF → Agent Zero communication
- [ ] Test authentication end-to-end
- [ ] Test polling and state updates
- [ ] Test file upload/download
- [ ] Test error handling and recovery

### Task 32: E2E Tests
- [ ] Set up Playwright or Cypress
- [ ] Test critical user flows:
  - [ ] Login → Dashboard → Create Chat → Send Message
  - [ ] Create Task → Run Now → View in Mission Control
  - [ ] Upload File → Preview → Delete
  - [ ] Create Backup → Restore with confirmation
- [ ] Test mobile responsive behavior

---

## Deployment & DevOps

### Task 33: Vercel Configuration
- [ ] Create `vercel.json` configuration
- [ ] Set up environment variables in Vercel dashboard
- [ ] Configure build settings
- [ ] Set up domain (if custom)
- [ ] Enable preview deployments
- [ ] Configure edge functions for API routes

### Task 34: CI/CD Pipeline
- [ ] Set up GitHub Actions workflow
- [ ] Add linting step
- [ ] Add type checking step
- [ ] Add test step
- [ ] Add build step
- [ ] Implement automatic deployment to Vercel on push to main

### Task 35: Monitoring & Logging
- [ ] Add Vercel Analytics
- [ ] Set up error tracking (Sentry or similar)
- [ ] Implement performance monitoring
- [ ] Add uptime monitoring
- [ ] Create dashboard for metrics

---

## Documentation

### Task 36: User Documentation
- [ ] Create README.md for Vercel app
- [ ] Write setup guide (environment variables, deployment)
- [ ] Document authentication setup
- [ ] Create user guide for dashboard features
- [ ] Add troubleshooting section
- [ ] Document mobile usage

### Task 37: Developer Documentation
- [ ] Document BFF architecture
- [ ] Create API route reference
- [ ] Write component documentation
- [ ] Document state management patterns
- [ ] Add contribution guidelines
- [ ] Create architecture diagrams

### Task 38: Deployment Guide
- [ ] Write Vercel deployment instructions
- [ ] Document Agent Zero backend setup
- [ ] Create network configuration guide (VPN, tunnel, public)
- [ ] Add security best practices
- [ ] Document environment variable setup
- [ ] Create upgrade guide

---

## Final Polish

### Task 39: Performance Optimization
- [ ] Implement code splitting
- [ ] Add lazy loading for panels
- [ ] Optimize images (Next.js Image component)
- [ ] Minimize bundle size
- [ ] Add caching strategies
- [ ] Optimize polling efficiency
- [ ] Implement request deduplication

### Task 40: User Experience Enhancements
- [ ] Add loading skeletons
- [ ] Implement optimistic UI updates
- [ ] Create empty states for all panels
- [ ] Add helpful error messages with recovery suggestions
- [ ] Build onboarding tour for first-time users
- [ ] Add keyboard shortcuts reference
- [ ] Create contextual help tooltips

### Task 41: Final Testing & Launch
- [ ] Perform full manual testing on desktop
- [ ] Test on mobile devices (iOS, Android)
- [ ] Test with slow network (throttling)
- [ ] Verify all API endpoints work
- [ ] Check error handling and edge cases
- [ ] Review security measures
- [ ] Perform load testing
- [ ] Create launch checklist
- [ ] Deploy to production
- [ ] Monitor post-launch metrics

---

## Maintenance & Future Enhancements

### Task 42: Post-Launch
- [ ] Monitor error rates and fix issues
- [ ] Collect user feedback
- [ ] Track analytics and usage patterns
- [ ] Plan feature improvements
- [ ] Update documentation based on user questions

### Task 43: Future Features (Roadmap)
- [ ] Add WebSocket support for real-time updates
- [ ] Implement desktop streaming (noVNC)
- [ ] Create custom panel layouts (drag-and-drop)
- [ ] Add export reports (PDF, HTML)
- [ ] Build timeline playback feature
- [ ] Implement multi-context comparison
- [ ] Add collaborative features (multi-user)
- [ ] Create mobile native app (React Native)

---

## Estimated Timeline

- **Phase 1 (Weeks 1-2)**: Setup, Auth, BFF API Layer (Tasks 1-6)
- **Phase 2 (Weeks 3-5)**: Core UI Components (Tasks 7-15)
- **Phase 3 (Week 6)**: Remaining Panels (Tasks 16-20)
- **Phase 4 (Week 7)**: Real-time & State (Tasks 21-23)
- **Phase 5 (Week 8)**: UI/UX Enhancement (Tasks 24-26)
- **Phase 6 (Week 9)**: Security & Testing (Tasks 27-32)
- **Phase 7 (Week 10)**: Deployment & Documentation (Tasks 33-38)
- **Phase 8 (Week 11)**: Polish & Launch (Tasks 39-41)

**Total Estimated Time**: 11 weeks for full implementation

---

## Priority Levels

### P0 (Must Have - MVP)
- Tasks 1-6: Setup and core BFF
- Tasks 7-11: Basic UI (Mission Control, Beads, Chats)
- Task 21-22: Polling and state
- Task 27: Basic security
- Task 36: User docs

### P1 (Should Have - Full Feature Parity)
- Tasks 12-20: All remaining panels
- Task 23: Toast system
- Tasks 24-26: Design and mobile
- Tasks 28-29: Advanced security
- Tasks 30-31: Testing
- Tasks 33-34: Deployment

### P2 (Nice to Have - Polish)
- Tasks 32: E2E tests
- Task 35: Monitoring
- Task 37-38: Advanced docs
- Tasks 39-41: Performance and UX polish

---

## Key Success Criteria

✅ Dashboard accessible from any device via Vercel URL
✅ All 60+ Agent Zero API endpoints proxied and working
✅ Mobile-first UI works on phones and tablets
✅ Real-time updates via adaptive polling
✅ No secrets exposed to browser (all in BFF)
✅ Authentication prevents unauthorized access
✅ Comprehensive documentation for users and developers
✅ Deployment automated via CI/CD
✅ Performance meets targets (< 2s page load, < 500ms API response)
✅ Accessibility score > 90 (Lighthouse)

---

## Notes for Next Agent

1. **Start with MVP**: Focus on P0 tasks first to get working prototype
2. **Test as you go**: Don't wait until end - test each component
3. **Security first**: Never expose AZ_API_KEY to browser
4. **Mobile-friendly**: Test on actual devices, not just DevTools
5. **Document decisions**: Update docs as you make architecture choices
6. **Git commits**: Commit frequently with descriptive messages
7. **Environment setup**: Create .env.example and document all variables
8. **Error handling**: Every API call should have error handling
9. **Loading states**: Show loading indicators for all async operations
10. **Graceful degradation**: If backend feature missing, UI should handle it

---

## Reference Documents

- Main spec: Original Vercel BFF specification
- API mapping: `docs/master-dashboard.md` (section: API Mapping)
- Color system: `docs/master-dashboard.md` (section: Operational State Colors)
- Backend repo: `agent-zero-Fork` (already has Master Dashboard)
- Existing dashboard: Reference `webui/master-dashboard.html` for feature parity

---

## Getting Help

If stuck on any task:
1. Check Agent Zero repo `python/api/*.py` for endpoint implementation
2. Review Master Dashboard code in `webui/js/master-dashboard/` for patterns
3. Test endpoints directly with curl/Postman before building UI
4. Consult Next.js docs for App Router patterns
5. Check Vercel docs for deployment specifics

---

**Good luck! 🚀 Let's build an amazing mobile-first dashboard for Agent Zero!**
