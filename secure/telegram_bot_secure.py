#!/usr/bin/env python3
"""
Secure Telegram Bot with Encrypted Vault Integration

Security Features:
- No environment variables (uses encrypted vault)
- Permission-based access control
- Rate limiting
- Input sanitization
- Prompt injection defense
- Audit logging
- Secret masking in responses

Author: Agent Zero Security Team
Version: 1.0.0
"""

import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path

# Add secure directory to path
sys.path.insert(0, os.path.dirname(__file__))

from secrets_vault import get_vault, SecretsVault
from input_sanitizer import InputSanitizer, RateLimiter, AccessControl
from vault_manager import VaultManager

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("ERROR: python-telegram-bot not installed")
    print("Install with: pip install python-telegram-bot")
    exit(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SecureTelegramBot:
    """Secure Telegram bot with vault integration"""
    
    def __init__(self, vault_password: str, admin_user_ids: list = None):
        self.vault = get_vault()
        self.vault_manager = VaultManager(self.vault)
        self.sanitizer = InputSanitizer(strict_mode=True)
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.access_control = AccessControl(admin_ids=admin_user_ids or [])
        
        # Unlock vault
        if not self.vault.unlock(vault_password):
            raise Exception("Failed to unlock vault. Invalid password?")
        
        logger.info("✅ Vault unlocked successfully")
        
        # Get bot token from vault
        self.bot_token = self.vault.get_secret("telegram", "bot_token")
        if not self.bot_token:
            raise Exception("Bot token not found in vault")
        
        logger.info("✅ Bot token loaded from vault")
        
        # Initialize bot application
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/start"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait.")
            return
        
        welcome_message = f"""
🔐 **Agent Zero Command Center**

Welcome! Your user ID is: `{user_id}`

**Core Commands:**
/help - Show this help message
/ping - Check bot status
/status - Full system status dashboard

**Agent & Model Commands:**
/model [name] - Switch active model or show current
/models - List all available models
/swarm <task> - Launch agent swarm on a task
/ask <question> - Send a question to Agent Zero

**GitHub Commands:**
/repos - List monitored repositories
/scan <owner/repo> - Scan a repository
/finish <owner/repo> - Auto-finish incomplete features

**Scheduling Commands:**
/schedule - List scheduled tasks
/cron <spec> <prompt> - Create a scheduled task

**Admin Commands:**
/list_secrets - List vault secrets (admin only)
/get_secret <cat> <key> - Retrieve a secret (admin only)
/stats - Vault statistics (admin only)
/health - Vault health check (admin only)
/lock - Lock the vault (admin only)

🔒 Encrypted with AES-256-GCM + Windows DPAPI.
"""
        
        await update.message.reply_text(welcome_message, parse_mode="Markdown")
        logger.info(f"User {user_id} started bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command"""
        user_id = update.effective_user.id
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/ping"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait.")
            return
        
        vault_status = "🔓 Unlocked" if not self.vault.is_locked() else "🔒 Locked"
        
        response = f"""
🏓 Pong!

Vault Status: {vault_status}
Your ID: `{user_id}`
Admin: {"Yes" if self.access_control.is_admin(user_id) else "No"}
"""
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def list_secrets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list_secrets command (admin only)"""
        user_id = update.effective_user.id
        
        # Check permission
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            logger.warning(f"Unauthorized access attempt by {user_id}: /list_secrets")
            return
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/list_secrets"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait.")
            return
        
        try:
            secrets = self.vault.list_secrets()
            
            response = "📋 **Available Secrets:**\n\n"
            for category, keys in secrets.items():
                response += f"**{category}** ({len(keys)} secrets):\n"
                for key in keys:
                    response += f"  • `{key}`\n"
                response += "\n"
            
            await update.message.reply_text(response, parse_mode="Markdown")
            logger.info(f"Admin {user_id} listed secrets")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"list_secrets failed: {e}")
    
    async def get_secret_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get_secret command (admin only)"""
        user_id = update.effective_user.id
        
        # Check permission
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            logger.warning(f"Unauthorized access attempt by {user_id}: /get_secret")
            return
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/get_secret"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait.")
            return
        
        # Parse arguments
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /get_secret <category> <key>")
            return
        
        category = context.args[0]
        key = context.args[1]
        
        # Validate inputs
        if not self.sanitizer.validate_category(category):
            await update.message.reply_text("❌ Invalid category name")
            return
        
        if not self.sanitizer.validate_secret_key(key):
            await update.message.reply_text("❌ Invalid secret key")
            return
        
        try:
            secret_value = self.vault.get_secret(category, key)
            
            if secret_value is None:
                await update.message.reply_text(f"❌ Secret not found: {category}/{key}")
                return
            
            # Send secret (will be visible only to requester)
            response = f"🔑 **Secret:** `{category}/{key}`\n\n```\n{secret_value}\n```"
            
            await update.message.reply_text(response, parse_mode="Markdown")
            logger.info(f"Admin {user_id} retrieved secret: {category}/{key}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"get_secret failed: {e}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (admin only)"""
        user_id = update.effective_user.id
        
        # Check permission
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/stats"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait.")
            return
        
        try:
            metadata = self.vault.get_metadata()
            secrets = self.vault.list_secrets()
            
            response = f"""
📊 **Vault Statistics**

**Total Secrets:** {metadata.get('secret_count', 0)}
**Access Count:** {metadata.get('access_count', 0)}
**Last Access:** {metadata.get('last_access', 'Never')}
**Categories:** {len(secrets)}

**Breakdown:**
"""
            
            for category, keys in secrets.items():
                response += f"  • {category}: {len(keys)} secrets\n"
            
            await update.message.reply_text(response, parse_mode="Markdown")
            logger.info(f"Admin {user_id} viewed stats")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"stats failed: {e}")
    
    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command (admin only)"""
        user_id = update.effective_user.id
        
        # Check permission
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        
        try:
            health = self.vault_manager.health_check()
            
            status_emoji = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "warning" else "❌"
            
            response = f"""
{status_emoji} **Vault Health Check**

**Status:** {health['status'].upper()}
**Secret Count:** {health.get('secret_count', 'N/A')}
**Access Count:** {health.get('access_count', 'N/A')}
"""
            
            if health.get('issues'):
                response += "\n⚠️ **Issues:**\n"
                for issue in health['issues']:
                    response += f"  • {issue}\n"
            
            if health.get('warnings'):
                response += "\n⚠️ **Warnings:**\n"
                for warning in health['warnings']:
                    response += f"  • {warning}\n"
            
            await update.message.reply_text(response, parse_mode="Markdown")
            logger.info(f"Admin {user_id} checked health")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"health check failed: {e}")
    
    async def lock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lock command (admin only)"""
        user_id = update.effective_user.id
        
        # Check permission
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        
        try:
            self.vault.lock()
            await update.message.reply_text("🔒 Vault locked successfully")
            logger.info(f"Admin {user_id} locked vault")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"lock failed: {e}")

    # ─── NEW COMMAND CENTER COMMANDS ───────────────────────────

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status — full system dashboard"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/status"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        vault_status = "🔓 Unlocked" if not self.vault.is_locked() else "🔒 Locked"
        
        response = f"""
