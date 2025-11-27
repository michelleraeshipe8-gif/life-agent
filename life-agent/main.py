"""
Life Agent - Main Entry Point
"""
import asyncio
import logging
import os
import signal
from dotenv import load_dotenv
from core.agent_core import AgentCore
from core.telegram_bot import TelegramBot

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global references for graceful shutdown
agent = None
bot = None


async def main():
    """Main application entry point"""
    global agent, bot
    
    logger.info("=" * 50)
    logger.info("Life Agent Starting...")
    logger.info("=" * 50)
    
    try:
        # Initialize agent core
        agent = AgentCore()
        await agent.initialize()
        
        # Initialize Telegram bot
        bot = TelegramBot(agent)
        await bot.run()
        
        logger.info("=" * 50)
        logger.info("[OK] Life Agent is running!")
        logger.info("=" * 50)
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await shutdown()


async def shutdown():
    """Graceful shutdown"""
    logger.info("Shutting down...")
    
    if bot:
        await bot.stop()
    
    if agent:
        await agent.shutdown()
    
    logger.info("[OK] Shutdown complete")


def handle_signal(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    raise KeyboardInterrupt


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/screenshots', exist_ok=True)
    
    # Run
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
