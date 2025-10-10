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
- Create a new module to track customer feedback

**Time to complete**: 10 minutes

---

## Prerequisites

Before you start, ensure you have:

- **Odoo instance**: Version 14+ (on-premise or cloud)
- **Odoo credentials**: Username and API key (Odoo user profile -> Account Security -> New API Key)
- **Python 3.10+**: Installed on your system
- **Claude Desktop**: for the quick-start (any other MCP client Works)

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

# Virtual environment setup (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
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
Connecting to Odoo at: https://yourdatabase.odoo.com
  Hostname: yourdatabase.odoo.com
  Timeout: 30s, Verify SSL: True
  JSON-RPC endpoint: https://yourdatabase.odoo.com/jsonrpc
Authenticating with database: yourdatabase, username: your@registereduser.email
  Authenticated successfully with UID: X
```

**If authentication fails**:
- Verify your `ODOO_URL` includes `https://`
- Confirm `ODOO_DB` matches your database name exactly
- Check that `ODOO_USERNAME` is correct
- `ODOO_PASSWORD` is user profile's API key
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

**Option 2: Using uvx (Recommended - No Installation)**

First, create your credentials in `~/.config/odoo/.env`:

```bash
mkdir -p ~/.config/odoo
cat > ~/.config/odoo/.env << 'EOF'
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-email@company.com
ODOO_PASSWORD=your-password-or-api-key
EOF
```

Then add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["--from", "odoo-mcp", "odoo-mcp"]
    }
  }
}
```

**Option 3: Using Docker**

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "ODOO_URL=https://your-instance.odoo.com",
        "-e", "ODOO_DB=your-database-name",
        "-e", "ODOO_USERNAME=your-email@company.com",
        "-e", "ODOO_PASSWORD=your-password-or-api-key",
        "alanogic/mcp-odoo-adv:latest"
      ]
    }
  }
}
```

Or with `.env` file:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", "/absolute/path/to/.env", "alanogic/mcp-odoo-adv:latest"]
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

Instead of using specialised tools, the client uses the 'execute_method' and 'batch_execute' tools, which can do anything you need.
Just begin a new conversation by "use your odoo mcp tools to ..."


---

## Transport modes

The server supports three transport modes for different use cases:

### STDIO (Claude Desktop)

**Best for**: Claude Desktop integration
**Command**: `python run_server.py` or `./run.py` -> select option 1
**Connection**: Process pipes (stdin/stdout)
**Network**: Not required

### SSE (Web browsers)

**Best for**: Web-based AI clients
**Command**: `python run_server_sse.py` or `./run.py` -> select option 2
**URL**: `http://0.0.0.0:8009/sse`
**Protocol**: Server-Sent Events

### HTTP (API integrations)

**Best for**: Custom applications
**Command**: `python run_server_http.py`or `./run.py` -> select option 3
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

1. **Query your data**: "Show my customers from France"
2. **Automate workflows**: "Find all unpaid invoices and send reminders"
3. **Generate reports**: "Summarize this month's sales by product category"
4. **Custom module**: "Create a new module to track customer feedback"

Explore the [COOKBOOK.md](COOKBOOK.md) for detailed examples and patterns.

---

*Built with [FastMCP](https://gofastmcp.com) • Follows [Model Context Protocol](https://modelcontextprotocol.io) specification*
