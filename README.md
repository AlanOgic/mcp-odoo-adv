# Odoo MCP Server Advanced

**Two tools. Infinite possibilities. Full Odoo API access.**

An advanced MCP (Model Context Protocol) server implementation for Odoo ERP systems, enabling AI assistants to interact with Odoo data and functionality through the standardized Model Context Protocol.

**Forked from [tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)** - Thanks to Lê Anh Tuấn for the excellent foundation.

---

## 🎯 Philosophy: Radical Simplicity

**Why just 2 tools?**

Because complexity is the enemy of reliability. Instead of maintaining 7+ specialized tools (most broken or redundant), we provide:

1. **`execute_method`** - Universal access to the entire Odoo API
2. **`batch_execute`** - Atomic multi-operation transactions

That's it. Everything else is just documentation and examples.

### The Power User Advantage

```python
# Instead of specialized "search_employee" tool:
execute_method(model="hr.employee", method="search_read",
               kwargs_json='{"domain": [["name", "ilike", "john"]]}')

# Instead of specialized "search_holidays" tool:
execute_method(model="hr.leave", method="search_read",
               kwargs_json='{"domain": [["date_from", ">=", "2025-01-01"]]}')

# Instead of specialized "deep_read" tool:
execute_method(model="res.partner", method="read",
               args_json='[[263], ["name", "country_id", "invoice_ids"]]')
```

**See? You already have everything you need.** 🚀

---

## 🚀 Quick Start

### Installation

**Option 1: Using uvx (Recommended)**

```bash
# Run directly without installation
uvx --from odoo-mcp odoo-mcp

# Or from source directory
uvx --from . odoo-mcp
```

**Option 2: Traditional pip install**

```bash
# From source
git clone https://github.com/AlanOgic/mcp-odoo-adv.git
cd mcp-odoo-adv
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file:

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password-or-api-key
```

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

**Option 2: Using uvx (Simpler Alternative)**

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["--from", "odoo-mcp", "odoo-mcp"],
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

## 🎓 Learn by Example

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

## 💡 Why This Approach Works

### ✅ Advantages

**1. Reliability**
- No broken specialized tools
- Odoo provides excellent native error messages
- One path to maintain, not seven

**2. Power**
- Full Odoo API access
- No artificial limitations
- Do anything Odoo can do

**3. Simplicity**
- Learn 2 tools, not 7
- Clear mental model
- Easier to debug

**4. Maintainability**
- Less code to maintain
- Focus on documentation, not tools
- Better long-term stability

### ❌ What We Removed (And Why)

We removed 5 specialized tools because they were:

1. **Redundant** - `execute_method` already does everything
2. **Broken** - Most had bugs or limitations
3. **Misleading** - Gave false sense of convenience
4. **Maintenance burden** - More code to maintain and debug

**Removed tools:**
- ❌ `search_employee` - Just use `execute_method` with `hr.employee`
- ❌ `search_holidays` - Just use `execute_method` with `hr.leave`
- ❌ `validate_before_execute` - Odoo's native errors are better
- ❌ `deep_read` - Causes oversized responses, use `read` + `read`
- ❌ `scan_pending_crm_responses` - Too specific, build your own query

---

## 🔥 Features

### Core Capabilities
* **Two Universal Tools**: `execute_method` and `batch_execute` - that's all you need
* **Full Odoo API**: Complete access to all models, methods, and workflows
* **MCP 2025 Compliant**: Latest Model Context Protocol specification (2025-06-18)
* **FastMCP 2.12+**: Built with modern FastMCP framework
* **Python 3.10-3.13**: Tested on all current Python versions

### Multiple Transports
* **STDIO**: For Claude Desktop (default)
* **SSE**: For web browsers and HTTP clients
* **Streamable HTTP**: For API integrations
* See [TRANSPORTS.md](DOCS/TRANSPORTS.md) for details

### Production Ready
* **Comprehensive Error Handling**: Odoo provides excellent native errors
* **Flexible Configuration**: Environment variables or config files
* **Enhanced Logging**: Timestamped logs in `./logs/`
* **HTTP Proxy Support**: `HTTP_PROXY` environment variable
* **SSL Control**: `ODOO_VERIFY_SSL` option
* **Configurable Timeouts**: `ODOO_TIMEOUT` (default: 30s)

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

### Docker

```bash
# STDIO transport
docker run -i --rm --env-file .env alanogic/mcp-odoo-adv:latest

# SSE transport
docker run -p 8000:8000 --env-file .env alanogic/mcp-odoo-adv:sse

# HTTP transport
docker run -p 8000:8000 --env-file .env alanogic/mcp-odoo-adv:http
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

## 🧪 Testing

Run the test suite:

```bash
python test_simplified.py
```

Tests verify:
- Only 2 tools registered
- All specialized tools removed
- Module imports correctly
- Proper tool signatures

---

## 📖 Documentation

- **[COOKBOOK.md](COOKBOOK.md)** - 40+ practical examples (START HERE!)
- **[TRANSPORTS.md](DOCS/TRANSPORTS.md)** - Multiple transport options
- **[CLAUDE.md](DOCS/CLAUDE.md)** - Developer guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

**Development philosophy:**
- Keep it simple
- Avoid specialized tools
- Focus on documentation
- Test thoroughly

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Original project by [Lê Anh Tuấn](https://github.com/tuanle96/mcp-odoo)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Follows [Model Context Protocol](https://modelcontextprotocol.io) specification

---

## 🎯 Project Goals

1. **Simplicity** - Two tools, infinite possibilities
2. **Reliability** - No broken specialized tools
3. **Power** - Full Odoo API access
4. **Documentation** - Excellent examples and guides
5. **Maintainability** - Less code, more stability

---

**Remember**: You don't need specialized tools. You have the full Odoo API at your fingertips. 🌟

**Read the [COOKBOOK](COOKBOOK.md) and start building!**
