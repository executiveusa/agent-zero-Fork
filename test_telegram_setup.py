#!/usr/bin/env python3
"""Quick test script to verify Telegram bot dependencies"""

import sys

print("Testing Telegram Bot Setup...")
print("-" * 50)

# Test imports
try:
    from telegram import Update
    from telegram.ext import Application
    print("✅ python-telegram-bot: OK")
except ImportError as e:
    print(f"❌ python-telegram-bot: FAILED - {e}")
    sys.exit(1)

try:
    import requests
    print("✅ requests: OK")
except ImportError as e:
    print(f"❌ requests: FAILED - {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv: OK")
except ImportError as e:
    print(f"❌ python-dotenv: FAILED - {e}")

print("-" * 50)

# Check environment variables
import os

token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_id = os.getenv("TELEGRAM_ADMIN_ID")

print("\nEnvironment Variables:")
print(f"  TELEGRAM_BOT_TOKEN: {'✅ Set' if token else '❌ Not Set (required)'}")
print(f"  TELEGRAM_ADMIN_ID: {'✅ Set' if admin_id else '❌ Not Set (required)'}")
print(f"  GITHUB_TOKEN: {'✅ Set' if os.getenv('GITHUB_TOKEN') else '⚠️ Not Set (optional)'}")

print("\n" + "-" * 50)

if not token or not admin_id:
    print("\n⚠️ MISSING REQUIRED ENVIRONMENT VARIABLES")
    print("\nTo set them (PowerShell):")
    print('  $env:TELEGRAM_BOT_TOKEN = "your_token_here"')
    print('  $env:TELEGRAM_ADMIN_ID = "your_user_id_here"')
    print("\nGet your token from @BotFather on Telegram")
    print("Get your user ID from @userinfobot on Telegram")
    sys.exit(1)
else:
    print("\n✅ All required environment variables are set!")
    print("\nYou can now run:")
    print("  python telegram_bot.py --polling")

print()
