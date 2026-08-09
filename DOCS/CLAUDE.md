# CLAUDE.md - Odoo MCP Server v1.0.0-beta.2

This file provides guidance to Claude Code (claude.ai/code) when working with the Odoo MCP Server Advanced.

**Philosophy: Radical Simplicity + Self-Improving Knowledge**
- **Three tools**: `execute_method`, `batch_execute`, `add_cookbook_pattern`
- **Eight resources**: 7 Odoo discovery resources + `odoo://cookbook/patterns`
- **Infinite possibilities**: Full Odoo API access
- **Smart limits**: Automatic protection against massive data returns (DEFAULT=100, MAX=1000)
- **Self-learning**: cookbook resource + write tool capture hard-won recipes (≥4-failure threshold)

---

## Quick Start

### Installation

**Recommended: uvx (no installation needed)**
```bash
# Run directly
uvx --from odoo-mcp odoo-mcp

# From source directory
uvx --from . odoo-mcp
```

**Traditional: pip install**
```bash
# From source with dev dependencies
pip install -e ".[dev]"

# Or from PyPI (when published)
pip install odoo-mcp
```

### Configuration

**Create `.env` file:**
```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password-or-api-key
```

**Optional environment variables:**
```bash
ODOO_TIMEOUT=30           # Connection timeout (default: 30s)
ODOO_VERIFY_SSL=true      # SSL verification (default: true)
HTTP_PROXY=http://proxy   # HTTP proxy for Odoo connection
```

### Running the Server

After `pip install -e .`, four console scripts are available (defined in `pyproject.toml [project.scripts]`):

| Script | Module | Default bind | Notes |
|---|---|---|---|
| `odoo-mcp` | `odoo_mcp.__main__:main` | stdio | Claude Desktop, Claude Code, Cursor |
| `odoo-mcp-sse` | `odoo_mcp.runners.sse:main` | `0.0.0.0:8009/sse` | Browsers, legacy MCP clients |
| `odoo-mcp-http` | `odoo_mcp.runners.http:main` | `127.0.0.1:8008/mcp` | Streamable HTTP (no auth — bind to localhost) |
| `odoo-mcp-http-secure` | `odoo_mcp.runners.http_secure:main` | `0.0.0.0:8008/mcp` | Bearer-token auth + IP allowlist |

```bash
# STDIO (Claude Desktop / Claude Code / Cursor)
odoo-mcp                # or: python -m odoo_mcp
uvx --from . odoo-mcp   # zero-install runner

# SSE (web browsers, legacy)
odoo-mcp-sse

# Streamable HTTP (API integrations)
odoo-mcp-http

# Secure HTTP (production behind reverse proxy)
MCP_BEARER_TOKEN=$(openssl rand -hex 32) odoo-mcp-http-secure
```

Each runner streams to `./logs/mcp_server_<transport>_<timestamp>.log`.

**Docker:**
```bash
# STDIO
docker run -i --rm --env-file .env alanogic/mcp-odoo-adv

# SSE
docker run -p 8009:8009 --env-file .env alanogic/mcp-odoo-adv:sse

# HTTP
docker run -p 8008:8008 --env-file .env alanogic/mcp-odoo-adv:http
```

---

## Claude Desktop Setup

**Option 1: uvx (Recommended)**

Add to `claude_desktop_config.json`:
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

**Option 2: Python module**
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

---

## Architecture Overview

### Module layout

```
src/odoo_mcp/
├── __main__.py        # STDIO entry point (odoo-mcp)
├── server.py          # MCP server: tools, resources, prompts (940 LOC)
├── odoo_client.py     # OdooClient (JSON-RPC + JSON-2)
├── domain.py          # search-domain normalization (extracted from server)
├── limits.py          # smart-limit policy (DEFAULT=100, MAX=1000)
├── logging_util.py    # TeeLogger + setup_file_logging (shared by runners)
├── cookbook.py        # Learned Patterns read/write (≥4-failure threshold)
└── runners/
    ├── http.py         # Streamable HTTP runner (odoo-mcp-http)
    ├── sse.py          # SSE runner (odoo-mcp-sse)
    └── http_secure.py  # Bearer-auth HTTP (odoo-mcp-http-secure)

tests/
├── test_domain.py       # 31 tests — pure domain normalization
├── test_limits.py       # 31 tests — pure smart-limit policy
├── test_cookbook.py     # 16 tests — pure COOKBOOK read/write
└── test_mcp_surface.py  # 17 tests — in-memory MCP round-trips
```

