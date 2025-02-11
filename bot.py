import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext

# Configure logging for the bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to TaskManager Bot!\n\n"
        "Available commands:\n"
        "/new <task> - Create a new task\n"
        "/list - Show all tasks\n"
        "/done <task_id> - Mark task as complete\n"
        "/help - Show this help message"
    )

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a task description!")
        return

    task_text = ' '.join(context.args)
    task_id = context.bot_data['storage'].add_task(task_text)
    await update.message.reply_text(f"Task created with ID: {task_id}")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = context.bot_data['storage'].get_all_tasks()
    if not tasks:
        await update.message.reply_text("No tasks found!")
        return

    task_list = "\n".join([
        f"{task_id}: {task['text']} ({'✓' if task['completed'] else '○'})"
        for task_id, task in tasks.items()
    ])
    await update.message.reply_text(f"Tasks:\n{task_list}")

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a task ID!")
        return

    try:
        task_id = int(context.args[0])
        if context.bot_data['storage'].mark_task_complete(task_id):
            await update.message.reply_text(f"Task {task_id} marked as complete!")
        else:
            await update.message.reply_text(f"Task {task_id} not found!")
    except ValueError:
        await update.message.reply_text("Invalid task ID!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Available commands:\n"
        "/new <task> - Create a new task\n"
        "/list - Show all tasks\n"
        "/done <task_id> - Mark task as complete\n"
        "/help - Show this help message"
    )

async def setup_bot(storage):
    """Setup and run the Telegram bot"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not found in environment variables!")
            return

        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Store the storage instance in bot_data
        application.bot_data['storage'] = storage

        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("new", new_task))
        application.add_handler(CommandHandler("list", list_tasks))
        application.add_handler(CommandHandler("done", mark_done))

        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.run_polling()

    except Exception as e:
        logger.error(f"Error running bot: {str(e)}", exc_info=True)
        raise