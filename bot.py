from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
import os
from storage import TaskStorage

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Initialize task storage
task_storage = TaskStorage()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("📝 New Task", callback_data="new_task"),
            InlineKeyboardButton("📋 List Tasks", callback_data="list_tasks")
        ],
        [
            InlineKeyboardButton("🏷️ Categories", callback_data="categories"),
            InlineKeyboardButton("✅ Mark Done", callback_data="mark_done")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Task Manager Bot! 🤖\n\n"
        "What would you like to do?",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot and show main menu\n"
        "/new <task> - Create a new task\n"
        "/category <task_id> <category> - Set task category\n"
        "/list - Show all tasks\n"
        "/list_category <category> - Show tasks in a category\n"
        "/categories - List all categories\n"
        "/done <task_id> - Mark task as complete\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks from inline keyboard."""
    query = update.callback_query
    await query.answer()

    if query.data == "new_task":
        await query.message.reply_text(
            "To create a new task, use the command:\n"
            "/new <your task description>"
        )
    elif query.data == "list_tasks":
        tasks = task_storage.get_all_tasks()
        if tasks:
            task_list = []
            for task_id, task in tasks.items():
                category_text = f" [{task['category']}]" if task['category'] else ""
                status = "✅" if task['completed'] else "📌"
                task_list.append(f"{status} {task_id}: {task['text']}{category_text}")
            await query.message.reply_text("Your tasks:\n\n" + "\n".join(task_list))
        else:
            await query.message.reply_text("You don't have any tasks yet!")
    elif query.data == "categories":
        categories = task_storage.get_categories()
        if categories:
            category_list = "\n".join([f"📁 {category}" for category in categories])
            await query.message.reply_text(
                f"Available categories:\n\n{category_list}\n\n"
                "To view tasks in a category, use:\n"
                "/list_category <category>"
            )
        else:
            await query.message.reply_text(
                "No categories created yet!\n"
                "Add a category to a task using:\n"
                "/category <task_id> <category>"
            )
    elif query.data == "mark_done":
        await query.message.reply_text(
            "To mark a task as done, use the command:\n"
            "/done <task_id>"
        )
    elif query.data == "help":
        await help_command(update, context)

    # Show the main menu again
    keyboard = [
        [
            InlineKeyboardButton("📝 New Task", callback_data="new_task"),
            InlineKeyboardButton("📋 List Tasks", callback_data="list_tasks")
        ],
        [
            InlineKeyboardButton("🏷️ Categories", callback_data="categories"),
            InlineKeyboardButton("✅ Mark Done", callback_data="mark_done")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new task."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a task description.\n"
            "Usage: /new <task description>"
        )
        return

    task_text = " ".join(context.args)
    task_id = task_storage.add_task(task_text)
    await update.message.reply_text(
        f"Task added (ID: {task_id}): {task_text}\n\n"
        "To add a category to this task, use:\n"
        f"/category {task_id} <category>"
    )

async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a category for a task."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Please provide both task ID and category.\n"
            "Usage: /category <task_id> <category>"
        )
        return

    try:
        task_id = int(context.args[0])
        category = context.args[1]
    except ValueError:
        await update.message.reply_text("Invalid task ID. Please provide a number.")
        return

    if task_storage.set_task_category(task_id, category):
        await update.message.reply_text(f"Task {task_id} added to category: {category}")
    else:
        await update.message.reply_text(f"Task {task_id} not found.")

async def list_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List tasks in a specific category."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a category name.\n"
            "Usage: /list_category <category>"
        )
        return

    category = context.args[0]
    tasks = task_storage.get_tasks_by_category(category)
    if tasks:
        task_list = []
        for task_id, task in tasks.items():
            status = "✅" if task['completed'] else "📌"
            task_list.append(f"{status} {task_id}: {task['text']}")
        await update.message.reply_text(f"Tasks in category '{category}':\n\n" + "\n".join(task_list))
    else:
        await update.message.reply_text(f"No tasks found in category '{category}'")

async def list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available categories."""
    categories = task_storage.get_categories()
    if categories:
        category_list = "\n".join([f"📁 {category}" for category in categories])
        await update.message.reply_text(
            f"Available categories:\n\n{category_list}\n\n"
            "To view tasks in a category, use:\n"
            "/list_category <category>"
        )
    else:
        await update.message.reply_text(
            "No categories created yet!\n"
            "Add a category to a task using:\n"
            "/category <task_id> <category>"
        )

def create_application():
    """Create and configure the bot application"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found in environment variables!")
        return None

    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_task))
    application.add_handler(CommandHandler("category", set_category))
    application.add_handler(CommandHandler("list_category", list_category))
    application.add_handler(CommandHandler("categories", list_categories))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    return application