# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Odoo MCP Server Advanced** - An MCP (Model Context Protocol) server providing AI assistants with full access to Odoo ERP systems through just two universal tools.

**Core Philosophy**: Radical simplicity - two tools (`execute_method` and `batch_execute`) provide complete Odoo API access rather than dozens of specialized tools.

## Architecture

### Two-Layer Design

**1. MCP Server Layer** (`src/odoo_mcp/server.py`)
- Built on FastMCP 2.12+ (MCP 2025 spec)
- 2 universal tools: `execute_method`, `batch_execute`
- 10+ MCP resources for discovery (models, schemas, workflows)
- 3 user-facing prompts
- Smart limits: DEFAULT_LIMIT=100, MAX_LIMIT=1000 records

**2. Odoo Client Layer** (`src/odoo_mcp/odoo_client.py`)
- Supports JSON-2 API (Odoo 19+) and JSON-RPC (legacy)
- Bearer token authentication with automatic refresh
- Singleton pattern via `get_odoo_client()`
- HTTP proxy support, configurable SSL verification

### Key Design Decisions

**Why only 2 tools?**
- `execute_method`: Call ANY Odoo method on ANY model
- `batch_execute`: Execute multiple operations atomically
- Specialized tools were removed in v1.0 (redundant/broken)
- Focus on documentation (COOKBOOK.md) over tool proliferation

**Smart Limits System**:
- Prevents accidentally returning GBs of data (e.g., all mail.message records)
- Auto-applies DEFAULT_LIMIT=100 if user doesn't specify
- Caps at MAX_LIMIT=1000 (user can override with pagination)
- Warns for unlimited queries (limit=0 or limit=false)

## Development Commands

### Setup & Running

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run STDIO transport (Claude Desktop)
python run_server.py           # Enhanced logging to ./logs/
python -m odoo_mcp             # Standard entry point
uvx --from . odoo-mcp          # Zero-install runner

# Run SSE transport (web browsers)
python run_server_sse.py       # Port 8009

# Run HTTP transport (API integrations)
python run_server_http.py      # Port 8008
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type checking
mypy src/

# Run all checks before committing
black . && isort . && ruff check . && mypy src/
```

### Building & Publishing

```bash
# Build package
python -m build

