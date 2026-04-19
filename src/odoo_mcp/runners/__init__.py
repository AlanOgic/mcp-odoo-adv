"""Transport runners for the Odoo MCP server.

Each submodule exposes a ``main()`` callable wired up as a console script
in ``pyproject.toml``:

    odoo-mcp-http       → runners.http:main
    odoo-mcp-sse        → runners.sse:main
    odoo-mcp-http-secure → runners.http_secure:main
"""
