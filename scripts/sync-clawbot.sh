#!/bin/bash

################################################################################
# ClawBot → Agent Zero Sync Script
#
# Purpose: Manually synchronize updates from ClawBot repository to Agent Zero
# Usage: ./scripts/sync-clawbot.sh [--dry-run] [--no-merge] [--interactive]
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLAWBOT_REPO="https://github.com/executiveusa/clawdbot-Whatsapp-agent.git"
CLAWBOT_BRANCH="main"
CLAWBOT_REMOTE="clawbot-upstream"
DRY_RUN=false
NO_MERGE=false
INTERACTIVE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    --no-merge) NO_MERGE=true; shift ;;
    --interactive) INTERACTIVE=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ClawBot → Agent Zero Synchronization             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check Git Status
echo -e "${YELLOW}[1/7]${NC} Checking git status..."
if [[ $(git status --porcelain) ]]; then
  echo -e "${RED}❌ ERROR: Repository has uncommitted changes${NC}"
  git status
  exit 1
fi
echo -e "${GREEN}✅ Repository is clean${NC}"
echo ""

# Step 2: Configure Git
echo -e "${YELLOW}[2/7]${NC} Configuring Git..."
git config --global user.name "Agent Zero Sync" || true
git config --global user.email "sync@agent-zero.local" || true
echo -e "${GREEN}✅ Git configured${NC}"
echo ""

# Step 3: Add ClawBot remote
echo -e "${YELLOW}[3/7]${NC} Adding ClawBot remote..."
if git remote get-url $CLAWBOT_REMOTE &>/dev/null; then
  echo "Updating existing remote..."
  git remote set-url $CLAWBOT_REMOTE "$CLAWBOT_REPO"
else
  echo "Adding new remote..."
  git remote add $CLAWBOT_REMOTE "$CLAWBOT_REPO"
fi
echo -e "${GREEN}✅ ClawBot remote configured${NC}"
echo ""

# Step 4: Fetch Updates
echo -e "${YELLOW}[4/7]${NC} Fetching ClawBot updates..."
git fetch $CLAWBOT_REMOTE $CLAWBOT_BRANCH
echo -e "${GREEN}✅ Updates fetched${NC}"
echo ""

# Step 5: Check for Updates
echo -e "${YELLOW}[5/7]${NC} Checking for new commits..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMITS_BEHIND=$(git rev-list --count $CURRENT_BRANCH..$CLAWBOT_REMOTE/$CLAWBOT_BRANCH)

if [ "$COMMITS_BEHIND" -eq 0 ]; then
  echo -e "${GREEN}✅ Agent Zero is already up to date!${NC}"
  exit 0
fi

echo -e "${YELLOW}Agent Zero is behind by ${COMMITS_BEHIND} commits${NC}"
echo ""
echo -e "${BLUE}Latest changes in ClawBot:${NC}"
git log --oneline $CURRENT_BRANCH..$CLAWBOT_REMOTE/$CLAWBOT_BRANCH | head -10
echo ""

# Step 6: Interactive confirmation
if [ "$INTERACTIVE" = true ]; then
  read -p "Continue with merge? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Sync cancelled${NC}"
    exit 0
  fi
fi

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}📋 DRY RUN MODE - No changes will be made${NC}"
  echo ""
  echo -e "${BLUE}What would happen:${NC}"
  git log --stat $CURRENT_BRANCH..$CLAWBOT_REMOTE/$CLAWBOT_BRANCH
  exit 0
fi

if [ "$NO_MERGE" = true ]; then
  echo -e "${YELLOW}📋 FETCH ONLY - No merge will be performed${NC}"
  echo ""
  echo -e "${BLUE}Commits available to merge:${NC}"
  git log --oneline $CURRENT_BRANCH..$CLAWBOT_REMOTE/$CLAWBOT_BRANCH
  exit 0
fi

# Step 7: Merge Updates
echo -e "${YELLOW}[6/7]${NC} Merging ClawBot updates..."
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
SYNC_BRANCH="sync/clawbot-$TIMESTAMP"

echo "Creating branch: $SYNC_BRANCH"
git checkout -b "$SYNC_BRANCH"

echo "Merging updates (using ClawBot's version for conflicts)..."
if git merge "$CLAWBOT_REMOTE/$CLAWBOT_BRANCH" -X theirs --no-edit -m "🔄 Sync: ClawBot updates ($COMMITS_BEHIND commits)"; then
  echo -e "${GREEN}✅ Merge successful${NC}"
else
  echo -e "${YELLOW}⚠️ Merge conflicts detected - resolving${NC}"

  # List conflicted files
  echo ""
  echo -e "${BLUE}Conflicted files:${NC}"
  git diff --name-only --diff-filter=U
  echo ""

  # Resolve using ClawBot's version
  git diff --name-only --diff-filter=U | while read file; do
    echo "Resolving: $file (using ClawBot version)"
    git checkout --theirs "$file"
    git add "$file"
  done

  git commit -m "🔄 Merge: Resolved conflicts (ClawBot versions)" --no-edit
  echo -e "${GREEN}✅ Conflicts resolved${NC}"
fi
echo ""

# Step 8: Validate Integration
echo -e "${YELLOW}[7/7]${NC} Validating integration..."

VALIDATION_PASSED=true

# Check critical Agent Zero files
for file in "agent.py" "requirements.txt" "docker-compose.yml"; do
  if [ ! -f "$file" ]; then
    echo -e "${RED}❌ ERROR: $file missing after merge!${NC}"
    VALIDATION_PASSED=false
  fi
done

if [ "$VALIDATION_PASSED" = false ]; then
  echo ""
  echo -e "${RED}❌ Integration validation failed!${NC}"
  echo "You may need to manually restore Agent Zero files"
  exit 1
fi

echo -e "${GREEN}✅ Integration validation passed${NC}"
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ Synchronization Complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Branch: $SYNC_BRANCH"
echo "  Commits merged: $COMMITS_BEHIND"
echo "  Status: $(git status --porcelain | wc -l) files changed"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review changes: git diff main"
echo "  2. Test the integration: python agent.py --test"
echo "  3. Create a PR: git push origin $SYNC_BRANCH"
echo ""
