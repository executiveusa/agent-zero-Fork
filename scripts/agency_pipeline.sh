#!/bin/bash
# agency_pipeline.sh
# ─────────────────────────────────────────────────────────────────────
# End-to-end AI agency automation pipeline.
#
# Flow:
#   Input  →  Scan  →  Plan  →  Implement (parallel)  →  Test  →  Deploy  →  Announce
#
# Inputs (pick one):
#   --task "description"          Freeform task text
#   --issue-url "github URL"      Fetch task from a GitHub issue
#   --notion-task-id "id"         Fetch task from Notion (requires NOTION_TOKEN)
#
# Flags:
#   --dry-run                     Print the plan, do not execute
#   --skip-deploy                 Skip the git commit+push step
#
# Usage:
#   ./scripts/agency_pipeline.sh --task "Add dark-mode toggle to settings"
#   ./scripts/agency_pipeline.sh --issue-url https://github.com/owner/repo/issues/42
#   ./scripts/agency_pipeline.sh --task "Refactor auth" --dry-run
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── colours ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

# ── globals ────────────────────────────────────────────────────────
PIPELINE_ID=$(date +%s%N | cut -b1-13)
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/agency_pipeline_${PIPELINE_ID}.log"
mkdir -p "$LOG_DIR"

log() {
    local lvl=$1; shift
    local colour=$NC
    case "$lvl" in
        INFO)  colour=$CYAN   ;;
        WARN)  colour=$YELLOW ;;
        ERROR) colour=$RED    ;;
        OK)    colour=$GREEN  ;;
    esac
    printf "${colour}[%s] [%s]${NC} %s\n" "$(date '+%H:%M:%S')" "$lvl" "$*" | tee -a "$LOG_FILE"
}

# ── arg parsing ────────────────────────────────────────────────────
TASK=""
ISSUE_URL=""
NOTION_TASK_ID=""
DRY_RUN=false
SKIP_DEPLOY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --task)            TASK="$2";            shift 2 ;;
        --issue-url)       ISSUE_URL="$2";       shift 2 ;;
        --notion-task-id)  NOTION_TASK_ID="$2";  shift 2 ;;
        --dry-run)         DRY_RUN=true;         shift   ;;
        --skip-deploy)     SKIP_DEPLOY=true;     shift   ;;
        *)                 log ERROR "Unknown flag: $1"; exit 1 ;;
    esac
done

# ── resolve task from source ───────────────────────────────────────
if [[ -n "$ISSUE_URL" ]]; then
    log INFO "Fetching GitHub issue: $ISSUE_URL"
    REPO_PATH=$(echo "$ISSUE_URL" | sed 's|https://github.com/||;s|/issues/.*||')
    ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oP '/issues/\K\d+')
    TASK=$(gh issue view "$ISSUE_NUM" --repo "$REPO_PATH" \
           --json title,body --jq '.title + "\n\n" + .body' 2>/dev/null || echo "")
fi

if [[ -n "$NOTION_TASK_ID" && -z "$TASK" ]]; then
    log INFO "Fetching Notion task: $NOTION_TASK_ID"
    # Notion fetch via the notion_integration tool would go here.
    # For now fall back to the task ID as a label.
    TASK="Notion task ${NOTION_TASK_ID}"
fi

if [[ -z "$TASK" ]]; then
    log ERROR "No task provided. Use --task, --issue-url, or --notion-task-id"
    exit 1
fi

# ── header ─────────────────────────────────────────────────────────
log INFO "============================================"
log INFO "  AI AGENCY PIPELINE"
log INFO "  ID : ${PIPELINE_ID}"
log INFO "============================================"
log INFO "Task : ${TASK:0:120}"
log INFO "Dry  : ${DRY_RUN}"
log INFO "--------------------------------------------"

# ── helper: run an Agent Zero one-shot ─────────────────────────────
# Spins up a temporary AgentContext, sends a message, waits for the
# monologue to return, prints the result.  Profile is optional.
run_agent() {
    local PROFILE="$1"
    local MESSAGE="$2"

    python3 -c "
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('$0'))))

from agent import AgentContext, UserMessage
from initialize import initialize_agent

config = initialize_agent()
if '${PROFILE}':
    config.profile = '${PROFILE}'

