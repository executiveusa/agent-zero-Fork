#!/bin/bash

################################################################################
# Agent Zero Telegram Bot Deployment Script
#
# Purpose: Deploy the Telegram control bot to Hostinger VPS
# Usage: ./deployment/deploy-telegram-bot.sh [--local] [--remote] [--install] [--start]
#
# This script handles:
# - Environment setup
# - Dependency installation
# - Systemd service configuration
# - Bot startup and monitoring
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_MODE="${1:-local}"  # local or remote
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BOT_FILE="$PROJECT_ROOT/telegram_bot.py"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements-telegram-bot.txt"
SERVICE_FILE="$SCRIPT_DIR/systemd/agent-zero-telegram-bot.service"
SERVICE_NAME="agent-zero-telegram-bot"
BOT_USER="root"
BOT_HOME="/root"
VENV_PATH="$BOT_HOME/venv"
LOG_FILE="/var/log/agent-zero-telegram-bot.log"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Agent Zero Telegram Bot Deployment Script           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ===== VALIDATION =====
echo -e "${YELLOW}[1/7]${NC} Validating environment..."

if [ ! -f "$BOT_FILE" ]; then
    echo -e "${RED}❌ ERROR: telegram_bot.py not found at $BOT_FILE${NC}"
    exit 1
fi

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}❌ ERROR: requirements-telegram-bot.txt not found${NC}"
    exit 1
fi

if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ ERROR: systemd service file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"
echo ""

# ===== CHECK ENVIRONMENT VARIABLES =====
echo -e "${YELLOW}[2/7]${NC} Checking environment variables..."

REQUIRED_VARS=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_ADMIN_ID"
    "GITHUB_TOKEN"
    "GITHUB_OWNER"
    "GITHUB_REPO"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "   - $var"
    done
    echo ""
    echo "Solution:"
    echo "1. Copy .env.example to .env:"
    echo "   cp $PROJECT_ROOT/.env.example $BOT_HOME/.env"
    echo "2. Edit $BOT_HOME/.env and fill in your values"
    echo "3. Source the environment:"
    echo "   source $BOT_HOME/.env"
    exit 1
fi

echo -e "${GREEN}✅ All required environment variables set${NC}"
echo ""

# ===== INSTALL PYTHON DEPENDENCIES =====
echo -e "${YELLOW}[3/7]${NC} Installing Python dependencies..."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: pip3 not found. Install with: apt-get install python3-pip${NC}"
    exit 1
fi

# Create virtual environment if needed
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install requirements
pip install -q --upgrade pip setuptools wheel
pip install -q -r "$REQUIREMENTS_FILE"

deactivate

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ===== SETUP SYSTEMD SERVICE =====
echo -e "${YELLOW}[4/7]${NC} Setting up systemd service..."

# Check if running as root or can sudo
if [ "$EUID" -eq 0 ]; then
    # Copy service file
    cp "$SERVICE_FILE" /etc/systemd/system/$SERVICE_NAME.service
    chmod 644 /etc/systemd/system/$SERVICE_NAME.service

    # Reload systemd daemon
    systemctl daemon-reload

    echo -e "${GREEN}✅ Systemd service installed${NC}"
else
    echo -e "${YELLOW}⚠️  Not running as root. Service file not installed.${NC}"
    echo "To install systemd service, run:"
    echo "  sudo cp $SERVICE_FILE /etc/systemd/system/$SERVICE_NAME.service"
    echo "  sudo systemctl daemon-reload"
fi
echo ""

# ===== CREATE LOG DIRECTORY =====
echo -e "${YELLOW}[5/7]${NC} Setting up logging..."

LOG_DIR="$(dirname "$LOG_FILE")"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# Create empty log file
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

echo -e "${GREEN}✅ Logging configured at $LOG_FILE${NC}"
echo ""

# ===== ENVIRONMENT FILE SETUP =====
echo -e "${YELLOW}[6/7]${NC} Checking environment file..."

if [ ! -f "$BOT_HOME/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found at $BOT_HOME/.env${NC}"
    echo "Creating from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$BOT_HOME/.env"
    chmod 600 "$BOT_HOME/.env"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Edit $BOT_HOME/.env and fill in your values!${NC}"
else
    echo -e "${GREEN}✅ .env file found${NC}"
    chmod 600 "$BOT_HOME/.env"
fi
echo ""

# ===== TEST BOT INITIALIZATION =====
echo -e "${YELLOW}[7/7]${NC} Testing bot initialization..."

source "$BOT_HOME/.env"
cd "$PROJECT_ROOT"

# Test Python script syntax
if python3 -m py_compile "$BOT_FILE"; then
    echo -e "${GREEN}✅ Bot script syntax valid${NC}"
else
    echo -e "${RED}❌ Bot script has syntax errors${NC}"
    exit 1
fi
echo ""

# ===== SUMMARY =====
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Edit environment file:${NC}"
echo "   nano $BOT_HOME/.env"
echo ""
echo "2. ${YELLOW}Start the bot:${NC}"
if [ "$EUID" -eq 0 ]; then
    echo "   systemctl start $SERVICE_NAME"
    echo "   systemctl enable $SERVICE_NAME  # Auto-start on reboot"
else
    echo "   python3 $BOT_FILE"
fi
echo ""
echo "3. ${YELLOW}Check status:${NC}"
if [ "$EUID" -eq 0 ]; then
    echo "   systemctl status $SERVICE_NAME"
    echo "   journalctl -u $SERVICE_NAME -f  # View logs"
else
    echo "   python3 $BOT_FILE &"
fi
echo ""
echo "4. ${YELLOW}Test commands in Telegram:${NC}"
echo "   /start"
echo "   /help"
echo "   /repo_status"
echo ""

echo -e "${BLUE}Configuration Files:${NC}"
echo "  - Environment:  $BOT_HOME/.env"
echo "  - Service:      /etc/systemd/system/$SERVICE_NAME.service"
echo "  - Log:          $LOG_FILE"
echo "  - Bot:          $BOT_FILE"
echo ""

echo -e "${GREEN}Ready to use! 🚀${NC}"
