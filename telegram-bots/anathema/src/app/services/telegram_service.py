"""
Telegram Bot API utility functions
"""
import json
import requests
import logging

logger = logging.getLogger(__name__)

def send_message(bot_token: str, chat_id: int, text: str, parse_mode: str = "Markdown"):
    """Send message to Telegram chat"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message: {e}")
        return None

def set_bot_webhook(bot_token: str, webhook_url: str):
    """Set webhook URL for Telegram bot"""
    logger.info(f"Setting webhook to {webhook_url}")
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {
        "url": webhook_url
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Webhook set successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to set webhook: {e}")
        return None

def set_bot_commands(bot_token: str, commands: list):
    """Set bot commands using Telegram Bot API setMyCommands"""
    url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
    payload = {
        "commands": commands
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Bot commands set successfully: {len(commands)} commands")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to set bot commands: {e}")
        return False

def get_bot_info(bot_token: str):
    """Get bot information from Telegram API"""
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get bot info: {e}") 