import asyncio
from telegram import Bot

async def test():
    token = "8334090984:AAELS-YOMeZ72SaIPp79zl_YcVCjJxDqGhY"
    print(f"Testing token: {token[:15]}...")
    try:
        bot = Bot(token)
        me = await bot.get_me()
        print("\n" + "="*60)
        print("✅ TOKEN IS VALID!")
        print("="*60)
        print(f"Bot Name: {me.first_name}")
        print(f"Bot Username: @{me.username}")
        print(f"Bot ID: {me.id}")
        print("="*60)
        print(f"\n📱 Go to Telegram and search for: @{me.username}")
        print("   Send /start to get your User ID")
        return True
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TOKEN IS INVALID OR ERROR")
        print("="*60)
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
