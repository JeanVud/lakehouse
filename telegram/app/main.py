import asyncio
from datetime import datetime, timedelta
from typing import Dict
from fastapi import FastAPI, Request
from utils import send_message, logger
from session_manager import SessionManager
from command_registry import command_registry

app = FastAPI()

# Initialize session manager with command registry
session_manager = SessionManager(command_registry)

@app.get("/")
async def root():
    return {"message": "Telegram Finance Bot"}

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

    if chat_type != "private":
        logger.info(f"🔇 Ignored message in {chat_type} chat {chat_id}")
        return {"ok": True}

    logger.info(f"📨 From chat {chat_id}: {text}")

    try:
        await handle_message(chat_id, text)
    except Exception as e:
        error_msg = "⚠️ Sorry, I encountered an error. Please try again."
        await send_message(chat_id, error_msg)
        logger.error(f"❌ Error handling message: {e}")

    return {"ok": True}

async def handle_message(chat_id: int, text: str):
    # Check for active session
    session = session_manager.get_session(chat_id)
    if session:
        if session_manager.is_session_expired(session):
            logger.info(f"⏰ Session expired for user {chat_id}")
            session_manager.remove_session(chat_id)
            await send_message(chat_id, "Session expired. Start a new session with /log-finance")
            return
        
        # Handle session continuation
        handler = command_registry.get_handler(session.command)
        if handler:
            result = await handler.handle_session_continuation(chat_id, text, session.data)
            if result.get("session_ended", False):
                session_manager.remove_session(chat_id)
            return
    
    # Handle slash commands
    if text.startswith('/'):
        await handle_slash_command(chat_id, text)
    else:
        await send_message(chat_id, "Use /log-finance to start logging your purchases! Type /help for more information.")

async def handle_slash_command(chat_id: int, text: str):
    parts = text.split()
    command_name = parts[0][1:]  # Remove the slash
    
    # Get command key from command registry
    command_key = command_registry.get_command_by_name(command_name)
    
    if command_key:
        handler = command_registry.get_handler(command_key)
        if handler:
            session_data = await handler.parse_command_args(parts[1:])
            if command_registry.needs_session(command_key):
                session_manager.create_session(chat_id, command_key, session_data)
            await handler.handle_command(chat_id, session_data)
        else:
            logger.error(f"No handler found for command: {command_key}")
            await send_message(chat_id, "Command not implemented yet.")
    else:
        await send_message(chat_id, "Unknown command. Use /log-finance to start logging purchases or /help for assistance.")

@app.on_event("startup")
async def startup_event():
    # Validate that all configured commands have handlers
    try:
        command_registry.validate_commands()
        logger.info("✅ All commands validated successfully")
    except ValueError as e:
        logger.error(f"❌ Command validation failed: {e}")
    
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    while True:
        await asyncio.sleep(60)
        session_manager.cleanup_expired_sessions() 