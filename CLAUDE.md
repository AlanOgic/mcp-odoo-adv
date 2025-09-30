# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation
```bash
# Install from PyPI
pip install odoo-mcp

# Install from source with dev dependencies
pip install -e ".[dev]"

# Build Docker image
docker build -t mcp/odoo:latest -f Dockerfile .
```

### Running the Server
```bash
# Run as installed package (uses __main__.py entry point)
odoo-mcp

# Run with MCP development tools
mcp dev src/odoo_mcp/server.py

# Run standalone script (with logging to ./logs/)
python run_server.py

# Docker run
docker run -i --rm -e ODOO_URL -e ODOO_DB -e ODOO_USERNAME -e ODOO_PASSWORD mcp/odoo
```

### Debugging
```bash
# The run_server.py script provides enhanced logging to ./logs/ with timestamps
# Check logs for connection issues and domain normalization details
python run_server.py

# View real-time logs
tail -f logs/mcp_server_*.log

# Environment diagnostics printed to stderr on startup
# Check ODOO_* environment variables and connection details
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

# Build package
python -m build

# Publish (requires PyPI credentials)
twine upload dist/*
```

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides AI assistants with access to Odoo ERP systems via XML-RPC.

### Three-Layer Architecture

**1. MCP Server Layer** (`src/odoo_mcp/server.py`)
- Built on FastMCP framework
- Implements MCP resources (URI-based data access) and tools (RPC methods)
- Uses `AppContext` dataclass to inject OdooClient into request context
- Pydantic models for type-safe tool inputs/outputs
- Entry points:
  - `__main__.py`: Standard entry point using `mcp.run()`
  - `run_server.py`: Standalone script with enhanced logging to `./logs/`

**2. Odoo Client Layer** (`src/odoo_mcp/odoo_client.py`)
- `OdooClient`: XML-RPC client with authentication and method execution
  - Connection initialization and authentication in `_connect()` method
  - Generic `execute_method()` wrapper for all Odoo RPC calls
  - Specialized methods: `get_models()`, `get_model_info()`, `get_model_fields()`, `search_read()`, `read_records()`
- `RedirectTransport`: Custom transport supporting timeouts, SSL verification, HTTP proxies, and redirect following
  - Default timeout increased from 10s to 30s (configurable via `ODOO_TIMEOUT`)
  - Automatic redirect following (max 5 redirects)
  - HTTP proxy support via `HTTP_PROXY` environment variable or constructor parameter
- `load_config()`: Loads credentials from environment variables or config files
- Singleton pattern via `get_odoo_client()` ensures single connection per process

**3. Configuration System**
- Priority: Environment variables > config file
- Config file locations (in order): `./odoo_config.json`, `~/.config/odoo/config.json`, `~/.odoo_config.json`
- Configuration options:
  - Required: `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`
  - Optional: `ODOO_TIMEOUT` (default: 30), `ODOO_VERIFY_SSL` (default: true), `HTTP_PROXY`

### MCP Resources (URI-based)

- `odoo://models` - List all available Odoo models
- `odoo://model/{model_name}` - Get model metadata and field definitions
- `odoo://record/{model_name}/{record_id}` - Retrieve specific record by ID
- `odoo://search/{model_name}/{domain}` - Search records with domain (limit=10)

### MCP Tools (RPC methods)

**execute_method** - General-purpose method executor with complex domain normalization
- Accepts args (list) and kwargs (dict)
- Special handling for search methods (`search`, `search_count`, `search_read`)
- Normalizes domain parameters from multiple formats (list, object, JSON string)

**search_employee** - Convenience wrapper for `hr.employee.name_search`

**search_holidays** - Date range query for `hr.leave.report.calendar` with timezone adjustments

## Domain Parameter Handling

The `execute_method` tool includes sophisticated domain normalization logic (lines 242-340 in server.py) to handle multiple input formats:

### Supported Domain Formats

1. **List format**: `[["field", "operator", value], ...]`
2. **Object format**: `{"conditions": [{"field": "...", "operator": "...", "value": "..."}]}`
3. **JSON string**: String representation of either format above
4. **Single condition**: `["field", "operator", value]` (auto-wrapped)

### Normalization Process

- Unwraps unnecessarily nested domains (`[[domain]]` → `[domain]`)
- Converts object format to list format
- Parses JSON strings with fallback to `ast.literal_eval`
- Validates conditions (must be 3-element lists or operators `&`, `|`, `!`)
- Preserves complex domain logic operators

## Configuration

### Required Environment Variables
```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password-or-api-key
```

### Optional Environment Variables
```bash
ODOO_TIMEOUT=30  # Connection timeout in seconds (default: 30)
ODOO_VERIFY_SSL=true  # Whether to verify SSL certificates (default: true)
HTTP_PROXY=http://proxy:8080  # Force HTTP proxy for Odoo connection
```

### Claude Desktop Configuration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password-or-api-key"
      }
    }
  }
}
```

## Technical Details

### Custom Transport Features (`RedirectTransport`)
- Configurable timeouts (default 30s, previously 10s)
- SSL certificate verification toggle
- HTTP proxy support via `HTTP_PROXY` environment variable
- Automatic redirect following (max 5 redirects)
- Detailed logging to stderr for debugging connection issues

### Stateless Design
- Each request creates a fresh operation context
- No persistent state between requests
- Clean request/response cycle for reliability
- Singleton `OdooClient` instance shared across all requests via `get_odoo_client()`

### Error Handling Strategy
- Connection errors raise `ConnectionError` with descriptive messages
- Authentication failures raise `ValueError` with clear error context
- All errors logged to stderr for debugging
- Detailed diagnostics on startup (environment variables, connection details)

### Python Version
Requires Python ≥3.10 (configured in pyproject.toml)

### Dependencies
- `mcp>=0.1.1` - Model Context Protocol framework
- `requests>=2.31.0` - HTTP library
- `pypi-xmlrpc==2020.12.3` - XML-RPC protocol support

### Package Structure
```
src/odoo_mcp/
  ├── __init__.py          # Package initialization
  ├── __main__.py          # CLI entry point (odoo-mcp command)
  ├── server.py            # MCP server with resources and tools
  └── odoo_client.py       # Odoo XML-RPC client and transport
run_server.py              # Standalone runner with enhanced logging
Dockerfile                 # Container build with Python 3.10-slim
```

### Development Notes
- No test suite currently exists (opportunity for improvement)
- Code quality enforced via black, isort, ruff, and mypy
- Logging handled differently between entry points:
  - `__main__.py`: Logs to stderr only
  - `run_server.py`: Logs to both stderr and timestamped files in `./logs/`
- Domain normalization logging appears in stderr for debugging (server.py:343)