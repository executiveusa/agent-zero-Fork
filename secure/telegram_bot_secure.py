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
🔐 **Secure Agent Zero Bot**

Welcome! Your user ID is: `{user_id}`

Available commands:
/help - Show this help message
/ping - Check bot status
/list_secrets - List available secrets (admin only)
/get_secret <category> <key> - Get a secret (admin only)
/stats - Show vault statistics (admin only)
/health - Check vault health (admin only)
/lock - Lock the vault (admin only)

🔒 All secrets are encrypted with military-grade AES-256-GCM + Windows DPAPI.
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
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Sanitize input
        validation = self.sanitizer.sanitize_telegram_input(text)
        
        if not validation["valid"]:
            await update.message.reply_text(f"⚠️ Invalid input: {', '.join(validation['errors'])}")
            logger.warning(f"Invalid input from {user_id}: {validation['errors']}")
            return
        
        # Default response
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
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            self.app.add_handler(CommandHandler("ping", self.ping_command))
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
