import logging
import asyncio
from quart import Quart, render_template
from bot import create_application
from storage import TaskStorage
import socket

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Initialize task storage
task_storage = TaskStorage()

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def create_app():
    """Create and configure the Quart app"""
    app = Quart(__name__)
    app.secret_key = "your-secret-key-here"  # In production, use a secure secret key

    @app.route('/')
    async def index():
        """Render the main page with all tasks"""
        tasks = task_storage.get_all_tasks()
        return await render_template('index.html', tasks=tasks)

    return app

async def run_bot():
    """Initialize and run the Telegram bot"""
    try:
        bot_app = create_application()
        if not bot_app:
            logger.error("Failed to create bot application")
            return None

        await bot_app.initialize()
        await bot_app.start()

        # Start polling in the background
        return bot_app
    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        return None

async def main():
    """Initialize and run both the web app and Telegram bot"""
    try:
        # Check if port is already in use
        if is_port_in_use(5000):
            logger.error("Port 5000 is already in use")
            return

        # Create the Quart app
        app = create_app()

        # Initialize bot
        bot_app = await run_bot()
        if not bot_app:
            return

        # Start both services
        bot_task = asyncio.create_task(bot_app.updater.start_polling())
        web_task = asyncio.create_task(app.run_task(host="0.0.0.0", port=5000))

        # Wait for both tasks to complete
        await asyncio.gather(web_task, bot_task)

    except Exception as e:
        logger.error(f"Error running services: {str(e)}", exc_info=True)
    finally:
        if 'bot_app' in locals():
            try:
                await bot_app.updater.stop()
                await bot_app.stop()
                await bot_app.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {str(shutdown_error)}")

if __name__ == "__main__":
    asyncio.run(main())