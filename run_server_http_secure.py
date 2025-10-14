#!/usr/bin/env python3
"""
Run the Odoo MCP server with Streamable HTTP transport + Bearer Token Authentication.

This version adds security middleware to validate Bearer tokens before processing requests.

Environment Variables:
    MCP_BEARER_TOKEN: Required Bearer token for authentication (e.g., "your-secret-token-here")
    MCP_HOST: Host to bind to (default: 0.0.0.0)
    MCP_PORT: Port to listen on (default: 8008)
    MCP_HTTP_PATH: HTTP endpoint path (default: /mcp)
    ODOO_URL: Odoo server URL
    ODOO_DB: Database name
    ODOO_USERNAME: Login username
    ODOO_PASSWORD: Login password or API key

Security:
    - Requires Bearer token in Authorization header
    - Format: "Authorization: Bearer YOUR_TOKEN_HERE"
    - 401 Unauthorized if token is missing or invalid
    - Constant-time comparison to prevent timing attacks

Usage:
    # Set bearer token
    export MCP_BEARER_TOKEN="your-secure-random-token-$(openssl rand -hex 32)"

    # Run server
    python run_server_http_secure.py

    # Client usage
    curl -X POST http://localhost:8008/mcp \
      -H "Authorization: Bearer YOUR_TOKEN_HERE" \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
"""

import os
import sys
import secrets
from datetime import datetime
from typing import Callable

# Setup logging to both stderr and file
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"mcp_server_http_secure_{timestamp}.log")


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
    f"[{datetime.now().isoformat()}] Starting Secure Odoo MCP Server (HTTP + Bearer Auth)"
)
print(f"Logging to: {log_file}")

# Check for required Bearer token
BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN")
if not BEARER_TOKEN:
    print("\n" + "="*80)
    print("❌ SECURITY ERROR: MCP_BEARER_TOKEN environment variable is required!")
    print("="*80)
    print("\nTo fix:")
    print("  1. Generate a secure token:")
    print("     export MCP_BEARER_TOKEN=\"$(openssl rand -hex 32)\"")
    print("\n  2. Or set your own token:")
    print("     export MCP_BEARER_TOKEN=\"your-secret-token-here\"")
    print("\n  3. Then restart the server")
    print("\nNever use simple tokens in production! Use cryptographically random tokens.")
    print("="*80 + "\n")
    sys.exit(1)

# Validate token strength (warn if too weak)
if len(BEARER_TOKEN) < 32:
    print("\n" + "="*80)
    print("⚠️  WARNING: Bearer token is weak (< 32 characters)")
    print("="*80)
    print(f"  Current length: {len(BEARER_TOKEN)} characters")
    print("  Recommended: At least 32 characters (64+ for production)")
    print("\n  Generate a strong token:")
    print("     export MCP_BEARER_TOKEN=\"$(openssl rand -hex 32)\"")
    print("="*80 + "\n")

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
print(f"  Authentication: Bearer Token (length: {len(BEARER_TOKEN)} chars)")
print(f"  Token Preview: {BEARER_TOKEN[:8]}...{BEARER_TOKEN[-8:]}")


# Security middleware for Bearer token validation
def create_auth_middleware(expected_token: str) -> Callable:
    """
    Create middleware that validates Bearer tokens.

    Uses constant-time comparison to prevent timing attacks.
    """
    def auth_middleware(request, call_next):
        """Validate Bearer token before processing request"""
        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")

        # Check format: "Bearer TOKEN"
        if not auth_header.startswith("Bearer "):
            print(f"❌ Unauthorized request from {request.client}: Missing Bearer token")
            return {
                "error": {
                    "code": -32001,
                    "message": "Unauthorized: Missing Bearer token",
                    "data": "Authorization header must be: Bearer YOUR_TOKEN"
                },
                "jsonrpc": "2.0",
                "id": None
            }

        # Extract token
        provided_token = auth_header[7:].strip()  # Remove "Bearer " prefix

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(provided_token, expected_token):
            print(f"❌ Unauthorized request from {request.client}: Invalid Bearer token")
            return {
                "error": {
                    "code": -32001,
                    "message": "Unauthorized: Invalid Bearer token",
                    "data": "The provided token is incorrect"
                },
                "jsonrpc": "2.0",
                "id": None
            }

        # Token is valid - proceed with request
        print(f"✅ Authenticated request from {request.client}")
        return call_next(request)

    return auth_middleware


