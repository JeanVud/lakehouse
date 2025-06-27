#!/usr/bin/env python3
"""
Startup script for the Telegram Finance Bot
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file if it exists
load_dotenv()

def main():
    """Start the bot server"""
    # Check required environment variables
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables or create a .env file")
        return
    
    print("🚀 Starting Telegram Finance Bot...")
    print(f"📱 Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN', '')[:10]}...")
    print(f"👤 Bot Username: {os.getenv('BOT_USERNAME', 'Not set')}")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 