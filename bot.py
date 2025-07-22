import logging
import os
import json
import asyncio
from models import db, Category, File, Subscriber, PendingFile
from app import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Check if telegram is available
TELEGRAM_AVAILABLE = False
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Telegram module not available: {e}")
    logger.warning("Bot will run in limited mode. Install python-telegram-bot to enable full functionality.")

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.admin_id = int(os.getenv("ADMIN_ID", "0"))
        self.storage_channel_id = os.getenv("STORAGE_CHANNEL_ID", "")
        
    async def start(self, update, context):
        """Handle /start command"""
        if not TELEGRAM_AVAILABLE:
            return
            
        user_id = update.effective_user.id
        
        # Add user to subscribers
        with app.app_context():
            existing_subscriber = Subscriber.query.filter_by(user_id=user_id).first()
            if not existing_subscriber:
                subscriber = Subscriber(
                    user_id=user_id,
                    first_name=update.effective_user.first_name,
                    username=update.effective_user.username
                )
                db.session.add(subscriber)
                db.session.commit()
        
        # Show main menu
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update, context):
        """Show main category menu"""
        if not TELEGRAM_AVAILABLE:
            return
            
        with app.app_context():
            categories = Category.query.filter_by(parent_id=None).all()
            keyboard = []
            
            # Create buttons for main categories (categories without parent)
            main_categories = categories
        
        for category in main_categories:
            keyboard.append([InlineKeyboardButton(
                category.name, 
                callback_data=f"category_{category.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = "🤖 Welcome to File Distribution Bot!\n\nSelect a category to browse files:"
        
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
    
    async def handle_callback(self, update, context):
        """Handle callback queries from inline keyboards"""
        if not TELEGRAM_AVAILABLE:
            return
            
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("category_"):
            category_id = data.replace("category_", "")
            await self.show_category(update, context, category_id)
        elif data.startswith("file_"):
            file_id = data.replace("file_", "")
            await self.show_file(update, context, file_id)
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
        if not TELEGRAM_AVAILABLE:
            return
            
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
        
        text = f"📂 {category.name}\n\nSelect an item:"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    
    async def show_file(self, update, context, file_id: str):
        """Show file details and download link"""
        if not TELEGRAM_AVAILABLE:
            return
            
        with app.app_context():
            file_item = File.query.get(file_id)
            if not file_item:
                await update.callback_query.edit_message_text("File not found.")
                return
            
            # Create download button and back button
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
                text += f"Size: {file_item.size}\n"
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    
    async def handle_file_request(self, update, context):
        """Handle file download requests"""
        if not TELEGRAM_AVAILABLE:
            return
            
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
                    except Exception as e:
                        logger.error(f"Error sending file: {e}")
                        await update.message.reply_text("Sorry, there was an error sending the file.")
                else:
                    await update.message.reply_text("File not found.")
        else:
            await self.start(update, context)
    
    async def handle_admin_upload(self, update, context):
        """Handle file uploads from admin"""
        if not TELEGRAM_AVAILABLE:
            return
            
        if update.effective_user.id != self.admin_id:
            return
        
        if update.message.document:
            file_info = await context.bot.get_file(update.message.document.file_id)
            
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

def start_bot():
    """Start the Telegram bot"""
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram bot functionality disabled - python-telegram-bot not available")
        logger.info("Web admin panel will still work for managing categories and files")
        return
        
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not provided!")
        return
    
    # Check admin ID
    admin_id = os.getenv("ADMIN_ID", "0")
    if admin_id == "0":
        logger.error("ADMIN_ID not provided!")
        return
    
    bot = TelegramBot()
    
    try:
        # Create new event loop for this thread
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.handle_file_request))
        application.add_handler(CallbackQueryHandler(bot.handle_callback))
        application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_admin_upload))
        
        # Start polling
        logger.info("Starting Telegram bot...")
        logger.info(f"Bot token configured: {bool(bot_token)}")
        logger.info(f"Admin ID configured: {admin_id}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    start_bot()