# Add Bearer token authentication middleware
print("Adding Bearer token authentication middleware...")

class BearerAuthMiddleware:
    """Middleware for Bearer token validation"""

    def __init__(self, expected_token: str):
        self.expected_token = expected_token

    async def __call__(self, context, call_next):
        """Validate Bearer token before processing request"""
        # Only validate on HTTP requests (when context has http_request)
        from fastmcp.server.dependencies import get_http_request

        try:
            request = get_http_request()

            # Get Authorization header
            auth_header = request.headers.get("Authorization", "")

            # Check format: "Bearer TOKEN"
            if not auth_header.startswith("Bearer "):
                print(f"❌ Unauthorized request: Missing Bearer token")
                from fastmcp.exceptions import ToolError
                raise ToolError("Unauthorized: Missing Bearer token. Use: Authorization: Bearer YOUR_TOKEN")

            # Extract token
            provided_token = auth_header[7:].strip()  # Remove "Bearer " prefix

            # Constant-time comparison to prevent timing attacks
            if not secrets.compare_digest(provided_token, self.expected_token):
                print(f"❌ Unauthorized request: Invalid Bearer token")
                from fastmcp.exceptions import ToolError
                raise ToolError("Unauthorized: Invalid Bearer token")

            # Token is valid - proceed with request
            client_info = f"{request.client.host}:{request.client.port}" if request.client else "unknown"
            print(f"✅ Authenticated request from {client_info}")

        except Exception as e:
            # If we can't get request (e.g., STDIO transport), skip auth
            if "No HTTP request" not in str(e):
                raise

        return await call_next(context)

# Initialize middleware
from fastmcp.server.middleware import Middleware

class BearerAuthMiddlewareFastMCP(Middleware):
    """FastMCP-compatible Bearer token authentication middleware"""

    def __init__(self, expected_token: str):
        super().__init__()
        self.expected_token = expected_token

    async def on_message(self, context, call_next):
        """Validate Bearer token on every message"""
        # Get HTTP request if available
        try:
            from fastmcp.server.dependencies import get_http_request
            request = get_http_request()

            # Get Authorization header
            auth_header = request.headers.get("Authorization", "")

            # Check format: "Bearer TOKEN"
            if not auth_header.startswith("Bearer "):
                print(f"❌ Unauthorized request: Missing Bearer token")
                from fastmcp.exceptions import ToolError
                raise ToolError("Unauthorized: Missing Bearer token. Header format: Authorization: Bearer YOUR_TOKEN")

            # Extract token
            provided_token = auth_header[7:].strip()

            # Constant-time comparison
            if not secrets.compare_digest(provided_token, self.expected_token):
                print(f"❌ Unauthorized request: Invalid Bearer token")
                from fastmcp.exceptions import ToolError
                raise ToolError("Unauthorized: Invalid Bearer token")

            # Log successful authentication
            client_info = f"{request.client.host}:{request.client.port}" if request.client else "unknown"
            print(f"✅ Authenticated request from {client_info}")

        except RuntimeError as e:
            # No HTTP request available (e.g., STDIO transport) - skip auth
            if "No HTTP request" not in str(e):
                raise

        return await call_next(context)

# Add middleware to server
mcp.add_middleware(BearerAuthMiddlewareFastMCP(BEARER_TOKEN))

print("\n" + "="*80)
print("🔒 SECURITY ENABLED")
print("="*80)
print("✅ Bearer token authentication middleware active")
print("✅ Constant-time token comparison (timing attack prevention)")
print()
print("Client usage:")
print(f'  curl -X POST http://{host}:{port}{path} \\')
print(f'    -H "Authorization: Bearer {BEARER_TOKEN[:8]}...{BEARER_TOKEN[-8:]}" \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}\'')
print()
print("Python client example:")
print(f"  from fastmcp.client.transports import StreamableHttpTransport")
print(f"  from fastmcp.client.auth import BearerAuth")
print(f'  transport = StreamableHttpTransport("http://{host}:{port}{path}", auth=BearerAuth("YOUR_TOKEN"))')
print("="*80 + "\n")

# Run with streamable HTTP transport + authentication
print("🚀 Starting SECURE Odoo MCP Server (Bearer token required)\n")

mcp.run(
    transport="streamable-http",
    host=host,
    port=port,
    path=path,
)
