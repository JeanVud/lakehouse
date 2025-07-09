import logging
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def send_message(bot_token: str, chat_id: int, text: str, parse_mode: str = "HTML"):
    """Send message to Telegram chat"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload) 

def set_bot_webhook(bot_token: str, webhook_url: str):
    logger.info(f"Setting webhook to {webhook_url}")
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {
        "url": webhook_url
    }
    response = httpx.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"Failed to set webhook: {response.text}")
    else:
        logger.info(f"Webhook set successfully")
    return response.json()

def get_bot_info(bot_token: str):
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = httpx.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get bot info: {response.text}")
    return response.json()