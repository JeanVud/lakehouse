from fastapi import FastAPI, Request
from utils import send_message, logger
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from utils import set_bot_webhook

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
    chat_type = message.get("type")
    text = message.get("text", "")

    if not text:
        return {"ok": True}

    # if chat_type != "private":
    #     logger.info(f"🔇 Ignored message in {chat_type} chat {chat_id}")
    #     return {"ok": True}

    logger.info(f"📨 From chat {chat_id}: {text}")

    try:
        await send_message(TELEGRAM_BOT_TOKEN, chat_id, f"You texted: {text}")
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")

    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Anathema Bot started")
    set_bot_webhook(TELEGRAM_BOT_TOKEN, WEBHOOK_URL)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Anathema Bot stopped")