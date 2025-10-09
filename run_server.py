#!/usr/bin/env python3
"""
Standalone script to run the Advanced Odoo MCP server with enhanced logging
Compatible with FastMCP 2.12+
"""

import sys
import os
import logging
import datetime

from odoo_mcp.server import mcp  # FastMCP instance from our code


def setup_logging():
    """Set up logging to both console and file"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"mcp_server_{timestamp}.log")

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Format for both handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def main() -> int:
    """
    Run the MCP server with FastMCP 2.12+
    """
    logger = setup_logging()

    try:
        logger.info("=== ODOO ADVANCED MCP SERVER STARTING ===")
        logger.info(f"Python version: {sys.version}")
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if key.startswith("ODOO_"):
                if key == "ODOO_PASSWORD":
                    logger.info(f"  {key}: ***hidden***")
                else:
                    logger.info(f"  {key}: {value}")

        logger.info(f"MCP object type: {type(mcp)}")
        logger.info("Starting Advanced Odoo MCP server with FastMCP run() method...")
        sys.stderr.flush()

        # Use FastMCP's run() method - same as __main__.py
        mcp.run()

        logger.info("MCP server stopped normally")
        return 0

    except KeyboardInterrupt:
        logger.info("Advanced Odoo MCP server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
