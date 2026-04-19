"""Command-line entry point for the Odoo MCP Server (STDIO transport)."""
from __future__ import annotations

import os
import sys
import traceback

from .logging_util import setup_file_logging
from .server import mcp

_SECRET_SUFFIXES = ("_PASSWORD", "_API_KEY", "_KEY", "_SECRET", "_TOKEN")


def _print_env() -> None:
    print("Environment variables:", file=sys.stderr)
    for key, value in sorted(os.environ.items()):
        if not key.startswith("ODOO_"):
            continue
        if any(key.endswith(s) for s in _SECRET_SUFFIXES):
            print(f"  {key}: ***hidden***", file=sys.stderr)
        else:
            print(f"  {key}: {value}", file=sys.stderr)


def main() -> int:
    """Run the MCP server on the STDIO transport."""
    log_file = setup_file_logging("stdio")

    try:
        print("=== ODOO MCP SERVER STARTING (STDIO) ===", file=sys.stderr)
        print(f"Python version: {sys.version}", file=sys.stderr)
        print(f"Logging to: {log_file}", file=sys.stderr)
        _print_env()

        print("Starting MCP server...", file=sys.stderr)
        sys.stderr.flush()

        mcp.run()

        print("MCP server stopped normally", file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        print("MCP server stopped by user", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
