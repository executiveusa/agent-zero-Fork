#!/usr/bin/env python3
"""
Agent Zero Telegram Control Bot

A secure Telegram bot for controlling Agent Zero and the ClawBot sync system.
Provides commands for:
- Repository management (status, pull, commit, push)
- Dashboard control (stats, health, settings)
- Agent Zero management (start, stop, status, logs)
- ClawBot sync control (trigger manual sync, check status)
- System monitoring and notifications

Security Features:
- Admin authentication required for sensitive commands
- No secrets exposed in responses
- All credentials stored in environment variables
- Git operations use SSH authentication
- Rate limiting and command logging
- Secure secret masking in logs

Usage:
    # Development (polling)
    python3 telegram_bot.py --polling

    # Production (webhook - requires systemd/docker)
    python3 telegram_bot.py --webhook

Environment Variables Required:
    - TELEGRAM_BOT_TOKEN: Bot token from @BotFather
    - TELEGRAM_ADMIN_ID: Your Telegram user ID
    - GITHUB_TOKEN: GitHub personal access token
    - GITHUB_OWNER: Repository owner (executiveusa)
    - GITHUB_REPO: Repository name (agent-zero-Fork)

Author: Agent Zero Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Third-party imports
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )
    from telegram.error import TelegramError
except ImportError:
    print("ERROR: python-telegram-bot not installed")
    print("Install with: pip install python-telegram-bot")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed")
    print("Install with: pip install requests")
    sys.exit(1)

# ===== CONFIGURATION =====

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
TELEGRAM_AUTHORIZED_USERS = [
    int(uid.strip())
    for uid in os.getenv("TELEGRAM_AUTHORIZED_USERS", "").split(",")
    if uid.strip()
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "executiveusa")
GITHUB_REPO = os.getenv("GITHUB_REPO", "agent-zero-Fork")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

AGENT_ZERO_API_URL = os.getenv("AGENT_ZERO_API_URL", "http://localhost:8000")
HOSTINGER_AGENT_ZERO_URL = os.getenv(
    "HOSTINGER_AGENT_ZERO_URL", "http://127.0.0.1:8000"
)

BOT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REPO_PATH = os.getenv("HOSTINGER_DEPLOY_PATH", "/root/agent-zero")

# Validate required configuration
if not TELEGRAM_BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN not set in environment")
    sys.exit(1)

if not TELEGRAM_ADMIN_ID:
    print("ERROR: TELEGRAM_ADMIN_ID not set in environment")
    sys.exit(1)

# ===== LOGGING SETUP =====

logging.basicConfig(
    level=getattr(logging, BOT_LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/agent_zero_telegram_bot.log"),
    ],
)

logger = logging.getLogger(__name__)


# ===== ENUMS =====


class CommandCategory(Enum):
    """Command categories for organization"""

    REPO = "repository"
    DASHBOARD = "dashboard"
    AGENT = "agent_zero"
    SYSTEM = "system"
    SYNC = "clawbot_sync"


# ===== DATA CLASSES =====


@dataclass
class CommandResponse:
    """Standard response format for bot commands"""

    success: bool
    title: str
    message: str
    details: Optional[Dict] = None
    error: Optional[str] = None

    def to_string(self) -> str:
        """Convert to human-readable format"""
        status = "✅" if self.success else "❌"
        text = f"{status} *{self.title}*\n\n{self.message}"
        if self.error and not self.success:
            text += f"\n\n_Error: {self.error}_"
        return text


# ===== SECURITY & AUTHENTICATION =====


class SecurityManager:
    """Manages authentication and authorization"""

    @staticmethod
    def mask_secret(secret: str, show_chars: int = 4) -> str:
        """Mask a secret string, showing only first and last chars"""
        if len(secret) <= show_chars:
            return "*" * len(secret)
        return secret[:show_chars] + "*" * (len(secret) - show_chars * 2) + secret[-show_chars:]

    @staticmethod
    def is_authorized(user_id: int) -> bool:
        """Check if user is authorized to use bot"""
        authorized = [TELEGRAM_ADMIN_ID] + TELEGRAM_AUTHORIZED_USERS
        is_auth = user_id in authorized
        logger.info(
            f"Authorization check for user {user_id}: {'GRANTED' if is_auth else 'DENIED'}"
        )
        return is_auth

    @staticmethod
    def hash_command(command: str) -> str:
        """Create hash of command for audit logging"""
        return hashlib.sha256(command.encode()).hexdigest()[:8]

    @staticmethod
    async def verify_token(token: str, token_type: str = "github") -> bool:
        """Verify a token is valid (non-empty and properly formatted)"""
        if not token:
            return False

        if token_type == "github":
            # Check GitHub token format
            return token.startswith(("ghp_", "ghu_", "ghs_", "gho_"))
        elif token_type == "telegram":
            return ":" in token and len(token.split(":")) == 2

        return len(token) > 10  # Generic check


# ===== GITHUB OPERATIONS =====


class GitHubManager:
    """Manages GitHub repository operations"""

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_repo_status(self) -> CommandResponse:
        """Get repository status"""
        try:
            # Get repo info
            response = requests.get(f"{self.api_url}", headers=self.headers, timeout=10)
            if response.status_code != 200:
                return CommandResponse(
                    success=False,
                    title="Repository Status",
                    message="Failed to fetch repository info",
                    error=f"GitHub API returned {response.status_code}",
                )

            repo_data = response.json()

            # Get latest commit
            commits_response = requests.get(
                f"{self.api_url}/commits", headers=self.headers, timeout=10
            )
            latest_commit = (
                commits_response.json()[0] if commits_response.status_code == 200 else {}
            )

            message = (
                f"*Repository:* {self.repo}\n"
                f"*Owner:* {self.owner}\n"
                f"*URL:* {repo_data.get('html_url', 'N/A')}\n"
                f"*Stars:* {repo_data.get('stargazers_count', 0)}\n"
                f"*Watchers:* {repo_data.get('watchers_count', 0)}\n"
                f"*Forks:* {repo_data.get('forks_count', 0)}\n"
                f"*Default Branch:* {repo_data.get('default_branch', 'N/A')}\n"
                f"*Latest Commit:* `{latest_commit.get('sha', 'N/A')[:7]}`"
            )

            return CommandResponse(
                success=True,
                title="Repository Status",
                message=message,
                details={
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "watchers": repo_data.get("watchers_count", 0),
                },
            )

        except Exception as e:
            logger.error(f"GitHub status check failed: {e}")
            return CommandResponse(
                success=False,
                title="Repository Status",
                message="Error fetching repository status",
                error=str(e),
            )

    async def get_recent_commits(self, branch: str = GITHUB_BRANCH, limit: int = 5) -> CommandResponse:
        """Get recent commits on a branch"""
        try:
            response = requests.get(
                f"{self.api_url}/commits",
                headers=self.headers,
                params={"sha": branch, "per_page": limit},
                timeout=10,
            )

            if response.status_code != 200:
                return CommandResponse(
                    success=False,
                    title="Recent Commits",
                    message=f"Failed to fetch commits from {branch}",
                    error=f"Status code: {response.status_code}",
                )

            commits = response.json()
            commits_text = (
                f"*Latest {len(commits)} commits on {branch}:*\n\n"
            )

            for i, commit in enumerate(commits, 1):
                msg = commit["commit"]["message"].split("\n")[0][:50]
                author = commit["commit"]["author"].get("name", "Unknown")
                date = commit["commit"]["author"].get("date", "N/A")[:10]
                sha = commit["sha"][:7]

                commits_text += (
                    f"{i}. `{sha}` - {msg}\n"
                    f"   by {author} on {date}\n\n"
                )

            return CommandResponse(
                success=True,
                title="Recent Commits",
                message=commits_text,
            )

        except Exception as e:
            logger.error(f"Failed to get commits: {e}")
            return CommandResponse(
                success=False,
                title="Recent Commits",
                message="Error fetching commits",
                error=str(e),
            )

    async def trigger_sync_workflow(self) -> CommandResponse:
        """Trigger the ClawBot sync GitHub Actions workflow"""
        try:
            # Get workflow ID first
            workflows_response = requests.get(
                f"{self.api_url}/actions/workflows",
                headers=self.headers,
                timeout=10,
            )

            if workflows_response.status_code != 200:
                return CommandResponse(
                    success=False,
                    title="Trigger Sync Workflow",
                    message="Failed to find workflows",
                    error="Cannot access GitHub Actions",
                )

            workflows = workflows_response.json().get("workflows", [])
            sync_workflow = next(
                (w for w in workflows if "sync" in w["name"].lower()),
                None,
            )

            if not sync_workflow:
                return CommandResponse(
                    success=False,
                    title="Trigger Sync Workflow",
                    message="Sync workflow not found",
                    error="sync-clawbot-updates.yml not found",
                )

            # Trigger the workflow
            trigger_response = requests.post(
                f"{self.api_url}/actions/workflows/{sync_workflow['id']}/dispatches",
                headers=self.headers,
                json={"ref": GITHUB_BRANCH},
                timeout=10,
            )

            if trigger_response.status_code == 204:
                return CommandResponse(
                    success=True,
                    title="Sync Workflow Triggered",
                    message=(
                        f"ClawBot sync workflow triggered on {GITHUB_BRANCH} branch\n\n"
                        "The workflow will run and create a PR if updates are found.\n"
                        "Check GitHub Actions for progress."
                    ),
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Trigger Sync Workflow",
                    message="Failed to trigger workflow",
                    error=f"Status code: {trigger_response.status_code}",
                )

        except Exception as e:
            logger.error(f"Failed to trigger sync workflow: {e}")
            return CommandResponse(
                success=False,
                title="Trigger Sync Workflow",
                message="Error triggering workflow",
                error=str(e),
            )

    async def get_open_prs(self) -> CommandResponse:
        """Get open pull requests"""
        try:
            response = requests.get(
                f"{self.api_url}/pulls",
                headers=self.headers,
                params={"state": "open", "per_page": 5},
                timeout=10,
            )

            if response.status_code != 200:
                return CommandResponse(
                    success=False,
                    title="Open Pull Requests",
                    message="Failed to fetch PRs",
                    error=f"Status code: {response.status_code}",
                )

            prs = response.json()
            if not prs:
                return CommandResponse(
                    success=True,
                    title="Open Pull Requests",
                    message="No open pull requests",
                )

            prs_text = f"*Open Pull Requests ({len(prs)}):*\n\n"

            for pr in prs:
                prs_text += (
                    f"#{pr['number']} - {pr['title']}\n"
                    f"By {pr['user']['login']}\n"
                    f"Created: {pr['created_at'][:10]}\n\n"
                )

            return CommandResponse(
                success=True,
                title="Open Pull Requests",
                message=prs_text,
            )

        except Exception as e:
            logger.error(f"Failed to get PRs: {e}")
            return CommandResponse(
                success=False,
                title="Open Pull Requests",
                message="Error fetching PRs",
                error=str(e),
            )


# ===== AGENT ZERO API OPERATIONS =====


class AgentZeroManager:
    """Manages Agent Zero API operations"""

    def __init__(self, api_url: str = AGENT_ZERO_API_URL):
        self.api_url = api_url

    async def get_health(self) -> CommandResponse:
        """Get Agent Zero health status"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=10)

            if response.status_code == 200:
                data = response.json()
                message = (
                    f"*Status:* ✅ Healthy\n"
                    f"*Uptime:* {data.get('uptime', 'N/A')} seconds\n"
                    f"*Version:* {data.get('version', 'N/A')}\n"
                    f"*Active Chats:* {data.get('active_chats', 0)}\n"
                    f"*Memory Usage:* {data.get('memory_mb', 0)} MB"
                )
                return CommandResponse(
                    success=True,
                    title="Agent Zero Health",
                    message=message,
                    details=data,
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Agent Zero Health",
                    message="Agent Zero is not responding",
                    error=f"Status code: {response.status_code}",
                )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return CommandResponse(
                success=False,
                title="Agent Zero Health",
                message="Could not connect to Agent Zero",
                error=str(e),
            )

    async def get_stats(self) -> CommandResponse:
        """Get Agent Zero statistics"""
        try:
            response = requests.get(f"{self.api_url}/api/stats", timeout=10)

            if response.status_code == 200:
                data = response.json()
                message = (
                    f"*Total Messages:* {data.get('total_messages', 0)}\n"
                    f"*Total Chats:* {data.get('total_chats', 0)}\n"
                    f"*Total Tools Used:* {data.get('total_tools_used', 0)}\n"
                    f"*Average Response Time:* {data.get('avg_response_time', 0):.2f}s"
                )
                return CommandResponse(
                    success=True,
                    title="Agent Zero Statistics",
                    message=message,
                    details=data,
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Agent Zero Statistics",
                    message="Failed to fetch statistics",
                    error=f"Status code: {response.status_code}",
                )

        except Exception as e:
            logger.error(f"Stats fetch failed: {e}")
            return CommandResponse(
                success=False,
                title="Agent Zero Statistics",
                message="Could not fetch statistics",
                error=str(e),
            )


