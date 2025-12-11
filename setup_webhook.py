import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    if not webhook_url:
        # Use Render URL
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            webhook_url = f"{render_url}/webhook"
        else:
            print("❌ WEBHOOK_URL not found!")
            return
    
    bot = Bot(token=token)
    
    try:
        # Remove existing webhook
        await bot.delete_webhook()
        print("✅ Old webhook removed")
        
        # Set new webhook
        await bot.set_webhook(webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
        
        # Check webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"📋 Webhook info: {webhook_info.url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())