import logging
import threading
import time
import os
from app import app
from bot import start_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_bot():
    """Run Telegram bot"""
    while True:
        try:
            logger.info("Starting Telegram bot service...")
            start_bot()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)

# Note: Bot service is started separately to avoid event loop conflicts