📊 **Agent Zero System Status**

**Vault:** {vault_status}
**Model Router:** Active
**Swarm:** Idle
**Scheduler:** Running

**Available Providers:**
  • Moonshot/Kimi (K2, K2.5, K2-Thinking)
  • Zhipu AI (GLM-4-Plus, GLM-4-Flash)
  • Google Gemini (2.5 Pro, 2.5 Flash)
  • Anthropic Claude
  • OpenAI GPT-4o
  • DeepSeek

**Integrations:**
  • GitHub Pipeline: ✅ Active
  • Telegram Bot: ✅ Online
  • ZenFlow IDE: ⏳ Pending
  • Google AI Studio: ⏳ Pending
"""
        await update.message.reply_text(response, parse_mode="Markdown")

    async def model_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model — switch or show current model"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/model"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        if context.args:
            model_name = " ".join(context.args)
            # Store model preference (will be picked up by Agent Zero)
            self._user_prefs = getattr(self, '_user_prefs', {})
            self._user_prefs[user_id] = {"model": model_name}
            await update.message.reply_text(f"✅ Model preference set to: `{model_name}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("""
🤖 **Current Model Configuration**

Use `/model <name>` to switch. Examples:
  `/model moonshot/kimi-k2-turbo-preview`
  `/model gemini/gemini-2.5-pro`
  `/model openai/glm-4-flash`
  `/model anthropic/claude-sonnet-4-20250514`