**MCP Server Layer** (`src/odoo_mcp/server.py`)
- Built on FastMCP 3.x (`fastmcp>=3.2,<4`). The MCP protocol revision is
  negotiated by FastMCP and the `mcp` SDK — this server does not pin one.
- **3 tools**: `execute_method`, `batch_execute`, `add_cookbook_pattern`
- **8 resources** — clients see 4 concrete (`odoo://models`, `odoo://workflows`,
  `odoo://server/info`, `odoo://cookbook/patterns`) plus 4 templates, which are
  returned by `resources/templates/list`, *not* `resources/list`
- **3 prompts**: `search-customers`, `create-sales-order`, `odoo-exploration`
  — each returns a plain string; FastMCP 3 rejects the 2.x list-of-dicts shape
- Pydantic models for type-safe responses

**Odoo Client Layer** (`src/odoo_mcp/odoo_client.py`)
- `OdooClient`: JSON-RPC client (Odoo 14-18 default) with optional JSON-2 upgrade for Odoo 19+
- JSON-2 path uses Bearer token auth with automatic token refresh
- Singleton pattern via `get_odoo_client()`

### What Was Removed (v1.0 Simplification)

**Removed 5 specialized tools** (~600 lines):
- ❌ `search_employee` - Use `execute_method` with `hr.employee`
- ❌ `search_holidays` - Use `execute_method` with `hr.leave`
- ❌ `validate_before_execute` - Odoo's native errors are better
- ❌ `deep_read` - Caused oversized responses
- ❌ `scan_pending_crm_responses` - Too specific

**Removed 2 prompts**:
- ❌ `troubleshoot-operation` - Generic troubleshooting is better
- ❌ `draft-crm-responses` - Replaced by COOKBOOK examples

**Why?**
- Power users can do everything with `execute_method`
- Specialized tools were redundant/broken
- Focus on documentation (COOKBOOK.md) over tools
- Simpler codebase = more reliable

---

## The Two Tools

### 1. execute_method

Universal access to the entire Odoo API.

**Signature:**
```python
execute_method(
    model: str,              # Odoo model name (e.g., "res.partner")
    method: str,             # Odoo method name (e.g., "search_read")
    args_json: str = "[]",   # Positional arguments as JSON
    kwargs_json: str = "{}"  # Keyword arguments as JSON
)
```

**Response:**
```python
{
    "success": bool,
    "result": Any,        # Method return value
    "error": str | None   # Error message if failed
}
```

**Smart Limits (Automatic):**
- DEFAULT_LIMIT: 100 records (auto-applied if no limit specified)
- MAX_LIMIT: 1000 records (hard cap on user requests)
- Override: Set `"limit": N` in kwargs_json
- Unlimited: Set `"limit": 0` (warns about massive datasets)

**Examples:**
```python
# Search customers
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{"fields": ["name", "email"], "limit": 50}'
)

# Create record
execute_method(
    model="res.partner",
    method="create",
    args_json='[{"name": "New Customer", "email": "customer@example.com"}]'
)

# Update record
execute_method(
    model="res.partner",
    method="write",
    args_json='[[123], {"phone": "+1234567890"}]'
)

# Delete record
execute_method(
    model="res.partner",
    method="unlink",
    args_json='[[123]]'
)
```

### 2. batch_execute

Execute multiple operations atomically (all succeed or all rollback).

**Signature:**
```python
batch_execute(
    operations: List[dict],  # List of operations to execute
    atomic: bool = True      # Rollback all if any fails
)
```

**Operation Format:**
```python
{
    "model": str,
    "method": str,
    "args_json": str,
    "kwargs_json": str
}
```

**Response:**
```python
{
    "success": bool,
    "results": List[dict],           # Individual operation results
    "total_operations": int,
    "successful_operations": int,
    "failed_operations": int,
    "error": str | None
}
```