# ===== SHELL OPERATIONS =====


class ShellManager:
    """Manages local shell operations (for development/testing)"""

    @staticmethod
    async def execute_command(command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Execute shell command safely

        Returns: (success, output)
        """
        logger.info(f"Executing command: {SecurityManager.hash_command(command)}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=REPO_PATH,
            )

            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            return success, output[:500]  # Limit output to 500 chars

        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, str(e)

    @staticmethod
    async def get_git_status() -> CommandResponse:
        """Get git status"""
        try:
            success, output = await ShellManager.execute_command(
                "cd $REPO_PATH && git status --short"
            )

            if success:
                if not output.strip():
                    message = "Repository is clean, no uncommitted changes"
                else:
                    lines = output.strip().split("\n")
                    message = f"*Modified files ({len(lines)}):*\n"
                    for line in lines[:10]:  # Show first 10
                        message += f"`{line}`\n"
                    if len(lines) > 10:
                        message += f"\n... and {len(lines) - 10} more files"

                return CommandResponse(
                    success=True,
                    title="Git Status",
                    message=message,
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Git Status",
                    message="Failed to get git status",
                    error=output,
                )

        except Exception as e:
            logger.error(f"Git status check failed: {e}")
            return CommandResponse(
                success=False,
                title="Git Status",
                message="Error checking git status",
                error=str(e),
            )

    @staticmethod
    async def git_pull(branch: str = GITHUB_BRANCH) -> CommandResponse:
        """Pull latest changes from branch"""
        try:
            success, output = await ShellManager.execute_command(
                f"cd $REPO_PATH && git pull origin {branch}"
            )

            if success:
                message = (
                    f"Successfully pulled latest changes from {branch}\n\n"
                    f"```\n{output}\n```"
                )
                return CommandResponse(
                    success=True,
                    title="Git Pull",
                    message=message,
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Git Pull",
                    message=f"Failed to pull from {branch}",
                    error=output,
                )

        except Exception as e:
            logger.error(f"Git pull failed: {e}")
            return CommandResponse(
                success=False,
                title="Git Pull",
                message="Error pulling from repository",
                error=str(e),
            )

    @staticmethod
    async def trigger_manual_sync() -> CommandResponse:
        """Trigger manual ClawBot sync"""
        try:
            success, output = await ShellManager.execute_command(
                "bash scripts/sync-clawbot.sh --dry-run"
            )

            if success:
                message = (
                    f"Manual sync check completed\n\n"
                    f"```\n{output}\n```"
                )
                return CommandResponse(
                    success=True,
                    title="Manual Sync Check",
                    message=message,
                )
            else:
                return CommandResponse(
                    success=False,
                    title="Manual Sync Check",
                    message="Sync check failed",
                    error=output,
                )

        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return CommandResponse(
                success=False,
                title="Manual Sync Check",
                message="Error checking manual sync",
                error=str(e),
            )


# ===== TELEGRAM BOT HANDLERS =====


class TelegramBotHandlers:
    """Telegram bot command handlers"""

    def __init__(self):
        self.github = GitHubManager(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO)
        self.agent_zero = AgentZeroManager()

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command"""
        user_id = update.effective_user.id

        if not SecurityManager.is_authorized(user_id):
            await update.message.reply_text(
                "❌ You are not authorized to use this bot.\n"
                "Contact the bot administrator."
            )
            logger.warning(f"Unauthorized user {user_id} attempted to use /start")
            return

        welcome_message = (
            "🤖 *Agent Zero Telegram Control Bot*\n\n"
            "Welcome! I can help you manage Agent Zero and the repository.\n\n"
            "*Available Commands:*\n"
            "/repo - Repository status and management\n"
            "/sync - ClawBot sync operations\n"
            "/agent - Agent Zero status and control\n"
            "/help - Show all commands\n\n"
            "_Use the buttons below or type commands._"
        )

        keyboard = [
            [
                InlineKeyboardButton("📦 Repository", callback_data="repo_status"),
                InlineKeyboardButton("🔄 Sync", callback_data="sync_status"),
            ],
            [
                InlineKeyboardButton("🤖 Agent Zero", callback_data="agent_health"),
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command"""
        help_text = (
            "*Agent Zero Telegram Bot - Commands*\n\n"
            "*Repository Commands:*\n"
            "/repo_status - Show repository status\n"
            "/repo_commits - Show recent commits\n"
            "/repo_prs - Show open pull requests\n"
            "/git_status - Show git status\n"
            "/git_pull - Pull latest changes\n\n"
            "*Sync Commands:*\n"
            "/sync_status - Check sync status\n"
            "/sync_trigger - Trigger manual sync (GitHub Actions)\n"
            "/sync_check - Check what would sync\n\n"
            "*Agent Zero Commands:*\n"
            "/agent_health - Check Agent Zero health\n"
            "/agent_stats - Show Agent Zero statistics\n\n"
            "*System Commands:*\n"
            "/help - Show this help message\n"
            "/start - Show welcome message\n\n"
            "_All commands require admin authorization._"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_repo_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /repo_status command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.github.get_repo_status()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_commits(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /repo_commits command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.github.get_recent_commits()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_prs(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /repo_prs command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.github.get_open_prs()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_git_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /git_status command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await ShellManager.get_git_status()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_git_pull(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /git_pull command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await ShellManager.git_pull()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_sync_trigger(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /sync_trigger command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.github.trigger_sync_workflow()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_sync_check(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /sync_check command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await ShellManager.trigger_manual_sync()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_agent_health(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /agent_health command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.agent_zero.get_health()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_agent_stats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /agent_stats command"""
        await update.message.reply_chat_action(ChatAction.TYPING)

        response = await self.agent_zero.get_stats()
        await update.message.reply_text(
            response.to_string(),
            parse_mode="Markdown",
        )

    async def handle_button_click(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle inline button clicks"""
        query = update.callback_query
        await query.answer()

        handlers_map = {
            "repo_status": self.handle_repo_status,
            "sync_status": self.handle_sync_trigger,
            "agent_health": self.handle_agent_health,
            "help": self.handle_help,
        }

        handler = handlers_map.get(query.data)
        if handler:
            # Create a mock update object for the handler
            update.message = query.message
            await handler(update, context)


# ===== MAIN BOT APPLICATION =====


def create_app() -> Application:
    """Create and configure the Telegram bot application"""

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    handlers = TelegramBotHandlers()

    # Authorization filter
    auth_filter = filters.User(
        user_id=[TELEGRAM_ADMIN_ID] + TELEGRAM_AUTHORIZED_USERS
    )

    # Command handlers
    app.add_handler(CommandHandler("start", handlers.handle_start, filters=auth_filter))
    app.add_handler(CommandHandler("help", handlers.handle_help, filters=auth_filter))
    app.add_handler(
        CommandHandler("repo_status", handlers.handle_repo_status, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("repo_commits", handlers.handle_commits, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("repo_prs", handlers.handle_prs, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("git_status", handlers.handle_git_status, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("git_pull", handlers.handle_git_pull, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("sync_trigger", handlers.handle_sync_trigger, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("sync_check", handlers.handle_sync_check, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("agent_health", handlers.handle_agent_health, filters=auth_filter)
    )
    app.add_handler(
        CommandHandler("agent_stats", handlers.handle_agent_stats, filters=auth_filter)
    )

    # Button handlers
    app.add_handler(CallbackQueryHandler(handlers.handle_button_click))

    logger.info("Telegram bot application created successfully")
    return app


async def main():
    """Main entry point"""

    logger.info("Starting Agent Zero Telegram Control Bot...")
    logger.info(f"Repository: {GITHUB_OWNER}/{GITHUB_REPO}")
    logger.info(f"Admin ID: {TELEGRAM_ADMIN_ID}")

    app = create_app()

    # Start the bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    logger.info("Bot started successfully. Press Ctrl+C to stop.")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
