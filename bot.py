from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Store tasks per user
user_tasks = {}

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Check Tasks", callback_data="check_tasks")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Click the button below to check your tasks:", reply_markup=reply_markup)

# Handle Button Clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "check_tasks":
        tasks = user_tasks.get(user_id, [])
        if tasks:
            task_list = "\n".join([f"📌 {i+1}. {task}" for i, task in enumerate(tasks)])
            await query.message.reply_text(f"Here are your tasks:\n\n{task_list}")
        else:
            await query.message.reply_text("You don't have any tasks yet!")

        # Show the button again
        keyboard = [[InlineKeyboardButton("📋 Check Tasks", callback_data="check_tasks")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Click to check tasks again:", reply_markup=reply_markup)

# Handle Text Messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📋 Check Tasks", callback_data="check_tasks")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please use the button below to check tasks:", reply_markup=reply_markup)

def create_application():
    """Create and configure the bot application"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found in environment variables!")
        return None

    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application