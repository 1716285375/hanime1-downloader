"""
Main entry point for Hanime1 Downloader
"""
import asyncio
import logging
import sys
import uvicorn
import uvicorn.config
from loguru import logger

from config import webui_config, LOG_DIR


# Logging configuration will be set up in main()

from api.server import app


import argparse
import os

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Hanime1 Downloader")
    parser.add_argument("--mode", choices=["dev", "prod"], default="prod", help="Application mode (dev/prod)")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variables based on arguments
    # These will be picked up by config.py when imported by uvicorn workers
    if args.mode:
        os.environ["HANIME_MODE"] = args.mode
    if args.host:
        os.environ["HANIME_HOST"] = args.host
    if args.port:
        os.environ["HANIME_PORT"] = str(args.port)
    if args.reload:
        os.environ["HANIME_RELOAD"] = "true"
        
    # Re-import config to pick up env vars for the main process logging
    # Note: uvicorn workers will import config freshly in their own processes
    import importlib
    import config
    importlib.reload(config)
    from config import webui_config

    # Configure logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logger.remove()  # Remove default handlers
    
    # File handler
    logger.add(
        LOG_DIR / "app_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG" if args.mode == "dev" else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    # Console handler (added back)
    logger.add(
        sys.stderr,
        level="DEBUG" if args.mode == "dev" else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Intercept standard logging (Uvicorn)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False
    
    logger.info("=" * 60)
    logger.info(f"Starting Hanime1 Downloader v1.0 ({args.mode} mode)")
    logger.info("=" * 60)
    
    # Display configuration
    logger.info(f"WebUI: http://{webui_config.host}:{webui_config.port}")
    logger.info(f"Log directory: {LOG_DIR}")
    
    try:
        # Run FastAPI server with uvicorn
        # log_config=None ensures uvicorn doesn't overwrite our logging config
        use_reload = webui_config.reload or args.mode == "dev"
        
        uvicorn.run(
            "main:app",
            host=webui_config.host,
            port=webui_config.port,
            log_level=webui_config.log_level.lower(),
            reload=use_reload,
            log_config=uvicorn.config.LOGGING_CONFIG
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
