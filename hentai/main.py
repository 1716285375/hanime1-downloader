"""
Main entry point for Hanime1 Downloader
"""
import asyncio
import uvicorn
from loguru import logger

from config import webui_config, LOG_DIR
from api.server import app


# Configure logging
logger.add(
    LOG_DIR / "app_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting Hanime1 Downloader v1.0")
    logger.info("=" * 60)
    
    # Display configuration
    logger.info(f"WebUI: http://{webui_config.host}:{webui_config.port}")
    logger.info(f"Log directory: {LOG_DIR}")
    
    try:
        # Run FastAPI server with uvicorn
        uvicorn.run(
            app,
            host=webui_config.host,
            port=webui_config.port,
            log_level=webui_config.log_level.lower(),
            reload=webui_config.reload
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        logger.info("Hanime1 Downloader stopped")


if __name__ == "__main__":
    main()
