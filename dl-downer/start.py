# Debug: Check if an asyncio event loop is already running before we do anything
import asyncio
from loguru import logger

try:
    loop = asyncio.get_running_loop()
    logger.debug(f"Event loop already running before nest_asyncio: {loop}")
except RuntimeError:
    logger.debug("No event loop running before nest_asyncio")

# Apply nest_asyncio to allow Playwright sync API to work even if an asyncio loop exists
# This is needed in some environments (e.g., Docker with certain base images)
import nest_asyncio
nest_asyncio.apply()

from src.server import start_server
start_server()
