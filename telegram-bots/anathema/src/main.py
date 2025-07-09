from fastapi import FastAPI, Request
from utils import send_message, logger, set_bot_commands
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from utils import set_bot_webhook
from commands import handler
import json

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
        command_executed = await handler.execute(chat_id, text)
        
        # If not a command, handle as regular message
        if not command_executed:
            await send_message(TELEGRAM_BOT_TOKEN, chat_id, f"You said: {text}")
            
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")
        # Send error message to user
        try:
            await send_message(TELEGRAM_BOT_TOKEN, chat_id, "Sorry, something went wrong. Please try again.")
        except:
            pass

    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Anathema Bot started")
    
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