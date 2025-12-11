import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot_handlers import start, handle_voice, handle_text
from flask import Flask, request

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Create Telegram application
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

# Routes
@app.route('/')
def home():
    return "🤖 Telegram Quote Bot is running!<br>Send /start to @YourBotName"

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle Telegram updates"""
    try:
        # Get update from Telegram
        json_str = request.get_data().decode('UTF-8')
        update = Update.de_json(json_str, telegram_app.bot)
        
        # Process update
        await telegram_app.process_update(update)
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Manual webhook setup page"""
    render_url = os.getenv("RENDER_EXTERNAL_URL", request.host_url.rstrip('/'))
    webhook_url = f"{render_url}/webhook"
    
    return f"""
    <h1>Setup Webhook</h1>
    <p>Webhook URL: <code>{webhook_url}</code></p>
    <p>Token: <code>{TELEGRAM_TOKEN[:10]}...{TELEGRAM_TOKEN[-5:]}</code></p>
    <p>Steps:</p>
    <ol>
        <li>Click: <a href="https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}" target="_blank">
            Set Webhook Now
        </a></li>
        <li>Check: <a href="https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo" target="_blank">
            Verify Webhook
        </a></li>
        <li>Test your bot on Telegram!</li>
    </ol>
    """

@app.route('/health')
def health():
    return 'OK', 200

def main():
    """Run the app"""
    # Ensure temp directory exists
    if not os.path.exists("temp"):
        os.makedirs("temp", exist_ok=True)
    
    # Initialize Telegram app (but don't start polling)
    telegram_app.initialize()
    
    # Get port from environment
    port = int(os.getenv("PORT", 10000))
    
    logger.info(f"🚀 Starting Flask app on port {port}")
    logger.info(f"🤖 Bot token: {TELEGRAM_TOKEN[:10]}...")
    
    # Run Flask
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()