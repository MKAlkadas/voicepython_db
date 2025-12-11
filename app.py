import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot_handlers import start, handle_voice, handle_text

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return
    
    # Create temp directory
    if not os.path.exists("temp"):
        os.makedirs("temp", exist_ok=True)
    
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("✅ Bot is running with polling...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )

if __name__ == '__main__':
    main()