**Example:**
```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "create",
            "args_json": '[{"name": "Customer A"}]'
        },
        {
            "model": "sale.order",
            "method": "create",
            "args_json": '[{"partner_id": 123, "date_order": "2025-01-01"}]'
        }
    ],
    atomic=True  # All or nothing
)
```

---

## MCP Resources

Eight resources. Use them for read-only context — anything that mutates state
or needs runtime filtering goes through `execute_method`.

Note how clients see them: the four with `{param}` placeholders are **resource
templates**, returned by `resources/templates/list`. A client that only reads
`resources/list` sees just the four concrete URIs.

### Odoo discovery (7)

| URI | Kind | Purpose |
|---|---|---|
| `odoo://models` | concrete | All Odoo models — name + display name |
| `odoo://workflows` | concrete | Workflow hints based on installed modules (sale, stock, crm, hr, account, project) |
| `odoo://server/info` | concrete | Odoo version, database, installed modules |
| `odoo://model/{model}/schema` | template | **Canonical schema** — fields, types, requireds, relationships, defaults |
| `odoo://model/{model}/access` | template | Per-op permissions (read/write/create/unlink) for current user |
| `odoo://methods/{model}` | template | Common ORM methods + usage example |
| `odoo://record/{model}/{id}` | template | Single-record lookup by id (all fields) |

There is no `odoo://model/{model}`, no `odoo://fields/{model}`, and no
`odoo://search/{model}/{domain}` — earlier revisions of this document listed
them, but they were never implemented. For a field list, use
`odoo://model/{model}/schema`; for a search, use `execute_method`.

### Self-improving knowledge (1, concrete)

| URI | Purpose |
|---|---|
| `odoo://cookbook/patterns` | **Learned Patterns** section of `COOKBOOK.md` — recipes from ≥4-failure problems. High priority (0.95) so clients consult it early when troubleshooting. |

The cookbook resource pairs with the `add_cookbook_pattern` tool for write access.
Together they implement the self-learning loop:

```
Try execute_method → fail → read odoo://cookbook/patterns
  → recipe exists → apply
  → no recipe → keep trying
                  → ≥4 failures → add_cookbook_pattern (write what worked)
```

---

## MCP Prompts

**1. search-customers**
- Guide for searching and filtering customers
- Uses execute_method with res.partner

**2. create-sales-order**
- Step-by-step sales order creation
- Uses batch_execute for related records

**3. odoo-exploration**
- Discovering models, fields, and relationships
- Uses resources and execute_method

---

## Claude Code Skills

Eight skills ship in `.claude/skills/` and auto-activate on relevant requests
when this repo is opened in Claude Code. They are **client-side** (Claude Code
only) — other MCP hosts get the same knowledge via the cookbook resource and
`COOKBOOK.md`.

| Skill | Trigger |
|---|---|
| `odoo-mcp-searching` | Building search domains / filters |
| `odoo-mcp-efficient-queries` | Pagination, field scoping, `read_group` |
| `odoo-mcp-crud` | Create/write/unlink, archive vs delete |
| `odoo-mcp-relationships` | many2one / one2many / many2many command tuples |
| `odoo-mcp-workflows` | `action_confirm`, `action_post`, `button_validate` |
| `odoo-mcp-batch` | Atomic transactions with `@N` references |
| `odoo-mcp-real-world` | HR / CRM / inventory cross-model recipes |
| `odoo-mcp-learned-patterns` | When to read/write the cookbook resource |

See [`.claude/skills/README.md`](../.claude/skills/README.md) for the contributor
guide.

---

## Smart Limits System

### Why Limits?

Without limits, searching `mail.message` could return **GBs of data** (thousands of emails).

### How It Works

**Automatic Application:**
```python
# User doesn't specify limit
execute_method(model="mail.message", method="search_read")
# → Automatically limited to 100 records

# User requests too many
execute_method(model="mail.message", method="search_read",
               kwargs_json='{"limit": 5000}')
# → Capped at 1000 records, warning logged
```

**Override Limits:**
```python
# Custom limit (within max)
kwargs_json='{"limit": 500}'  # OK, returns 500

# Unlimited (use with caution!)
kwargs_json='{"limit": 0}'    # WARNING: May return GBs
kwargs_json='{"limit": false}' # WARNING: May return GBs
```

