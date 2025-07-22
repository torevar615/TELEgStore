#!/usr/bin/env python3
import asyncio
import threading
import logging
from app import app
from bot import start_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_flask():
    """Run Flask app"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    """Run Telegram bot"""
    try:
        start_bot()
    except Exception as e:
        logging.error(f"Bot error: {e}")

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    run_flask()