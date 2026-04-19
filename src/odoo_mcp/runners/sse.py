"""SSE (Server-Sent Events) transport runner (no auth).

Default bind is ``127.0.0.1:8009``. This runner has NO authentication — set
``MCP_HOST=0.0.0.0`` only when running behind an auth layer.

Environment:
    MCP_HOST      Host to bind to (default: 127.0.0.1)
    MCP_PORT      Port to listen on (default: 8009)
    MCP_SSE_PATH  SSE endpoint path (default: /sse)
    ODOO_*        Standard Odoo credentials (see README)
"""
from __future__ import annotations

import os
from datetime import datetime

from ..logging_util import setup_file_logging
from ..server import mcp


def main() -> None:
    log_file = setup_file_logging("sse")
    print(
        f"[{datetime.now().isoformat()}] "
        f"Starting Odoo MCP Server (SSE)"
    )
    print(f"Logging to: {log_file}")

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8009"))
    path = os.environ.get("MCP_SSE_PATH", "/sse")

    print("SSE Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  SSE Path: {path}")
    print(f"  URL: http://{host}:{port}{path}")
    if host == "0.0.0.0":
        print(
            "  ⚠️  Bound to 0.0.0.0 with NO AUTH — place behind an auth layer."
        )

    mcp.run(transport="sse", host=host, port=port, path=path)


if __name__ == "__main__":
    main()