# Publish to PyPI
twine upload dist/*

# Build Docker images
docker build -t mcp/odoo:latest -f Dockerfile .
docker build -t mcp/odoo:sse -f Dockerfile.sse .
docker build -t mcp/odoo:http -f Dockerfile.http .
```

## Configuration

### Environment Variables

**Required:**
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password-or-api-key
```

**Optional:**
```bash
ODOO_API_VERSION=json-rpc        # "json-rpc" (default, Odoo 14-18) or "json-2" (Odoo 19+ only)
ODOO_API_KEY=your_api_key        # For JSON-2 API only; on Odoo 18 put the API key in ODOO_PASSWORD instead
ODOO_TIMEOUT=30                  # Connection timeout (default: 30s)
ODOO_VERIFY_SSL=true             # SSL verification (default: true)
HTTP_PROXY=http://proxy.com      # HTTP proxy for Odoo connection
```

### Configuration Files

1. `.env` - Environment variables (preferred)
2. `./odoo_config.json` - JSON config file
3. `~/.config/odoo/config.json` - User config

## Package Structure

```
mcp-odoo-adv/
├── src/odoo_mcp/
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # STDIO entry point (odoo-mcp command)
│   ├── server.py                # MCP server (1000+ lines)
│   │   ├── Tools: execute_method, batch_execute
│   │   ├── Resources: discovery resources + cookbook
│   │   ├── Prompts: user-facing templates
│   │   └── Composes the domain/limits/cookbook modules below
│   ├── odoo_client.py           # Odoo API client (JSON-RPC + JSON-2)
│   ├── domain.py                # Search-domain normalization (pure)
│   ├── limits.py                # Smart-limit policy (pure, no logging)
│   ├── cookbook.py              # Read/write COOKBOOK Learned Patterns
│   ├── logging_util.py          # Shared logging helpers for runners
│   └── runners/                 # Transport runners (one main() each)
│       ├── __init__.py
│       ├── http.py              # Streamable HTTP, 127.0.0.1:8008, NO auth
│       ├── http_secure.py       # Streamable HTTP + Bearer token auth
│       └── sse.py               # SSE, 127.0.0.1:8009, NO auth
├── .claude/skills/              # 8 Claude Code skills covering the cookbook
├── pyproject.toml               # Package config (setuptools, Python 3.10+)
├── fastmcp.json                 # MCP metadata
├── Dockerfile                   # STDIO image
├── Dockerfile.http              # HTTP image
├── Dockerfile.sse               # SSE image
├── docker-compose.yml           # Local compose stack
├── docker-compose.prod.yml      # Production compose stack
├── nginx.conf.example           # Reverse-proxy sample
├── .env.example                 # Environment template
├── odoo_config.json.example     # JSON config template
├── README.md                    # User documentation
├── AGENTS.md                    # Agent-facing repo guide
├── COOKBOOK.md                  # Usage examples + Learned Patterns
├── USER_GUIDE.md                # Setup guide
├── CHANGELOG.md                 # Version history
├── SECURITY.md                  # Security policy
├── LICENSE                      # GPL-3.0-or-later
├── NOTICE                       # Attribution
└── DOCS/
    ├── CLAUDE.md                # Detailed technical reference (900+ lines)
    ├── TRANSPORTS.md            # Transport details
    ├── DOCKER.md                # Docker deployment
    ├── SECURITY.md              # Security hardening guide
    └── STREAMINGHTTP_GUIDE.md   # Streamable HTTP guide
```

**Console scripts** (declared in `pyproject.toml`, no top-level `run_server*.py`):

| Command | Target | Transport |
|---------|--------|-----------|
| `odoo-mcp` | `odoo_mcp.__main__:main` | STDIO |
| `odoo-mcp-http` | `odoo_mcp.runners.http:main` | Streamable HTTP (no auth) |
| `odoo-mcp-http-secure` | `odoo_mcp.runners.http_secure:main` | Streamable HTTP + Bearer |
| `odoo-mcp-sse` | `odoo_mcp.runners.sse:main` | SSE (no auth) |

## Common Development Tasks

### Adding a New MCP Resource

1. Add resource decorator in `src/odoo_mcp/server.py`:
```python
@mcp.resource(
    "odoo://your-resource/{param}",
    description="Resource description",
    annotations={"audience": ["assistant"], "priority": 0.8}
)
def get_your_resource(param: str) -> str:
    """Docstring"""
    odoo_client = get_odoo_client()
    # Implementation
    return json.dumps(result, indent=2)
```

2. Document in README.md and DOCS/CLAUDE.md
3. Add example to COOKBOOK.md if user-facing

### Modifying Smart Limits

Edit constants in `src/odoo_mcp/server.py:800-802`:
```python
DEFAULT_LIMIT = 100  # Auto-applied if not specified
MAX_LIMIT = 1000     # Hard cap on user requests
```

Logic is in `execute_method` tool (lines 800-930).

### Supporting a New Odoo API Version

1. Update `src/odoo_mcp/odoo_client.py:_execute()` method
2. Add authentication logic in `__init__()` or `_connect()`
3. Update environment variable handling in `get_odoo_client()`
4. Document in README.md under "Advanced Usage"

### Adding a New Transport

1. Create `run_server_[transport].py` based on existing patterns
2. Create corresponding `Dockerfile.[transport]`
3. Update DOCS/TRANSPORTS.md with usage
4. Add to README.md Quick Start section

## Testing & Debugging

### Manual Testing

```bash
# Test with real Odoo instance (requires .env configuration)
python test_transports_real.py

# Test smart limits system
python test_limits.py
```

### Debugging Tips

**View logs:**
```bash
# Real-time log monitoring
tail -f logs/mcp_server_*.log

# Search for errors
grep -i error logs/mcp_server_*.log

# View authentication details
python -m odoo_mcp 2>&1 | grep -i auth
```

**Common Issues:**

1. **Authentication failures**: Check ODOO_URL includes `https://`, verify credentials
2. **Connection timeouts**: Increase ODOO_TIMEOUT environment variable
3. **SSL errors**: Set ODOO_VERIFY_SSL=false (not recommended for production)
4. **Smart limits blocking queries**: Override with explicit limit in kwargs_json

## Critical Implementation Details

### Domain Normalization (server.py:806-905)

`execute_method` automatically normalizes search domains to handle multiple input formats:

```python
# Supported formats:
[["field", "=", "value"]]              # Odoo native
{"conditions": [{...}]}                # Object format
'[["field", "=", "value"]]'           # JSON string
["field", "=", "value"]                # Single condition (auto-wrapped)
```

Process: unwraps nested domains → converts objects → parses JSON → validates → preserves logic operators

### Smart Limits Logic (server.py:800-930)

Applied to `search`, `search_read`, `search_count` methods:

1. Check if user provided `limit` in kwargs
2. If not: apply DEFAULT_LIMIT=100
3. If yes but > MAX_LIMIT: cap at 1000, log warning
4. If limit=0 or false: allow but log warning about massive datasets
5. Log if result ≥ MAX_LIMIT

### Authentication Flow

**JSON-2 API (Odoo 19+)**:
- Bearer token in Authorization header
- Database name in X-Odoo-Database header
- Automatic token refresh via session cookies

**JSON-RPC (legacy)**:
- Initial authenticate call to get UID
- UID + password sent with every request
- Deprecated in Odoo 20 (fall 2026)

## Important Patterns

### Reading Odoo API Results

Always check `success` field before accessing `result`:

```python
response = execute_method(model="res.partner", method="search_read", ...)

if not response['success']:
    print(f"Error: {response['error']}")
else:
    records = response['result']
    # Process records
```

### Efficient Querying

```python
# ✅ Good: Specify fields + filter + limit
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[["model", "=", "crm.lead"], ["date", ">=", "2025-01-01"]]]',
    kwargs_json='{"fields": ["date", "subject", "author_id"], "limit": 100}'
)

# ❌ Bad: No filters or field selection (returns ALL fields for ALL records)
execute_method(model="mail.message", method="search_read")
```

### Pagination Pattern

```python
# Count first
count = execute_method(model="your.model", method="search_count", args_json='[[...]]')
total = count['result']

# Then paginate
for page in range((total // 100) + 1):
    execute_method(
        model="your.model",
        method="search_read",
        args_json='[[...]]',
        kwargs_json=f'{{"limit": 100, "offset": {page * 100}}}'
    )
```

## Version Compatibility

- **Python**: 3.10+ (configured in pyproject.toml)
- **FastMCP**: 2.12+ (MCP 2025-06-18 spec)
- **Odoo**: 14+ (JSON-2 API requires 19+)
- **MCP Protocol**: 2025-06-18 specification

## References

- **Detailed Technical Docs**: `DOCS/CLAUDE.md` (850+ lines with complete API reference)
- **Usage Examples**: `COOKBOOK.md` (40+ practical examples)
- **Setup Guide**: `USER_GUIDE.md` (step-by-step installation)
- **Transport Options**: `DOCS/TRANSPORTS.md` (STDIO, SSE, HTTP details)
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **FastMCP Framework**: https://gofastmcp.com
- **Odoo API Docs**: https://www.odoo.com/documentation/

## Notes for Claude Code

- This project emphasizes **simplicity over features** - resist adding specialized tools
- **COOKBOOK.md is the main documentation** - add examples there, not new tools
- Smart limits are intentionally restrictive - document pagination patterns instead
- All Odoo errors are passed through directly - they're excellent and self-explanatory
- Use `context7` MCP tool to verify latest Odoo API changes before modifying client code
- Never add `Claude Code` attribution to commit messages (per user configuration)

## Self-Learning System (IMPORTANT)

**COOKBOOK.md contains a "Learned Patterns" section that grows from experience.**

**Your workflow when using MCP-Odoo tools:**

1. **First attempt**: Use `execute_method` or `batch_execute` directly
2. **After 1st failure**: Read COOKBOOK.md's **Learned Patterns section**
   - Check if similar problem already documented
   - Apply the working pattern if found
   - Continue trying if not found
3. **After 4+ failures**: Automatically document the new pattern
   - Add complete entry to Learned Patterns section
   - Include all failed attempts with reasons
   - Document the working solution
   - Explain why it works
   - Announce: "✅ New pattern documented: [brief explanation]"

**This mimics human behavior**: Try first, check manual after failure, document hard-won solutions.

**Key points:**
- Check COOKBOOK after 1 failure (like checking a user guide)
- Document after ≥4 failures (significant trial-and-error)
- No manual prompting needed - you detect and document automatically
- Each pattern becomes institutional knowledge