ctx = AgentContext(config=config, name='pipeline-${PIPELINE_ID}')
agent = ctx.agent0
agent.hist_add_user_message(UserMessage(message='''${MESSAGE}''', attachments=[]))

async def go():
    return await agent.monologue()

result = asyncio.run(go())
print(result if result else '')
AgentContext.remove(ctx.id)
" 2>&1
}

# ─── STAGE 1: SCAN ─────────────────────────────────────────────────
log INFO "[1/5] Scanning repository and requirements..."

SCAN_OUT=$(run_agent "github-repo-scanner" \
    "Scan the current repository for context relevant to this task: ${TASK}. \
     Return a structured JSON with current_state, gaps, risks, and recommended subtasks." \
)

log INFO "Scan complete: ${SCAN_OUT:0:160}..."

# ─── STAGE 2: PLAN ─────────────────────────────────────────────────
log INFO "[2/5] Generating parallel implementation plan..."

PLAN_OUT=$(run_agent "" \
    "Given this scan result:\n${SCAN_OUT}\n\
     Create a parallel implementation plan for: ${TASK}.\n\
     Output ONLY a valid JSON array of task objects:\n\
     [{\"message\": \"specific instruction\", \"profile\": \"developer|researcher\"}]\n\
     Each task must be independently executable (no inter-task dependencies).\n\
     Maximum 6 tasks." \
)

log INFO "Plan: ${PLAN_OUT:0:200}..."

if [[ "$DRY_RUN" == true ]]; then
    log WARN "DRY RUN -- stopping before implementation."
    log WARN "Plan:"
    echo "$PLAN_OUT"
    exit 0
fi

# ─── STAGE 3: IMPLEMENT (parallel) ─────────────────────────────────
log INFO "[3/5] Implementing in parallel..."

IMPL_OUT=$(python3 -c "
import asyncio, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath('$0'))))

from agent import AgentContext, UserMessage
from initialize import initialize_agent

config = initialize_agent()
ctx = AgentContext(config=config, name='pipeline-impl-${PIPELINE_ID}')
agent = ctx.agent0

# Build the parallel_delegate invocation
try:
    tasks = json.loads('''${PLAN_OUT}''')
except Exception:
    tasks = [{'message': '${TASK}', 'profile': 'developer'}]

msg = json.dumps({'tool_name': 'parallel_delegate', 'tool_args': {'tasks': tasks}})
agent.hist_add_user_message(UserMessage(message=msg, attachments=[]))

async def go():
    return await agent.monologue()

result = asyncio.run(go())
print(result if result else '')
AgentContext.remove(ctx.id)
" 2>&1)

log INFO "Implementation complete."

# ─── STAGE 4: TEST ─────────────────────────────────────────────────
log INFO "[4/5] Running tests and linting..."

TEST_OUT=$(run_agent "developer" \
    "Run the full test suite and linter for this project. \
     If any failures are trivial (typo, missing import) fix them in place and re-run. \
     Report: STATUS (PASS|FAIL), tests passed/failed, linter status, any issues." \
)

log INFO "Test result: ${TEST_OUT:0:200}..."

# Check for explicit FAIL
if echo "$TEST_OUT" | grep -qi "STATUS: FAIL"; then
    log WARN "Tests reported FAIL -- skipping deploy. Review output above."
    SKIP_DEPLOY=true
fi

# ─── STAGE 5: DEPLOY ───────────────────────────────────────────────
if [[ "$SKIP_DEPLOY" == true ]]; then
    log WARN "[5/5] Deploy skipped (--skip-deploy or test failure)."
else
    log INFO "[5/5] Committing and pushing..."
    run_agent "developer" \
        "Commit all changed files with message: 'feat: ${TASK:0:60}'. \
         Push to the current branch. Report the commit hash and branch."
fi

# ─── DONE ──────────────────────────────────────────────────────────
log OK  "============================================"
log OK  "  PIPELINE COMPLETE -- ID ${PIPELINE_ID}"
log OK  "  Log: ${LOG_FILE}"
log OK  "============================================"

# TTS announcement (best-effort, never blocks exit)
python3 "$(dirname "$0")/tts_announce.py" \
    "Agency pipeline complete. Task delivered." &>/dev/null &

exit 0
