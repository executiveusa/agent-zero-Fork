#!/usr/bin/env python3
"""Quick test to verify Telegram bot token and get user ID"""

import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set")
    exit(1)

print(f"✅ Token found: {TOKEN[:10]}...")
print("\nTesting bot connection...\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and show user their ID"""
    user = update.effective_user
    user_id = user.id
    
    message = (
        f"✅ **Bot is working!**\n\n"
        f"👤 Your Info:\n"
        f"- **User ID**: `{user_id}`\n"
        f"- **Username**: @{user.username or 'None'}\n"
        f"- **Name**: {user.first_name} {user.last_name or ''}\n\n"
        f"📋 **To enable the full bot**, set this in PowerShell:\n"
        f"`$env:TELEGRAM_ADMIN_ID = \"{user_id}\"`"
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")
    
    # Print to console
    print("=" * 60)
    print(f"✅ Bot received message from user!")
    print(f"   User ID: {user_id}")
    print(f"   Username: @{user.username or 'None'}")
    print(f"   Name: {user.first_name} {user.last_name or ''}")
    print("=" * 60)
    print(f"\nTo authorize this user, run in PowerShell:")
    print(f'$env:TELEGRAM_ADMIN_ID = "{user_id}"')
    print("\nThen restart the bot with: python telegram_bot.py --polling")
    print("=" * 60)

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message"""
    user = update.effective_user
    await start(update, context)

async def main():
    """Start the bot"""
    try:
        # Create application
        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
        
        # Test bot connection
        bot_info = await app.bot.get_me()
        print("=" * 60)
        print("✅ BOT CONNECTION SUCCESSFUL!")
        print(f"   Bot Name: {bot_info.first_name}")
        print(f"   Bot Username: @{bot_info.username}")
        print(f"   Bot ID: {bot_info.id}")
        print("=" * 60)
        print("\n📱 Now open Telegram and:")
        print(f"   1. Search for: @{bot_info.username}")
        print("   2. Send /start or any message")
        print("   3. You'll receive your User ID")
        print("\n⏳ Waiting for messages... (Press Ctrl+C to stop)")
        print("=" * 60)
        print()
        
        # Start polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible issues:")
        print("  - Invalid bot token")
        print("  - Network connection problem")
        print("  - Bot was deleted or disabled")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
