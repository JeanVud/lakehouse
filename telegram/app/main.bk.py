import os
import openai
from openai import AsyncOpenAI
import httpx
from fastapi import FastAPI, Request
import json

# Set up API keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", '')
BOT_USERNAME = os.getenv("BOT_USERNAME", '')  # e.g. 'my_gpt_bot' (without @)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", '')
openai.api_key = OPENAI_API_KEY

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


app = FastAPI()



@app.get("/")
async def root():
    return {"message": "Hello, World!"}
@app.get("/health")
async def health():
    return {"status": "ok"}



@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    text = message.get("text", "")

    if not text:
        return {"ok": True}

    should_respond = False

    # Case 1: Direct message
    if chat_type == "private":
        should_respond = True

    # Case 2: Group chat and bot is mentioned
    elif chat_type in ["group", "supergroup"]:
        entities = message.get("entities", [])
        for entity in entities:
            if entity.get("type") == "mention":
                offset = entity.get("offset", 0)
                length = entity.get("length", 0)
                mention_text = text[offset:offset+length]
                if mention_text.lower() in [f"@{BOT_USERNAME}".lower()]:
                    should_respond = True
                    break

    if not should_respond:
        print(f"🔇 Ignored message in chat {chat_id}")
        return {"ok": True}

    print(f"📨 From {chat_type} chat {chat_id}: {text}")

    try:
        response = await ask_chatgpt(text)
        print(f"🤖 ChatGPT: {response}")
    except Exception as e:
        response = "⚠️ Sorry, I had trouble thinking right now."
        print(f"❌ OpenAI error: {e}")

    await send_message(chat_id, response)
    return {"ok": True}


async def ask_chatgpt(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


async def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)