### Efficient Querying Patterns

**1. Specify Fields**
```python
# ❌ Bad: Returns all fields
execute_method(model="mail.message", method="search_read")

# ✅ Good: Only needed fields
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"fields": ["date", "subject", "author_id"]}'
)
```

**2. Filter Aggressively**
```python
# ❌ Bad: All messages
execute_method(model="mail.message", method="search_read")

# ✅ Good: Filtered by date and type
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[
        ["model", "=", "crm.lead"],
        ["date", ">=", "2025-01-01"],
        ["message_type", "=", "email"]
    ]]',
    kwargs_json='{"fields": ["date", "subject"]}'
)
```

**3. Use Pagination**
```python
# Page 1 (records 0-99)
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 100, "offset": 0}'
)

# Page 2 (records 100-199)
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 100, "offset": 100}'
)
```

**4. Count First**
```python
# Check total count before fetching
execute_method(
    model="mail.message",
    method="search_count",
    args_json='[[["model", "=", "crm.lead"]]]'
)
# Returns: 1247

# Then paginate appropriately
# 1247 records / 100 per page = 13 pages
```

---

## Development Commands

### Code Quality
```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type checking
mypy src/

# Run all quality checks
black . && isort . && ruff check . && mypy src/
```

### Building & Publishing
```bash
# Build package
python -m build

# Publish to PyPI (requires credentials)
twine upload dist/*

# Build Docker images
docker build -t mcp/odoo:latest -f Dockerfile .
docker build -t mcp/odoo:sse -f Dockerfile.sse .
docker build -t mcp/odoo:http -f Dockerfile.http .
```

### Testing
```bash
# Test transports (requires running Odoo instance)
python test_transports_real.py

# Test smart limits
python test_limits.py
```

### Debugging

**Enhanced logging (all transports):**

Every runner tees stderr to a file via `logging_util.setup_file_logging`, so this
is not specific to one entry point.

```bash
# Logs to both stderr and ./logs/mcp_server_<transport>_<timestamp>.log
odoo-mcp

# View real-time logs
tail -f logs/mcp_server_*.log
```

**Environment Diagnostics:**
```bash
# Prints all ODOO_* variables on startup
python -m odoo_mcp
# Shows: Python version, environment vars, available methods
```

---

## Technical Details

### Odoo API Authentication

**JSON-RPC (default — Odoo 14-18)**:
- Session-based authentication via `authenticate` call → UID
- UID + password/API key sent with each `/jsonrpc` request
- No XML-RPC: the client speaks JSON-RPC only (faster, smaller payloads)
- On Odoo 18, put an API key in the password slot for hardened auth

**JSON-2 API (opt-in — Odoo 19+ only)**:
- Bearer token authentication, automatic refresh
- Session management via cookies
- Endpoints: `/api/v2/authenticate`, `/api/v2/call`
- Enable with `ODOO_API_VERSION=json-2` + `ODOO_API_KEY=<token>`

### Domain Normalization

The `execute_method` tool automatically normalizes domain parameters:

**Supported Formats:**
```python
# List format (Odoo native)
[["field", "operator", "value"], ...]

# Object format (AI-friendly)
{"conditions": [{"field": "...", "operator": "...", "value": "..."}]}

# JSON string
'[["field", "=", "value"]]'

# Single condition (auto-wrapped)
["field", "=", "value"]
```

**Normalization Process:**
1. Unwraps nested domains: `[[domain]]` → `[domain]`
2. Converts object format to list format
3. Parses JSON strings
4. Validates conditions (3-element lists or operators)
5. Preserves logic operators (`&`, `|`, `!`)

### Stateless Design

- Each request creates fresh operation context
- No persistent state between requests
- Singleton `OdooClient` shared across requests
- Clean request/response cycle

### Error Handling

- Connection errors: `ConnectionError` with details
- Authentication failures: `ValueError` with context
- All errors logged to stderr
- Detailed diagnostics on startup

### Python Version

- **Required**: Python ≥3.10
- **Tested**: Python 3.10, 3.11, 3.12, 3.13
- **Configured**: `pyproject.toml` line 10

