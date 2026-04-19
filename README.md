# Odoo MCP Server Advanced

**Two universal tools. A growing cookbook. Full Odoo API access for AI assistants.**

An advanced MCP (Model Context Protocol) server for Odoo ERP — STDIO, SSE, and Streamable HTTP transports — that gives Claude, Cursor, ChatGPT-via-MCP and other AI hosts direct access to your Odoo data and workflows.

> **AI assistants:** read [AGENTS.md](./AGENTS.md) for the tool-first quick reference.

---

## 🎯 Philosophy: Simplicity & Power

Connect AI assistants to Odoo with **two universal tools** plus a self-improving knowledge base:

1. **`execute_method`** — call any Odoo method on any model
2. **`batch_execute`** — execute multiple operations atomically (with `@N` result references)
3. **`add_cookbook_pattern`** — document hard-won recipes after ≥4 failed attempts

Plus 11 discovery resources, 3 prompts, and an `odoo://cookbook/patterns` resource that surfaces past lessons. No specialized tools, no validation layer, no artificial limits — full Odoo API.

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
odoo-mcp
```

This is useful for:
- Managing multiple Odoo instances (dev, staging, production)
- Organizing configs outside project directory
- Docker/Compose deployments with volume mounts

### Run Server

After `pip install -e .`, four console scripts are wired up:

```bash
# STDIO (Claude Desktop, Claude Code, Cursor)
odoo-mcp                      # or: python -m odoo_mcp

# SSE (browsers, port 8009)
odoo-mcp-sse

# Streamable HTTP (API integrations, port 8008)
odoo-mcp-http

# HTTP with Bearer auth (production behind a reverse proxy)
odoo-mcp-http-secure
```

Each runner streams logs to `./logs/mcp_server_<transport>_<timestamp>.log` plus stderr.

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

## 🔧 The Tools

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

Execute multiple operations atomically. All succeed or all rollback. Use `"@N"` (1-indexed) inside `args_json` to reference a previous operation's result.

```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "create",
         "args_json": '[{"name": "Acme"}]'},
        {"model": "sale.order", "method": "create",
         "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 5, "product_uom_qty": 1}]]}]'},
        {"model": "sale.order", "method": "action_confirm",
         "args_json": '[[@2]]'}
    ],
    atomic=True
)
```

### 3. add_cookbook_pattern - Self-Improving Knowledge Base

After **≥4 failed approaches** to the same problem, document the working solution so future sessions skip the trial-and-error:

```python
add_cookbook_pattern(
    problem="Search products by attribute value",
    failed_approaches=[
        "Used = on many2many field",
        "Tried dotted notation",
        "Used wrong model",
        "Passed scalar instead of list to in",
    ],
    working_solution='execute_method(model="product.template", method="search_read", args_json=\'[[["product_template_attribute_value_ids", "in", [123]]]]\')',
    why_it_works="Many2many fields require in with a list, not =",
    key_lesson="For m2m: always 'in' with a list, never '=' with scalar"
)
```

The `≥4` threshold is enforced — shallow trial-and-error stays out of the cookbook.

---

## 📚 Documentation

### Discovery resources (read before guessing)

| Resource | Returns |
|---|---|
| `odoo://models` | All models in this instance |
| `odoo://model/{model}/schema` | Full schema — fields, types, requireds, relationships |
| `odoo://model/{model}/access` | Your CRUD permissions on this model |
| `odoo://methods/{model}` | Methods available on this model |
| `odoo://workflows` | Business workflows from installed modules |
| `odoo://server/info` | Odoo version + installed modules |
| `odoo://cookbook/patterns` | Learned Patterns from past sessions (read after first failure) |

Plus `odoo://record/{model}/{id}`, `odoo://search/{model}/{domain}`, `odoo://fields/{model}`, `odoo://model/{model}` for one-off reads.

### The Cookbook

**[📖 COOKBOOK.md](COOKBOOK.md)** — 45+ practical examples:

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

- **`search-customers`** — Find customers with filters
- **`create-sales-order`** — Create sales orders step-by-step
- **`odoo-exploration`** — Discover your Odoo instance capabilities

### Claude Code skills

Eight skills ship in [`.claude/skills/`](./.claude/skills/) and auto-activate on relevant requests when this repo is opened in Claude Code. They wrap the cookbook into focused, trigger-aware guides:

- `odoo-mcp-searching` — domains, operators, name_search
- `odoo-mcp-efficient-queries` — pagination, fields, `read_group`
- `odoo-mcp-crud` — create/write/unlink, archive vs delete
- `odoo-mcp-relationships` — m2o/o2m/m2m command tuples
- `odoo-mcp-workflows` — `action_confirm`, `action_post`, `button_validate`
- `odoo-mcp-batch` — atomic transactions with `@N` references
- `odoo-mcp-real-world` — HR/CRM/inventory cross-model recipes
- `odoo-mcp-learned-patterns` — cookbook read/write workflow

Other MCP clients (Claude Desktop, Cursor) get the same knowledge portably via `COOKBOOK.md` and the `odoo://cookbook/patterns` resource.

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
* **Claude Desktop / Claude Code / Cursor Ready**: Works with any MCP host
* **Universal Tools**: `execute_method` + `batch_execute` reach the entire Odoo API
* **Self-improving cookbook**: `odoo://cookbook/patterns` resource + `add_cookbook_pattern` tool grow the institutional knowledge automatically
* **Smart Limits**: Automatic protection against oversized queries (DEFAULT=100, MAX=1000)
* **MCP 2025-06-18 spec**: Built on FastMCP 2.12+

### Multiple Connection Options
* **STDIO**: Direct integration with Claude Desktop
* **SSE**: Server-Sent Events for web browsers (port 8009)
* **HTTP**: Streamable HTTP for API integrations (port 8008)
* **Docker**: Pre-built containers for all transports

### Enterprise Ready
* **Odoo 18 primary target**: Works out of the box with Odoo 14-18 via JSON-RPC
* **Odoo 19+ opt-in**: JSON-2 Bearer token API available via `ODOO_API_VERSION=json-2`
* **Flexible Auth**: Environment variables or config files
* **Enhanced Logging**: Timestamped logs in `./logs/`
* **Proxy Support**: HTTP proxy configuration
* **SSL Control**: Configurable SSL verification
* **Python 3.10-3.13**: Tested on all current Python versions

---

## 🚀 Advanced Usage

### API keys

**Odoo 18 (default):** use the JSON-RPC path with an API key in the password slot.

```bash
export ODOO_API_VERSION=json-rpc   # default, can be omitted
export ODOO_PASSWORD=your_api_key_here
```

Generate the key in Odoo: `Preferences → Account Security → New API Key`.

**Odoo 19+ (opt-in upgrade):** JSON-2 Bearer token API.

```bash
export ODOO_API_VERSION=json-2
export ODOO_API_KEY=your_api_key_here
```

JSON-2 is future-proof — JSON-RPC is scheduled for removal in Odoo 20 (fall 2026).

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
