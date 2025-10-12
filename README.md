# Odoo MCP Server Advanced

**Two tools. Infinite possibilities. Full Odoo API access.**

An advanced MCP (Model Context Protocol) server implementation for Odoo ERP systems, enabling AI assistants to interact with Odoo data and functionality using STDIO, SSE, StreamingHttp.

---

## 🎯 Philosophy: Simplicity & Power

Connect AI assistants to Odoo with just **two universal tools**:

1. **`execute_method`** - Call any Odoo method on any model
2. **`batch_execute`** - Execute multiple operations atomically

No complexity. No limitations. Full Odoo API access.

### To rule them all. What You Can Do

Everything you need, just ask AI: automate, query, manage, customize, develop new modules, integrate with external systems, enhance your Odoo instance through AI.

---

## 🚀 Quick Start

### Installation

**Option 1: Traditional pip install**

```bash
# From source
git clone https://github.com/AlanOgic/mcp-odoo-adv.git
cd mcp-odoo-adv
# Virtual Environment
python3 -m venv .venv
source .venv/bin/activate
# Installation
pip install -e .
```

**Option 2: Using uvx (No Installation)**

```bash
# From source directory
uvx --from . odoo-mcp

```

**Option 3: Using Docker**

```bash
# build STDIO
docker build -t alanogic/mcp-odoo-adv:latest -f Dockerfile .

# build SSE
docker build -t alanogic/mcp-odoo-adv-sse:latest -f Dockerfile.sse .

# build HTTP
docker build -t alanogic/mcp-odoo-adv-http:latest -f Dockerfile.http .

# Run STDIO
docker run --env-file .env alanogic/mcp-odoo-adv:latest

# Run SSE
docker run --env-file .env alanogic/mcp-odoo-adv-sse:latest

# Run HTTP
docker run --env-file .env alanogic/mcp-odoo-adv-http:latest
```

### Configuration

Create a `.env` file (minimum):

```bash
cp .env.example .env
vim .env
```

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password-or-api-key
```

**Optional: Custom Configuration Directory**

Organize multiple Odoo configurations by setting a custom directory:

```bash
# Create custom config directory
export ODOO_CONFIG_DIR=~/mcp-odoo-env
mkdir -p $ODOO_CONFIG_DIR

# Copy and configure
cp .env.example $ODOO_CONFIG_DIR/.env
vim $ODOO_CONFIG_DIR/.env

# Run server (automatically uses custom directory)
python run_server.py
```

This is useful for:
- Managing multiple Odoo instances (dev, staging, production)
- Organizing configs outside project directory
- Docker/Compose deployments with volume mounts

### Run Server

```bash
# STDIO (Claude Desktop)
python run_server.py

# SSE (Web browsers)
python run_server_sse.py

# HTTP (API integrations)
python run_server_http.py
```

### Claude Desktop Setup

**Option 1: Using local installation**

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp"],
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DB": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"
      }
    }
  }
}
```

**Option 2: Using uvx (Recommended - No Installation)**

First, create your credentials in `~/.config/odoo/.env`:

```bash
mkdir -p ~/.config/odoo
cat > ~/.config/odoo/.env << 'EOF'
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
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

**Benefits:**
- No installation required - uvx downloads and runs automatically
- Credentials stored securely in `.env` file (not in config)
- Always uses the latest published version
- Works from anywhere on your system

**Option 3: Using Docker**

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "ODOO_URL=https://your-instance.odoo.com",
        "-e", "ODOO_DB=your-database",
        "-e", "ODOO_USERNAME=your-username",
        "-e", "ODOO_PASSWORD=your-password",
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

---

## 🔧 The Two Tools

### 1. execute_method - The Universal Powerhouse

Execute **ANY** Odoo method on **ANY** model. Full API access. No limitations.

```python
execute_method(
    model="<model_name>",
    method="<method_name>",
    args_json='[...]',      # Positional arguments
    kwargs_json='{...}'     # Keyword arguments
)
```

**Examples:**

```python
# Search customers
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{"fields": ["name", "email"], "limit": 20}'
)

# Create sales order
execute_method(
    model="sale.order",
    method="create",
    args_json='[{"partner_id": 8, "order_line": [[0, 0, {"product_id": 5, "product_uom_qty": 1}]]}]'
)

# Confirm order
execute_method(
    model="sale.order",
    method="action_confirm",
    args_json='[[5]]'
)
```

### 2. batch_execute - Atomic Transactions

Execute multiple operations atomically. All succeed or all rollback.

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
            "args_json": '[{"partner_id": 8}]'
        }
    ],
    atomic=True  # All succeed or all fail
)
```

---

## 📚 Documentation

### Essential Resources

**Before using the tools, check these resources:**

- **`odoo://model/{model}/schema`** - Field definitions, relationships, required fields
- **`odoo://model/{model}/access`** - Your permissions (read/write/create/delete)
- **`odoo://methods/{model}`** - Available methods for a model
- **`odoo://workflows`** - Business workflows (Sales, CRM, Inventory, etc.)
- **`odoo://server/info`** - Odoo version and installed modules

### The Cookbook

**[📖 COOKBOOK.md](COOKBOOK.md)** - 40+ practical examples:

- Searching & filtering
- Creating records
- Updating & deleting
- Working with relationships
- Business workflows
- Batch operations
- Advanced patterns

**Start here!** The cookbook shows you how to accomplish anything with just 2 tools.

### Prompts

**User-selectable templates in Claude's menu:**

- **`search-customers`** - Find customers with filters
- **`create-sales-order`** - Create sales orders step-by-step
- **`odoo-exploration`** - Discover your Odoo instance capabilities

---

## 🎓 Learn with examples

### Example 1: Find Employees

