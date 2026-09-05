"""Streamable HTTP transport with Bearer-token authentication.

Requires ``MCP_BEARER_TOKEN`` at startup (≥32 chars recommended). Uses
``secrets.compare_digest`` for constant-time comparison.

Environment:
    MCP_BEARER_TOKEN  Required Bearer token (use ``openssl rand -hex 32``)
    MCP_HOST          Host to bind to (default: 0.0.0.0 — safe because auth)
    MCP_PORT          Port to listen on (default: 8008)
    MCP_HTTP_PATH     HTTP endpoint path (default: /mcp)
    ODOO_*            Standard Odoo credentials (see README)
"""

from __future__ import annotations

import os
import secrets
import sys
from datetime import datetime
from typing import Any

from fastmcp.server.middleware import Middleware

from ..logging_util import setup_file_logging
from ..server import mcp


class BearerAuthMiddleware(Middleware):
    """Validate a Bearer token on every MCP message."""

    def __init__(self, expected_token: str) -> None:
        super().__init__()
        self._expected_token = expected_token

    async def on_message(self, context: Any, call_next: Any) -> Any:
        try:
            from fastmcp.server.dependencies import get_http_request

            request = get_http_request()
        except RuntimeError as exc:
            if "No HTTP request" in str(exc):
                return await call_next(context)
            raise

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            print("❌ Unauthorized request: Missing Bearer token")
            from fastmcp.exceptions import ToolError

            raise ToolError(
                "Unauthorized: Missing Bearer token. "
                "Header format: Authorization: Bearer YOUR_TOKEN"
            )

        provided_token = auth_header[7:].strip()
        if not secrets.compare_digest(provided_token, self._expected_token):
            print("❌ Unauthorized request: Invalid Bearer token")
            from fastmcp.exceptions import ToolError

            raise ToolError("Unauthorized: Invalid Bearer token")

        client_info = (
            f"{request.client.host}:{request.client.port}"
            if request.client
            else "unknown"
        )
        print(f"✅ Authenticated request from {client_info}")
        return await call_next(context)


def _require_token() -> str:
    token = os.environ.get("MCP_BEARER_TOKEN")
    if not token:
        print("\n" + "=" * 80)
        print("❌ SECURITY ERROR: MCP_BEARER_TOKEN environment variable is required!")
        print("=" * 80)
        print("\nTo fix:")
        print('  export MCP_BEARER_TOKEN="$(openssl rand -hex 32)"')
        print("=" * 80 + "\n")
        sys.exit(1)

    if len(token) < 32:
        print("\n" + "=" * 80)
        print(f"⚠️  WARNING: Bearer token is weak ({len(token)} chars, recommend ≥32)")
        print('  Generate: export MCP_BEARER_TOKEN="$(openssl rand -hex 32)"')
        print("=" * 80 + "\n")

    return token


def main() -> None:
    log_file = setup_file_logging("http_secure")
    print(
        f"[{datetime.now().isoformat()}] "
        f"Starting Odoo MCP Server (HTTP + Bearer Auth)"
    )
    print(f"Logging to: {log_file}")

    token = _require_token()

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8008"))
    path = os.environ.get("MCP_HTTP_PATH", "/mcp")

    print("Streamable HTTP Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  HTTP Path: {path}")
    print(f"  URL: http://{host}:{port}{path}")
    print(f"  Authentication: Bearer Token ({len(token)} chars)")
    print(f"  Token Preview: {token[:8]}...{token[-8:]}")

    mcp.add_middleware(BearerAuthMiddleware(token))

    print("\n" + "=" * 80)
    print("🔒 SECURITY ENABLED — constant-time token comparison active")
    print("=" * 80 + "\n")

    mcp.run(transport="streamable-http", host=host, port=port, path=path)


if __name__ == "__main__":
    main()
