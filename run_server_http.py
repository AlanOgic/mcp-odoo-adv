#!/usr/bin/env python3
"""
Run the Odoo MCP server with Streamable HTTP transport.

Streamable HTTP transport enables bidirectional streaming over HTTP/2,
suitable for API clients and programmatic integrations.

Environment Variables:
    MCP_HOST: Host to bind to (default: 0.0.0.0)
    MCP_PORT: Port to listen on (default: 8008)
    MCP_HTTP_PATH: HTTP endpoint path (default: /mcp)
    ODOO_URL: Odoo server URL
    ODOO_DB: Database name
    ODOO_USERNAME: Login username
    ODOO_PASSWORD: Login password or API key
    ODOO_TIMEOUT: Connection timeout in seconds (default: 30)
    ODOO_VERIFY_SSL: Whether to verify SSL certificates (default: true)
    HTTP_PROXY: HTTP proxy for Odoo connection (optional)

Usage:
    python run_server_http.py

    # With custom host/port
    MCP_HOST=localhost MCP_PORT=9000 python run_server_http.py

    # Docker
    docker run -p 8008:8008 alanogic/mcp-odoo-adv:http
"""

import os
import sys
from datetime import datetime

# Setup logging to both stderr and file
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"mcp_server_http_{timestamp}.log")


class TeeLogger:
    """Write to both stderr and a log file"""

    def __init__(self, file_path):
        self.terminal = sys.stderr
        self.log = open(file_path, "a")

    def __del__(self):
        """Ensure file is closed when TeeLogger is destroyed"""
        if hasattr(self, "log") and self.log:
            try:
                self.log.close()
            except:
                pass  # Ignore errors during cleanup

    def write(self, message):
        self.terminal.write(message)
        if self.log and not self.log.closed:
            self.log.write(message)
            self.log.flush()

    def flush(self):
        self.terminal.flush()
        if self.log and not self.log.closed:
            self.log.flush()

    def close(self):
        """Explicitly close the log file"""
        if self.log and not self.log.closed:
            self.log.close()


sys.stderr = TeeLogger(log_file)

print(
    f"[{datetime.now().isoformat()}] Starting Advanced Odoo MCP Server (Streamable HTTP Transport)"
)
print(f"Logging to: {log_file}")

from src.odoo_mcp.server import mcp

# Get HTTP configuration from environment
host = os.environ.get("MCP_HOST", "0.0.0.0")
port = int(os.environ.get("MCP_PORT", "8008"))
path = os.environ.get("MCP_HTTP_PATH", "/mcp")

print(f"Streamable HTTP Configuration:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  HTTP Path: {path}")
print(f"  URL: http://{host}:{port}{path}")

# Run with streamable HTTP transport
mcp.run(
    transport="streamable-http",
    host=host,
    port=port,
    path=path,
)
