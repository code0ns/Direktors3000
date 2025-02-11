import logging
import asyncio
from quart import Quart, render_template
from bot import setup_bot
from storage import TaskStorage

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Quart(__name__)
app.secret_key = "your-secret-key-here"

# Initialize task storage
task_storage = TaskStorage()

@app.route('/')
async def index():
    """Render the main page with all tasks"""
    tasks = task_storage.get_all_tasks()
    return await render_template('index.html', tasks=tasks)

async def run_app():
    """Run both the Flask app and Telegram bot concurrently"""
    try:
        logger.info("Starting services...")
        bot_task = asyncio.create_task(setup_bot(task_storage))
        await asyncio.gather(
            app.run_task(host="0.0.0.0", port=5000),
            bot_task
        )
    except Exception as e:
        logger.error(f"Error running services: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_app())