#!/usr/bin/env python3
"""
Standalone Telegram Bot Service
This runs the bot as a separate process to avoid threading/asyncio conflicts
"""
import os
import sys
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue with system environment variables
    pass

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Category, File, Subscriber, PendingFile
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_file_size(size_bytes):
    """Convert bytes to human-readable file size"""
    if size_bytes is None or size_bytes == 0:
        return "Unknown size"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

class TelegramBotService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.admin_id = int(os.getenv("ADMIN_ID", "0"))
        
        # Validate required environment variables
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
            logger.error("Please set your bot token in Railway environment variables")
            sys.exit(1)
            
        if not self.admin_id:
            logger.error("ADMIN_ID environment variable is not set!")
            logger.error("Please set your admin ID in Railway environment variables")
            sys.exit(1)
            
        logger.info(f"Bot token loaded: {self.bot_token[:10]}...")
        logger.info(f"Admin ID: {self.admin_id}")

    async def start_command(self, update: Update, context):
        """Handle /start command and file requests"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "No username"
        first_name = update.effective_user.first_name or "No name"
        
        logger.info(f"User {user_id} ({username}, {first_name}) started the bot")
        
        # Add user to subscribers
        with app.app_context():
            try:
                existing_subscriber = Subscriber.query.filter_by(user_id=user_id).first()
                if not existing_subscriber:
                    subscriber = Subscriber(
                        user_id=user_id,
                        first_name=update.effective_user.first_name or "",
                        username=update.effective_user.username or ""
                    )
                    db.session.add(subscriber)
                    db.session.commit()
                    logger.info(f"Added new subscriber: {user_id}")
            except Exception as e:
                logger.error(f"Error adding subscriber {user_id}: {e}")
                db.session.rollback()

        # Handle file download requests
        if context.args and context.args[0].startswith("file_"):
            file_id = context.args[0].replace("file_", "")
            with app.app_context():
                file_item = File.query.get(file_id)
                
                if file_item and file_item.telegram_file_id:
                    try:
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=file_item.telegram_file_id,
                            caption=f"📄 {file_item.name}"
                        )
                        return
                    except Exception as e:
                        logger.error(f"Error sending file: {e}")
                        await update.message.reply_text("Sorry, there was an error sending the file.")
                        return
                else:
                    await update.message.reply_text("File not found.")
                    return
        
        # Show main menu
        await self.show_main_menu(update, context)

    async def show_main_menu(self, update, context):
        """Show main category menu"""
        user_id = update.effective_user.id
        logger.info(f"Showing main menu for user {user_id}")
        
        with app.app_context():
            categories = Category.query.filter_by(parent_id=None).all()
            logger.info(f"Found {len(categories)} categories for user {user_id}")
            keyboard = []
            
            for category in categories:
                keyboard.append([InlineKeyboardButton(
                    category.name, 
                    callback_data=f"category_{category.id}"
                )])
        
        # Add search button
        if len(categories) > 0:
            keyboard.append([InlineKeyboardButton("🔍 Search Files", callback_data="search_files")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_text = "🤖 اهلا بكم في بوت المتجر ميتا للتطبيقات!\n\nاختر قسم لعرض الملفات او ابحث"
        
        if len(categories) == 0:
            welcome_text = "🤖اهلاً بكم في بوت المتجر ميتا للتطبيقات!\n\nNo categories available yet. Please contact the admin to add categories."
        
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=welcome_text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    text=welcome_text,
                    reply_markup=reply_markup
                )
            logger.info(f"Successfully sent main menu to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending main menu to user {user_id}: {e}")
            if not update.callback_query:
                await update.message.reply_text("Bot is starting up, please try again in a moment.")

    async def handle_callback(self, update, context):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("category_"):
            category_id = data.replace("category_", "")
            await self.show_category(update, context, category_id)
        elif data.startswith("file_"):
            file_id = data.replace("file_", "")
            await self.show_file(update, context, file_id)
        elif data == "search_files":
            await self.show_search_prompt(update, context)
        elif data == "back_main":
            await self.show_main_menu(update, context)
        elif data.startswith("back_category_"):
            parent_id = data.replace("back_category_", "")
            if parent_id == "None":
                await self.show_main_menu(update, context)
            else:
                await self.show_category(update, context, parent_id)

    async def show_category(self, update, context, category_id: str):
        """Show files and subcategories in a category"""
        with app.app_context():
            category = Category.query.get(category_id)
            if not category:
                await update.callback_query.edit_message_text("Category not found.")
                return
            
            keyboard = []
            
            # Get subcategories
            subcategories = Category.query.filter_by(parent_id=category_id).all()
            for subcat in subcategories:
                keyboard.append([InlineKeyboardButton(
                    f"📁 {subcat.name}", 
                    callback_data=f"category_{subcat.id}"
                )])
            
            # Get files in this category
            files = File.query.filter_by(category_id=category_id).all()
            for file_item in files:
                keyboard.append([InlineKeyboardButton(
                    f"📄 {file_item.name}", 
                    callback_data=f"file_{file_item.id}"
                )])
            
            # Add back button
            back_data = f"back_category_{category.parent_id or 'None'}"
            if category.parent_id is None:
                back_data = "back_main"
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_data)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=f"📁 {category.name}\n\nSelect a file or subcategory:",
            reply_markup=reply_markup
        )

    async def show_file(self, update, context, file_id: str):
        """Show file details and download link"""
        with app.app_context():
            file_item = File.query.get(file_id)
            if not file_item:
                await update.callback_query.edit_message_text("File not found.")
                return
            
            keyboard = []
            
            if file_item.telegram_file_id:
                keyboard.append([InlineKeyboardButton(
                    "📥 Download", 
                    url=f"https://t.me/{context.bot.username}?start=file_{file_id}"
                )])
            
            # Back to category
            category_id = file_item.category_id
            keyboard.append([InlineKeyboardButton(
                "⬅️ Back", 
                callback_data=f"category_{category_id}"
            )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"📄 {file_item.name}\n\n"
            if file_item.description:
                text += f"Description: {file_item.description}\n\n"
            if file_item.size:
                text += f"Size: {format_file_size(file_item.size)}\n"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_search_prompt(self, update, context):
        """Show search prompt to user"""
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        search_text = (
            "🔍 Search Files\n\n"
            "Type the name of the file you're looking for.\n"
            "I'll search through all available files."
        )
        
        await update.callback_query.edit_message_text(
            text=search_text,
            reply_markup=reply_markup
        )
        
        # Set user state to expect search query
        context.user_data['waiting_for_search'] = True

    async def handle_search_query(self, update, context):
        """Handle search query from user"""
        query = update.message.text.strip()
        user_id = update.effective_user.id
        
        logger.info(f"User {user_id} searching for: {query}")
        
        with app.app_context():
            # Search files by name (case-insensitive)
            files = File.query.filter(
                File.name.ilike(f'%{query}%')
            ).limit(20).all()
            
            if not files:
                keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_main")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🔍 No files found for '{query}'\n\nTry different keywords or browse categories.",
                    reply_markup=reply_markup
                )
                return
            
            # Show search results
            keyboard = []
            result_text = f"🔍 Search Results for '{query}'\n\nFound {len(files)} file(s):\n\n"
            
            for file_item in files:
                # Add file button
                keyboard.append([InlineKeyboardButton(
                    f"📄 {file_item.name}", 
                    callback_data=f"file_{file_item.id}"
                )])
                
                # Add to text description
                category_name = file_item.category.name if file_item.category else "Unknown"
                size_text = f" ({format_file_size(file_item.size)})" if file_item.size else ""
                result_text += f"📄 {file_item.name}{size_text}\n📂 Category: {category_name}\n\n"
            
            # Add back button
            keyboard.append([InlineKeyboardButton("🔍 New Search", callback_data="search_files")])
            keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text=result_text,
                reply_markup=reply_markup
            )
        
        # Clear search state
        context.user_data['waiting_for_search'] = False

    async def handle_text_message(self, update, context):
        """Handle text messages from users"""
        # Check if user is in search mode
        if context.user_data.get('waiting_for_search', False):
            await self.handle_search_query(update, context)
        else:
            # Regular text message - show help
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Use the buttons below to navigate, or send /start to see the main menu.",
                reply_markup=reply_markup
            )

    async def handle_admin_upload(self, update, context):
        """Handle file uploads from admin"""
        if update.effective_user.id != self.admin_id:
            return
        
        if update.message.document:
            # Store file info for admin panel to process
            with app.app_context():
                pending_file = PendingFile(
                    telegram_file_id=update.message.document.file_id,
                    name=update.message.document.file_name,
                    size=update.message.document.file_size,
                    mime_type=update.message.document.mime_type
                )
                db.session.add(pending_file)
                db.session.commit()
            
            await update.message.reply_text(
                f"✅ File '{update.message.document.file_name}' received!\n"
                "Use the admin panel to assign it to a category."
            )

    def run(self):
        """Start the bot"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not provided!")
            return
        
        if self.admin_id == 0:
            logger.error("ADMIN_ID not provided!")
            return
        
        logger.info(f"Starting bot with admin ID: {self.admin_id}")
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_admin_upload))
        
        # Start polling with proper configuration
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    bot = TelegramBotService()
    bot.run()

if __name__ == "__main__":
    main()