### Dependencies

```toml
[project]
dependencies = [
    "fastmcp>=2.12.0",  # MCP framework (2025-06-18 spec)
    "requests>=2.31.0", # HTTP client
]

[project.optional-dependencies]
dev = [
    "black",    # Code formatter
    "isort",    # Import sorter
    "mypy",     # Type checker
    "ruff",     # Fast linter
    "build",    # Package builder
    "twine",    # PyPI uploader
]
```

### Package Structure

```
mcp-odoo-adv/
├── src/odoo_mcp/
│   ├── __init__.py       # Package init
│   ├── __main__.py       # STDIO entry point (odoo-mcp command)
│   ├── server.py         # MCP surface (3 tools, 8 resources, 3 prompts)
│   ├── odoo_client.py    # Odoo JSON-RPC (14-18) + JSON-2 (19+) client
│   ├── domain.py         # Search-domain normalization (pure)
│   ├── limits.py         # Smart-limit policy (pure)
│   ├── cookbook.py       # COOKBOOK.md Learned Patterns read/write (pure)
│   ├── logging_util.py   # TeeLogger — stderr to terminal + file
│   └── runners/
│       ├── http.py           # Streamable HTTP  (odoo-mcp-http, 8008)
│       ├── http_secure.py    # HTTP + Bearer auth (odoo-mcp-http-secure)
│       └── sse.py            # SSE (odoo-mcp-sse, 8009) — deprecated
├── tests/
│   ├── test_domain.py       # pure domain normalization
│   ├── test_limits.py       # pure smart-limit policy
│   ├── test_cookbook.py     # pure COOKBOOK read/write
│   └── test_mcp_surface.py  # in-memory MCP round-trips
├── pyproject.toml        # Package config (setuptools)
├── fastmcp.json          # MCP server metadata
├── README.md             # User documentation
├── AGENTS.md             # Assistant-facing quick reference
├── COOKBOOK.md           # 45+ usage examples + Learned Patterns
├── CHANGELOG.md          # Version history
├── SECURITY.md           # Hardening guide
├── DOCS/
│   ├── CLAUDE.md         # This file
│   ├── TRANSPORTS.md     # Transport details
│   ├── DOCKER.md         # Container deployment
│   ├── SECURITY.md       # Security reference
│   └── STREAMINGHTTP_GUIDE.md
├── LICENSE               # GPL-3.0-or-later
├── Dockerfile            # STDIO container
├── Dockerfile.sse        # SSE container
├── Dockerfile.http       # HTTP container
├── nginx.conf.example    # Reverse-proxy template
├── .env.example          # Environment template
└── odoo_config.json.example  # Config template
```

---

## Common Patterns

See **COOKBOOK.md** for 40+ detailed examples covering:

### Core Operations
- Searching & reading records
- Creating records
- Updating records
- Deleting records
- Counting records

### Advanced Patterns
- Many2one relationships
- One2many relationships
- Many2many relationships
- Computed fields
- Custom methods
- Workflow actions
- Batch operations
- Error handling

### Efficiency Patterns
- Pagination strategies
- Field selection
- Aggressive filtering
- Count-before-fetch
- Batch processing

---

## Troubleshooting

### Problem: uvx command not found

**Solution:**
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Problem: Connection timeout

**Solution:**
```bash
# Increase timeout (default: 30s)
export ODOO_TIMEOUT=60
python -m odoo_mcp
```

### Problem: SSL certificate verification fails

**Solution:**
```bash
# Disable SSL verification (not recommended for production)
export ODOO_VERIFY_SSL=false
python -m odoo_mcp
```

### Problem: HTTP proxy required

**Solution:**
```bash
# Set HTTP proxy
export HTTP_PROXY=http://proxy.company.com:8080
python -m odoo_mcp
```

### Problem: Authentication fails