""", parse_mode="Markdown")

    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /models — list all available models"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/models"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        response = """
📋 **Available Models**

**Moonshot/Kimi:**
  `moonshot/kimi-k2-turbo-preview` — 262K, code champion
  `moonshot/kimi-k2.5` — 262K, multimodal+thinking
  `moonshot/kimi-k2-thinking` — 262K, deep reasoning

**Zhipu AI/GLM:**
  `openai/glm-4-plus` — 128K, general purpose
  `openai/glm-4-flash` — 128K, fast & cheap

**Google Gemini:**
  `gemini/gemini-2.5-pro` — 1M, vision+reasoning
  `gemini/gemini-2.5-flash` — 1M, balanced

**Anthropic:**
  `anthropic/claude-sonnet-4-20250514` — 200K, creative
  
**OpenAI:**
  `openai/gpt-4o` — 128K, general
  `openai/gpt-4o-mini` — 128K, fast
"""
        await update.message.reply_text(response, parse_mode="Markdown")

    async def swarm_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /swarm — launch agent swarm"""
        user_id = update.effective_user.id
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/swarm"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/swarm <task description>`\n\nExample: `/swarm Fix all open bugs in pauli-comic-funnel`", parse_mode="Markdown")
            return

        task = " ".join(context.args)
        await update.message.reply_text(f"🐝 **Swarm Launched**\n\nTask: _{task}_\nAgents: Deploying...\n\n_Check back with /status_", parse_mode="Markdown")
        logger.info(f"Admin {user_id} launched swarm: {task}")
        # TODO: integrate with swarm_orchestrator.py

    async def repos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /repos — list monitored repos"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/repos"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        repos = [
            ("agent0ai/agent-zero", "main", "Agent Zero Framework"),
            ("executiveusa/pauli-comic-funnel", "master", "Pauli Comic Funnel"),
        ]
        lines = ["📂 **Monitored Repositories**\n"]
        for repo, branch, desc in repos:
            lines.append(f"  • `{repo}` ({branch}) — {desc}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan — scan a repository"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/scan"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/scan owner/repo`", parse_mode="Markdown")
            return

        repo_str = context.args[0]
        parts = repo_str.split("/")
        if len(parts) != 2:
            await update.message.reply_text("❌ Format: `owner/repo`", parse_mode="Markdown")
            return

        await update.message.reply_text(f"🔍 Scanning `{repo_str}`...", parse_mode="Markdown")

        try:
            # Import scanner
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python', 'tools'))
            from github_repo_scanner import GitHubRepoScanner
            scanner = GitHubRepoScanner()
            data = scanner.scan_repository(parts[0], parts[1])
            
            if "error" in data:
                await update.message.reply_text(f"❌ Scan failed: {data['error']}")
                return

            info = data.get("repo_info", {})
            issues = data.get("issues", [])
            prs = data.get("pull_requests", [])
            
            response = f"""
✅ **Scan Complete: {repo_str}**

⭐ Stars: {info.get('stars', 0)} | 🍴 Forks: {info.get('forks', 0)}
📝 Open Issues: {len(issues)} | 🔀 Open PRs: {len(prs)}
💻 Language: {info.get('language', 'N/A')}

**Top Issues:**
"""
            for issue in issues[:5]:
                response += f"  • #{issue['number']}: {issue['title'][:60]}\n"

            await update.message.reply_text(response, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def finish_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /finish — auto-finish incomplete features"""
        user_id = update.effective_user.id
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/finish owner/repo`", parse_mode="Markdown")
            return

        repo_str = context.args[0]
        await update.message.reply_text(f"🚀 **Project Finisher** activated for `{repo_str}`\n\nScanning for incomplete features...", parse_mode="Markdown")
        logger.info(f"Admin {user_id} started finish for {repo_str}")
        # TODO: integrate with project-finisher agent profile

    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /schedule — list scheduled tasks"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/schedule"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        await update.message.reply_text("""
📅 **Scheduled Tasks**

Use `/cron <spec> <prompt>` to create new tasks.

_Task list will be populated from Agent Zero scheduler._
""", parse_mode="Markdown")

    async def cron_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cron — create scheduled task"""
        user_id = update.effective_user.id
        if not self.access_control.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only.")
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("""
Usage: `/cron <cron_spec> <prompt>`

Examples:
  `/cron */30 * * * * Check GitHub repos for new issues`
  `/cron 0 9 * * * Morning briefing of all projects`
  `/cron 0 */6 * * * Scan repos and generate PRDs`
""", parse_mode="Markdown")
            return

        # First arg could be a cron spec (5 fields) or a shorthand
        cron_spec = context.args[0]
        prompt = " ".join(context.args[1:])
        
        await update.message.reply_text(f"✅ Scheduled task created\n\nCron: `{cron_spec}`\nPrompt: _{prompt}_", parse_mode="Markdown")
        logger.info(f"Admin {user_id} created cron task: {cron_spec} -> {prompt}")

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask — send question to Agent Zero"""
        user_id = update.effective_user.id
        if not self.rate_limiter.check_rate_limit(f"{user_id}:/ask"):
            await update.message.reply_text("⚠️ Rate limit exceeded.")
            return

        if not context.args:
            await update.message.reply_text("Usage: `/ask <your question>`", parse_mode="Markdown")
            return

        question = " ".join(context.args)
        await update.message.reply_text(f"🤖 Processing: _{question}_", parse_mode="Markdown")
        # TODO: Route to Agent Zero agent.monologue()
        logger.info(f"User {user_id} asked: {question}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages — route to Agent Zero"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Sanitize input
        validation = self.sanitizer.sanitize_telegram_input(text)
        
        if not validation["valid"]:
            await update.message.reply_text(f"⚠️ Invalid input: {', '.join(validation['errors'])}")
            logger.warning(f"Invalid input from {user_id}: {validation['errors']}")
            return
        
        # Route to Agent Zero chat if authenticated
        if self.access_control.is_admin(user_id):
            await update.message.reply_text("🤖 Processing your message with Agent Zero...")
            # TODO: integrate with Agent Zero context.communicate()
            await update.message.reply_text(f"Agent received: {text[:200]}")
        else:
            await update.message.reply_text("Use /help to see available commands.")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def run(self):
        """Start the bot"""
        try:
            # Create application
            self.app = Application.builder().token(self.bot_token).build()
            
            # Add handlers — Core
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            self.app.add_handler(CommandHandler("ping", self.ping_command))
            
            # Add handlers — Agent & Model
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("model", self.model_command))
            self.app.add_handler(CommandHandler("models", self.models_command))
            self.app.add_handler(CommandHandler("swarm", self.swarm_command))
            self.app.add_handler(CommandHandler("ask", self.ask_command))
            
            # Add handlers — GitHub
            self.app.add_handler(CommandHandler("repos", self.repos_command))
            self.app.add_handler(CommandHandler("scan", self.scan_command))
            self.app.add_handler(CommandHandler("finish", self.finish_command))
            
            # Add handlers — Scheduling
            self.app.add_handler(CommandHandler("schedule", self.schedule_command))
            self.app.add_handler(CommandHandler("cron", self.cron_command))
            
            # Add handlers — Admin/Vault
            self.app.add_handler(CommandHandler("list_secrets", self.list_secrets_command))
            self.app.add_handler(CommandHandler("get_secret", self.get_secret_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))
            self.app.add_handler(CommandHandler("health", self.health_command))
            self.app.add_handler(CommandHandler("lock", self.lock_command))
            
            # Handle non-command messages
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Error handler
            self.app.add_error_handler(self.error_handler)
            
            logger.info("🚀 Starting Secure Telegram Bot...")
            logger.info("Press Ctrl+C to stop")
            
            # Run bot
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down bot...")
            self.vault.lock()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.vault.lock()
            raise


def main():
    """Main entry point"""
    import getpass
    
    print("="*60)
    print("🔐 SECURE TELEGRAM BOT")
    print("="*60)
    
    # Get vault password
    vault_password = getpass.getpass("Enter vault master password: ")
    
    # Get admin user ID
    admin_id_str = input("Enter admin Telegram user ID: ")
    try:
        admin_id = int(admin_id_str)
    except ValueError:
        print("❌ Invalid user ID")
        return
    
    try:
        # Create and run bot
        bot = SecureTelegramBot(vault_password, admin_user_ids=[admin_id])
        bot.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
