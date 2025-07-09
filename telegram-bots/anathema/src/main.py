from fastapi import FastAPI, Request
from app.services.telegram_service import send_message, set_bot_commands, set_bot_webhook
from core.utils import logger
from core.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from app.commands.base_commands import handler
from core.database import setup_database

# Import reminder commands to register them
import app.commands.reminder_commands

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Anathema Bot"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not text or not chat_id:
        return {"ok": True}

    try:
        # Try to execute as command first
        command_executed = handler.execute(chat_id, text)
        
        # If not a command, handle as regular message
        if not command_executed:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, f"You said: {text}")
            
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")
        # Send error message to user
        try:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, "Sorry, something went wrong. Please try again.")
        except:
            pass

    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Anathema Bot started")
    
    # Setup database and run schema
    try:
        await setup_database()
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
    
    # Set webhook
    set_bot_webhook(TELEGRAM_BOT_TOKEN, WEBHOOK_URL)
    
    # Register commands with Telegram
    commands = handler.get_telegram_commands()
    success = set_bot_commands(TELEGRAM_BOT_TOKEN, commands)
    
    if success:
        logger.info(f"✅ Bot commands registered successfully: {len(commands)} commands")
        for cmd in commands:
            logger.info(f"  • /{cmd['command']} - {cmd['description']}")
    else:
        logger.error("❌ Failed to register bot commands")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Anathema Bot stopped")