```python
execute_method(
    model="hr.employee",
    method="search_read",
    args_json='[[["name", "ilike", "john"]]]',
    kwargs_json='{"fields": ["name", "job_id", "department_id"], "limit": 10}'
)
```

### Example 2: Time Off Requests

```python
execute_method(
    model="hr.leave",
    method="search_read",
    args_json='[[
        ["employee_id", "=", 1],
        ["date_from", ">=", "2025-01-01"],
        ["state", "=", "validate"]
    ]]',
    kwargs_json='{"fields": ["employee_id", "date_from", "date_to", "holiday_status_id"]}'
)
```

### Example 3: Create Customer + Order (Atomic)

```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "create",
            "args_json": '[{"name": "Acme Corp", "email": "contact@acme.com"}]'
        },
        {
            "model": "sale.order",
            "method": "create",
            "args_json": '[{"partner_id": 123, "order_line": [[0, 0, {"product_id": 5}]]}]'
        }
    ],
    atomic=True
)
```

---

## 💡 Why This Design Works

### ✅ Key Benefits

**1. Universal Access**
- Full Odoo API at your fingertips
- No artificial limitations
- Do anything Odoo can do

**2. Simple & Predictable**
- Learn 2 tools, use everywhere
- Clear mental model
- Easy to debug and maintain

**3. Reliable**
- Odoo provides excellent native error messages
- Direct API access means fewer points of failure
- Stable, production-ready implementation

**4. Flexible**
- Works with several Odoo version (14+)
- Supports all Odoo models and methods
- Extensible through Odoo's native capabilities

---

## 🔥 Features

### AI Integration
* **Claude Desktop Ready**: Seamless integration with Claude Code
* **Two Universal Tools**: Access the entire Odoo API with `execute_method` and `batch_execute`
* **Smart Limits**: Automatic protection against oversized queries (configurable)
* **MCP 2025 Compliant**: Latest Model Context Protocol specification

### Multiple Connection Options
* **STDIO**: Direct integration with Claude Desktop
* **SSE**: Server-Sent Events for web browsers (port 8009)
* **HTTP**: Streamable HTTP for API integrations (port 8008)
* **Docker**: Pre-built containers for all transports

### Enterprise Ready
* **Odoo 14+**: Works with all modern Odoo versions
* **JSON-2 API**: Support for Odoo 19+ Bearer token authentication
* **Flexible Auth**: Environment variables or config files
* **Enhanced Logging**: Timestamped logs in `./logs/`
* **Proxy Support**: HTTP proxy configuration
* **SSL Control**: Configurable SSL verification
* **Python 3.10-3.13**: Tested on all current Python versions

---

## 🚀 Advanced Usage

### Odoo 19+ JSON-2 API (Recommended)

For better security with Odoo 19+:

```bash
export ODOO_API_VERSION=json-2
export ODOO_API_KEY=your_api_key_here
```

Benefits:
- Bearer token authentication (more secure)
- Better performance
- Future-proof (JSON-RPC deprecated in Odoo 20)

### Docker Deployment

```bash
# STDIO transport (Claude Desktop)
docker run -i --rm --env-file .env alanogic/mcp-odoo-adv:latest

# SSE transport (Web browsers)
docker run -p 8009:8009 --env-file .env alanogic/mcp-odoo-adv:sse

# HTTP transport (API integrations)
docker run -p 8008:8008 --env-file .env alanogic/mcp-odoo-adv:http
```

### Domain Operators

Common search operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `["country_id", "=", 75]` |
| `!=` | Not equal | `["active", "!=", false]` |
| `>`, `>=`, `<`, `<=` | Comparison | `["amount_total", ">=", 1000]` |
| `like`, `ilike` | Pattern match | `["name", "ilike", "acme"]` |
| `in`, `not in` | In list | `["state", "in", ["draft", "sent"]]` |

---

## 📖 Documentation

**New to Odoo MCP Server?** Start here:

1. **[USER_GUIDE.md](USER_GUIDE.md)** - Complete setup guide with 5-minute quick-start
2. **[COOKBOOK.md](COOKBOOK.md)** - 45+ practical examples for common tasks
3. **[DOCKER.md](DOCS/DOCKER.md)** - Docker deployment guide (containers, compose, production)
4. **[TRANSPORTS.md](DOCS/TRANSPORTS.md)** - Connection options (STDIO, SSE, HTTP)
5. **[CLAUDE.md](DOCS/CLAUDE.md)** - Technical reference and architecture
6. **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

**Development philosophy:**
- Simplicity first
- Universal tools over specialized ones
- Documentation over complexity
- Reliability through directness

---

## 📝 License

GNU General Public License v3.0 or later (GPL-3.0-or-later) - See [LICENSE](LICENSE) file

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

---

## 🙏 Acknowledgments

- Original project by [Lê Anh Tuấn](https://github.com/tuanle96/mcp-odoo)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Follows [Model Context Protocol](https://modelcontextprotocol.io) specification

---

## 🎯 What's Next?

**Ready to get started?**

1. **Quick Setup**: Follow the [USER_GUIDE.md](USER_GUIDE.md) 5-minute quick-start
2. **Learn by Example**: Browse [COOKBOOK.md](COOKBOOK.md) for 45+ recipes
3. **Explore Your Odoo**: Use the `odoo-exploration` prompt in Claude
4. **Build & Automate**: Create custom workflows with `execute_method`

**Need help?**
- 📖 Check the [USER_GUIDE.md](USER_GUIDE.md) troubleshooting section
- 💬 Open an [issue](https://github.com/AlanOgic/mcp-odoo-adv/issues) on GitHub
- 🌟 Star the repo if you find it useful!

---

**Connect AI to Odoo. Build the future.** 🚀
