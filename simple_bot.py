#!/usr/bin/env python3
"""
Simple Telegram Bot for file distribution
Self-contained version for Docker deployment
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Load environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTelegramBot:

    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.admin_id = ADMIN_ID

    async def start_command(self, update: Update, context):
        """Handle /start command"""
        user_id = update.effective_user.id

        # Simple welcome message with basic menu
        keyboard = [[
            InlineKeyboardButton("📁 Browse Files",
                                 callback_data="browse_files")
        ], [InlineKeyboardButton("ℹ️ About", callback_data="about")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🤖 Welcome to File Distribution Bot!\n\n"
            "This bot helps you access and download files.\n"
            "Select an option below:",
            reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()

        if query.data == "browse_files":
            await query.edit_message_text(
                "📁 File Browser\n\n"
                "Connect this bot to a database to browse files.\n"
                "For now, this is a basic setup.")
        elif query.data == "about":
            await query.edit_message_text(
                "ℹ️ About File Distribution Bot\n\n"
                "This bot distributes files organized in categories.\n"
                "Admin ID: {}\n"
                "Bot is running successfully!".format(self.admin_id))

    def run(self):
        """Start the bot"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not provided!")
            return

        logger.info(f"Starting simple bot with admin ID: {self.admin_id}")

        application = Application.builder().token(self.bot_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback))

        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = SimpleTelegramBot()
    bot.run()
