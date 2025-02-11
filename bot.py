from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
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

# Define conversation states
(EXPECTING_TASK, EXPECTING_CATEGORY, SELECTING_CATEGORY) = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Pievienot uzdevumu", callback_data="add_task"),
            InlineKeyboardButton("📋 Uzdevumu saraksts", callback_data="list_tasks")
        ],
        [
            InlineKeyboardButton("🏷️ Skatīt kategorijas", callback_data="view_categories"),
            InlineKeyboardButton("❓ Palīdzība", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Laipni lūdzam Uzdevumu pārvaldības botā! 🤖\n\n"
        "Ko vēlaties darīt?",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "Šeit ir tas, ko varat darīt:\n\n"
        "• Nospiediet '📝 Pievienot uzdevumu', lai izveidotu jaunu uzdevumu\n"
        "• Nospiediet '📋 Uzdevumu saraksts', lai redzētu visus uzdevumus\n"
        "• Nospiediet '🏷️ Skatīt kategorijas', lai pārvaldītu uzdevumu kategorijas\n"
        "• Nospiediet '❓ Palīdzība', lai redzētu šo ziņojumu vēlreiz"
    )
    await update.message.reply_text(help_text)
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks from inline keyboard."""
    query = update.callback_query
    await query.answer()

    if query.data == "add_task":
        await query.message.reply_text(
            "Lūdzu, ievadiet uzdevuma aprakstu:\n"
            "(vai nospiediet /cancel, lai atceltu)",
            reply_markup=ReplyKeyboardRemove()
        )
        return EXPECTING_TASK

    elif query.data == "list_tasks":
        tasks = task_storage.get_all_tasks()
        if tasks:
            task_list = []
            for task_id, task in tasks.items():
                category_text = f" [{task['category']}]" if task['category'] else ""
                status = "✅" if task['completed'] else "📌"
                task_list.append(f"{status} {task_id}: {task['text']}{category_text}")
            await query.message.reply_text("Jūsu uzdevumi:\n\n" + "\n".join(task_list))
        else:
            await query.message.reply_text("Jums vēl nav uzdevumu!")

    elif query.data == "view_categories":
        categories = task_storage.get_categories()
        if categories:
            keyboard = [[InlineKeyboardButton(f"📁 {category}", callback_data=f"cat_{category}")]
                       for category in categories]
            keyboard.append([InlineKeyboardButton("🔙 Atpakaļ", callback_data="back_to_main")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Izvēlieties kategoriju, lai skatītu tās uzdevumus:",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(
                "Vēl nav izveidotu kategoriju!\n"
                "Kategorijas tiks izveidotas automātiski, kad pievienosiet tās uzdevumiem."
            )

    elif query.data.startswith("cat_"):
        category = query.data[4:]  # Remove 'cat_' prefix
        tasks = task_storage.get_tasks_by_category(category)
        if tasks:
            task_list = []
            for task_id, task in tasks.items():
                status = "✅" if task['completed'] else "📌"
                task_list.append(f"{status} {task_id}: {task['text']}")
            await query.message.reply_text(
                f"Uzdevumi kategorijā '{category}':\n\n" + "\n".join(task_list)
            )
        else:
            await query.message.reply_text(f"Kategorijā '{category}' nav atrasts neviens uzdevums")

    elif query.data == "back_to_main":
        await start(update, context)

    elif query.data == "help":
        await help_command(update, context)

    return ConversationHandler.END

async def handle_new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new task text input."""
    task_text = update.message.text
    task_id = task_storage.add_task(task_text)

    keyboard = [
        [InlineKeyboardButton("➕ Pievienot kategoriju", callback_data=f"add_cat_{task_id}"),
         InlineKeyboardButton("Izlaist", callback_data="skip_category")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Uzdevums pievienots (ID: {task_id}): {task_text}\n\n"
        "Vai vēlaties pievienot šim uzdevumam kategoriju?",
        reply_markup=reply_markup
    )
    return SELECTING_CATEGORY

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection for a task."""
    query = update.callback_query
    await query.answer()

    if query.data == "skip_category":
        await query.message.reply_text("Uzdevums saglabāts bez kategorijas!")
        await start(update, context)
        return ConversationHandler.END

    task_id = int(query.data.split('_')[2])  # Extract task_id from 'add_cat_X'
    await query.message.reply_text(
        "Lūdzu, ievadiet kategorijas nosaukumu šim uzdevumam:\n"
        "(vai nospiediet /cancel, lai izlaistu)",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['task_id'] = task_id
    return EXPECTING_CATEGORY

async def handle_new_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new category text input."""
    category = update.message.text
    task_id = context.user_data.get('task_id')

    if task_storage.set_task_category(task_id, category):
        await update.message.reply_text(f"Uzdevums {task_id} pievienots kategorijai: {category}")
    else:
        await update.message.reply_text("Kaut kas nogāja greizi. Lūdzu, mēģiniet vēlreiz.")

    # Clear user data and return to main menu
    context.user_data.clear()
    await start(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Darbība atcelta.",
        reply_markup=ReplyKeyboardRemove()
    )
    await start(update, context)
    return ConversationHandler.END

def create_application():
    """Create and configure the bot application"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not found in environment variables!")
        return None

    application = Application.builder().token(bot_token).build()

    # Create conversation handler for task management
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_click),
            CommandHandler("start", start)
        ],
        states={
            EXPECTING_TASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_task)
            ],
            SELECTING_CATEGORY: [
                CallbackQueryHandler(handle_category_selection)
            ],
            EXPECTING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_category)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start)
        ],
    )

    # Register handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    return application