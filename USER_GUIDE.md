# Odoo MCP Server - User Guide

**Control your Odoo ERP with AI - Two tools. Infinite possibilities.**

This guide shows you how to connect AI assistants to your Odoo system using the Model Context Protocol (MCP). You'll learn to automate tasks, query data, and manage your business through natural language.

---

## What you'll accomplish

By the end of this guide, you will:

- Connect Claude Desktop to your Odoo instance
- Execute Odoo operations through natural language
- Automate business workflows with AI assistance
- Query and analyze your Odoo data

**Time to complete**: 10 minutes

---

## Prerequisites

Before you start, ensure you have:

- **Odoo instance**: Version 14+ (on-premise or cloud)
- **Odoo credentials**: Username and password/API key with appropriate permissions
- **Python 3.10+**: Installed on your system
- **Claude Desktop** (optional): For the interactive quick-start

### Check your Python version

```bash
python3 --version
# Should show: Python 3.10.x or higher
```

---

## Quick-start: Connect to Odoo in 5 minutes

This quick-start gets you running with STDIO transport (ideal for Claude Desktop).

### Step 1: Get the code

```bash
# Clone the repository
git clone https://github.com/AlanOgic/mcp-odoo-adv.git
cd mcp-odoo-adv

# Install dependencies
pip install -e .
```

**Verify installation**:
```bash
python3 -c "from odoo_mcp import server; print('✅ Installation successful')"
```

### Step 2: Configure your Odoo connection

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your Odoo credentials
nano .env
```

Add your Odoo details:

```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-email@company.com
ODOO_PASSWORD=your-password-or-api-key
```

**Security note**: The `.env` file is git-ignored and stays local to your machine.

### Step 3: Test the connection

```bash
# Run the server
python3 run_server.py
```

You should see:

```
╔══════════════════════════════════════════════════════════════════════════╗
║                          ODOO MCP SERVER                                  ║
║              Two tools. Infinite possibilities. Full API access.         ║
╚══════════════════════════════════════════════════════════════════════════╝

Odoo client configuration:
  URL: https://your-instance.odoo.com
  Database: your-database-name
  Username: your-email@company.com
  ✅ Authenticated successfully with UID: 2
```

**If authentication fails**:
- Verify your `ODOO_URL` includes `https://`
- Confirm `ODOO_DB` matches your database name exactly
- Check that `ODOO_USERNAME` and `ODOO_PASSWORD` are correct
- Ensure your user has API access permissions

### Step 4: Connect to Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Option 1: Using local installation**

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python3",
      "args": ["-m", "odoo_mcp"],
      "cwd": "/absolute/path/to/mcp-odoo-adv",
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USERNAME": "your-email@company.com",
        "ODOO_PASSWORD": "your-password-or-api-key"
      }
    }
  }
}
```

**Replace** `/absolute/path/to/mcp-odoo-adv` with your actual project path (e.g., `/Users/yourname/projects/mcp-odoo-adv`).

**Option 2: Using uvx (Simpler Alternative)**

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["--from", "odoo-mcp", "odoo-mcp"],
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USERNAME": "your-email@company.com",
        "ODOO_PASSWORD": "your-password-or-api-key"
      }
    }
  }
}
```

**Benefits of uvx**:
- No installation needed - uvx downloads and runs automatically
- No path configuration required
- Always uses the latest published version
- Works from anywhere on your system

**Restart Claude Desktop** to activate the connection.

### Step 5: Verify in Claude

Open Claude Desktop and try this prompt:

```
Show me my Odoo server information
```

Claude should respond with your Odoo version and installed modules. You're connected! 🎉

---

## Core concepts

### The two-tool philosophy

This MCP server provides just two tools:

1. **`execute_method`** - Calls any Odoo method on any model
2. **`batch_execute`** - Executes multiple operations atomically

That's it. No specialized tools needed—you have full Odoo API access.

### Why this works

```python
# Instead of specialized tools like "search_employee":
execute_method(
    model="hr.employee",
    method="search_read",
    kwargs_json='{"domain": [["name", "ilike", "john"]]}'
)

# Instead of specialized tools like "create_customer":
execute_method(
    model="res.partner",
    method="create",
    args_json='[{"name": "Acme Corp", "email": "contact@acme.com"}]'
)
```

You learn one pattern, get access to everything.

### Smart limits protect you

The server automatically applies safe limits:

- **Default limit**: 100 records (prevents massive data returns)
- **Maximum limit**: 1000 records (hard cap)
- **Override**: Set your own limit in `kwargs_json`

```python
# Safe: auto-limited to 100 records
execute_method(model="mail.message", method="search_read")

# Custom: explicit limit
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 50}'
)
```

---

## Common tasks

### Search for customers

```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{"fields": ["name", "email", "phone"], "limit": 20}'
)
```

### Create a sales order