**Check:**
1. ODOO_URL is correct (include https://)
2. ODOO_DB matches database name
3. ODOO_USERNAME has API access
4. ODOO_PASSWORD is correct (or use API key)

**Debug:**
```bash
# See authentication details on startup
python -m odoo_mcp 2>&1 | grep -i auth
```

### Problem: Smart limits blocking legitimate queries

**Solution:**
```python
# Override with explicit limit
execute_method(
    model="your.model",
    method="search_read",
    kwargs_json='{"limit": 500}'  # Up to 1000
)

# Or use pagination
for page in range(10):
    execute_method(
        model="your.model",
        method="search_read",
        kwargs_json=f'{{"limit": 100, "offset": {page * 100}}}'
    )
```

### Problem: Need more than MAX_LIMIT (1000) records

**Solution:**
```python
# Use pagination in a loop
all_records = []
offset = 0
limit = 1000

while True:
    result = execute_method(
        model="your.model",
        method="search_read",
        kwargs_json=f'{{"limit": {limit}, "offset": {offset}}}'
    )

    records = result['result']
    if not records:
        break

    all_records.extend(records)
    offset += limit
```

---

## Best Practices

### 1. Always Specify Fields
```python
# ❌ Bad: Returns all fields (slow, large payload)
execute_method(model="res.partner", method="search_read")

# ✅ Good: Only needed fields
execute_method(
    model="res.partner",
    method="search_read",
    kwargs_json='{"fields": ["name", "email", "phone"]}'
)
```

### 2. Filter Before Fetching
```python
# ❌ Bad: Fetch all then filter in code
all_partners = execute_method(model="res.partner", method="search_read")
# Then filter in Python...

# ✅ Good: Filter in Odoo
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0], ["country_id.code", "=", "US"]]]'
)
```

### 3. Use Batch Operations for Related Records
```python
# ✅ Atomic: All succeed or all rollback
batch_execute(operations=[
    {
        "model": "res.partner",
        "method": "create",
        "args_json": '[{"name": "Customer"}]'
    },
    {
        "model": "sale.order",
        "method": "create",
        "args_json": '[{"partner_id": 123}]'
    }
], atomic=True)
```

### 4. Check Count Before Large Queries
```python
# 1. Count first
count_result = execute_method(
    model="mail.message",
    method="search_count",
    args_json='[[["model", "=", "crm.lead"]]]'
)

total = count_result['result']
# Returns: 10000

# 2. Decide strategy based on count
if total > 1000:
    # Use pagination
    pass
else:
    # Fetch all
    pass
```

### 5. Handle Errors Gracefully
```python
result = execute_method(...)

if not result['success']:
    print(f"Error: {result['error']}")
    # Handle error appropriately
else:
    data = result['result']
    # Process data
```

---

## Version History

### v1.0.0-beta (Current) - Radical Simplification
- **BREAKING**: Removed 5 specialized tools
- **BREAKING**: Removed 2 prompts
- **NEW**: Smart limits system (DEFAULT_LIMIT=100, MAX_LIMIT=1000)
- **NEW**: Comprehensive COOKBOOK.md with 40+ examples
- **NEW**: uvx support for zero-install usage
- **IMPROVED**: Minimalist philosophy documentation
- **FIXED**: Python version requirement (3.10+, was incorrectly 3.12+)

### v0.0.4 - Transport Support
- Added SSE transport (port 8009)
- Added Streamable HTTP transport (port 8008)
- Enhanced logging to ./logs/ directory
- Docker images for all transports

### v0.0.3 - JSON-2 API Migration
- Migrated from XML-RPC to JSON-2 API (Odoo 19+)
- JWT Bearer token authentication
- Automatic token refresh
- Legacy XML-RPC fallback support

### v0.0.2 - MCP 2025 Compliance
- Upgraded to FastMCP 2.12+
- MCP 2025-06-18 spec compliance
- Resource annotations
- Output schemas

### v0.0.1 - Initial Release
- Forked from tuanle96/mcp-odoo
- Basic XML-RPC client
- 7 specialized tools
- STDIO transport only

---

## References

- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **FastMCP Framework**: https://gofastmcp.com
- **Odoo API Documentation**: https://www.odoo.com/documentation/
- **Project Repository**: https://github.com/AlanOgic/mcp-odoo-adv
- **Original Fork**: https://github.com/tuanle96/mcp-odoo

---

*Odoo MCP Server Advanced v1.0.0-beta*
*Two tools. Infinite possibilities. Full Odoo API access.*