```python
execute_method(
    model="sale.order",
    method="create",
    args_json='[{
        "partner_id": 8,
        "order_line": [
            [0, 0, {
                "product_id": 5,
                "product_uom_qty": 2,
                "price_unit": 50.00
            }]
        ]
    }]'
)
```

### Update records

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[1, 2, 3], {"phone": "+1234567890"}]'
)
```

### Run batch operations

```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "create",
            "args_json": '[{"name": "New Customer"}]'
        },
        {
            "model": "sale.order",
            "method": "create",
            "args_json": '[{"partner_id": 123}]'
        }
    ],
    atomic=True  # All succeed or all rollback
)
```

**See [COOKBOOK.md](COOKBOOK.md) for 40+ more examples.**

---

## Transport modes

The server supports three transport modes for different use cases:

### STDIO (Claude Desktop)

**Best for**: Claude Desktop integration
**Command**: `python run_server.py` → select option 1
**Connection**: Process pipes (stdin/stdout)
**Network**: Not required

### SSE (Web browsers)

**Best for**: Web-based AI clients
**Command**: `python run_server_sse.py`
**URL**: `http://0.0.0.0:8009/sse`
**Protocol**: Server-Sent Events

### HTTP (API integrations)

**Best for**: Custom applications
**Command**: `python run_server_http.py`
**URL**: `http://0.0.0.0:8008/mcp`
**Protocol**: Streamable HTTP

---

## Advanced configuration

### Use API keys (Odoo 19+)

For better security with Odoo 19+:

```bash
# In your .env file
ODOO_API_VERSION=json-2
ODOO_API_KEY=your_api_key_here
```

Benefits:
- Bearer token authentication (more secure)
- Better performance
- Future-proof (JSON-RPC deprecated in Odoo 20)

### Proxy configuration

If you need an HTTP proxy:

```bash
# In your .env file
HTTP_PROXY=http://proxy.company.com:8080
```

### Timeout adjustment

For slow connections:

```bash
# In your .env file
ODOO_TIMEOUT=60  # Default: 30 seconds
```

### SSL verification

For self-signed certificates (development only):

```bash
# In your .env file
ODOO_VERIFY_SSL=false  # Default: true
```

---

## Resources and next steps

### Learn more

- **[COOKBOOK.md](COOKBOOK.md)** - 40+ practical examples for common tasks
- **[DOCS/CLAUDE.md](DOCS/CLAUDE.md)** - Technical documentation and architecture
- **[DOCS/TRANSPORTS.md](DOCS/TRANSPORTS.md)** - Detailed transport configuration

### Explore Odoo capabilities

Use these MCP resources in Claude:

- `odoo://server/info` - Your Odoo version and installed modules
- `odoo://models` - All available models
- `odoo://model/res.partner/schema` - Field definitions for a model
- `odoo://workflows` - Business process workflows

### Get help

- **Issues**: [GitHub Issues](https://github.com/AlanOgic/mcp-odoo-adv/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AlanOgic/mcp-odoo-adv/discussions)
- **Original project**: [mcp-odoo](https://github.com/tuanle96/mcp-odoo) by Lê Anh Tuấn

---

## Troubleshooting

### Server won't start

**Problem**: `FileNotFoundError: No Odoo configuration found`

**Solution**: Create a `.env` file with your Odoo credentials (see Step 2).

---

**Problem**: `ModuleNotFoundError: No module named 'dotenv'`

**Solution**: Install dependencies:
```bash
pip install python-dotenv
```

### Authentication fails

**Problem**: `Authentication failed` or `Access Denied`

**Solutions**:
1. Verify your credentials are correct in `.env`
2. Ensure your Odoo user has API access
3. Check if your Odoo instance requires API keys (Odoo 19+)
4. Confirm the database name matches exactly

### Connection timeout

**Problem**: `Connection timeout` or server hangs

**Solutions**:
1. Increase timeout in `.env`: `ODOO_TIMEOUT=60`
2. Check your network connection to Odoo
3. Verify the Odoo URL is accessible from your machine

### Claude Desktop connection

**Problem**: Claude doesn't show Odoo tools

**Solutions**:
1. Restart Claude Desktop completely
2. Verify the `cwd` path in `claude_desktop_config.json` is absolute
3. Check Claude Desktop logs for errors
4. Test the server independently: `python run_server.py`

---

## What's next?

Now that you're connected, try these tasks:

1. **Query your data**: "Show me customers from France"
2. **Create records**: "Create a new sales order for customer #8"
3. **Automate workflows**: "Find all unpaid invoices and send reminders"
4. **Generate reports**: "Summarize this month's sales by product category"

Explore the [COOKBOOK.md](COOKBOOK.md) for detailed examples and patterns.

---

*Built with [FastMCP](https://gofastmcp.com) • Follows [Model Context Protocol](https://modelcontextprotocol.io) specification*
