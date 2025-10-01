# Odoo MCP Server Advanced

An advanced MCP (Model Context Protocol) server implementation for Odoo ERP systems, enabling AI assistants to interact with Odoo data and functionality through the standardized Model Context Protocol.

**Forked from [tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)** - Thanks to Lê Anh Tuấn for the excellent foundation.

This advanced version includes enhanced features, improved performance, and follows the latest MCP 2025-06-18 specification.

## What's New in v0.0.5 (Unreleased)

### Multiple Transport Support 🚀
- **SSE Transport**: Server-Sent Events for web browsers and HTTP clients
- **Streamable HTTP**: Bidirectional streaming for API integrations
- **STDIO Transport**: Default for Claude Desktop (existing)
- Flexible deployment with `run_server_sse.py` and `run_server_http.py`
- Docker images for each transport: `alanogic/mcp-odoo-adv:sse`, `alanogic/mcp-odoo-adv:http`
- Environment variables: `MCP_HOST`, `MCP_PORT`, `MCP_SSE_PATH`, `MCP_HTTP_PATH`
- See [TRANSPORTS.md](TRANSPORTS.md) for complete documentation

## Features

### Core Capabilities
* **Multiple Transports**: STDIO, SSE, and Streamable HTTP for different use cases
* **Comprehensive Odoo Integration**: Full access to Odoo models, records, and methods via JSON-RPC
* **MCP 2025 Compliant**: Implements latest Model Context Protocol specification (2025-06-18)
* **FastMCP 2.12+**: Built with latest FastMCP framework for optimal performance
* **Python 3.10-3.13**: Tested and supported on Python 3.10, 3.11, 3.12, and 3.13

### Advanced Features
* **Resource Templates**: Dynamic URI-based access to Odoo data with parameter support
* **Output Schemas**: Type-safe tool responses with Pydantic models
* **Resource Annotations**: Priority, audience, and metadata for better AI understanding
* **Smart Method Discovery**: Built-in method catalog showing available operations per model
* **Advanced Domain Normalization**: Supports multiple domain input formats (list, object, JSON string)
* **Server Metadata Access**: Query Odoo version, installed modules, and configuration

### Production Ready
* **Custom Transport Layer**: HTTP proxy support, SSL verification control, automatic redirects
* **Enhanced Error Handling**: Detailed error messages with context
* **Flexible Configuration**: Environment variables and fastmcp.json configuration
* **Comprehensive Logging**: Enhanced debugging with timestamped log files
* **Stateless Operations**: Clean request/response cycle for reliable integration
* **Timeout Management**: Configurable connection timeouts (default: 30s)

## Tools

* **execute_method**
  * Execute a custom method on an Odoo model
  * Inputs:
    * `model` (string): The model name (e.g., 'res.partner')
    * `method` (string): Method name to execute
    * `args` (optional array): Positional arguments
    * `kwargs` (optional object): Keyword arguments
  * Returns: Dictionary with the method result and success indicator

* **search_employee**
  * Search for employees by name
  * Inputs:
    * `name` (string): The name (or part of the name) to search for
    * `limit` (optional number): The maximum number of results to return (default 20)
  * Returns: Object containing success indicator, list of matching employee names and IDs, and any error message

* **search_holidays**
  * Searches for holidays within a specified date range
  * Inputs:
    * `start_date` (string): Start date in YYYY-MM-DD format
    * `end_date` (string): End date in YYYY-MM-DD format
    * `employee_id` (optional number): Optional employee ID to filter holidays
  * Returns: Object containing success indicator, list of holidays found, and any error message

## Resources

MCP resources provide URI-based access to Odoo data. FastMCP automatically categorizes them into **Resources** (static) and **Resource Templates** (parameterized).

### Static Resources

* **odoo://models**
  * Lists all available models in the Odoo system
  * Priority: 0.9 (high - essential for discovery)
  * Returns: JSON array of model information

* **odoo://server/info**
  * Get Odoo server metadata (version, database, installed modules)
  * Priority: 0.5 (useful for context)
  * Returns: JSON object with server information

### Resource Templates (Parameterized)

* **odoo://model/{model_name}**
  * Get information about a specific model including fields
  * Priority: 0.8
  * Example: `odoo://model/res.partner`
  * Returns: JSON object with model metadata and field definitions

* **odoo://fields/{model_name}**
  * Get just field definitions for a model (lighter than full model info)
  * Priority: 0.75
  * Example: `odoo://fields/sale.order`
  * Returns: JSON object with field definitions

* **odoo://methods/{model_name}**
  * List available Odoo ORM methods with descriptions and parameters
  * Priority: 0.7
  * Includes usage examples for execute_method tool
  * Example: `odoo://methods/res.partner`
  * Returns: JSON object with read/write methods catalog

* **odoo://record/{model_name}/{record_id}**
  * Get a specific record by ID
  * Priority: 0.7
  * Example: `odoo://record/res.partner/1`
  * Returns: JSON object with record data

* **odoo://search/{model_name}/{domain}**
  * Search for records that match a domain
  * Priority: 0.6
  * Example: `odoo://search/res.partner/[["is_company","=",true]]`
  * Returns: JSON array of matching records (limited to 10 by default)

## Configuration

### Odoo Connection Setup

1. Create a configuration file named `odoo_config.json`:

```json
{
  "url": "https://your-odoo-instance.com",
  "db": "your-database-name",
  "username": "your-username",
  "password": "your-password-or-api-key"
}
```

2. Alternatively, use environment variables:
   * `ODOO_URL`: Your Odoo server URL
   * `ODOO_DB`: Database name
   * `ODOO_USERNAME`: Login username
   * `ODOO_PASSWORD`: Password or API key
   * `ODOO_TIMEOUT`: Connection timeout in seconds (default: 30)
   * `ODOO_VERIFY_SSL`: Whether to verify SSL certificates (default: true)
   * `HTTP_PROXY`: Force the ODOO connection to use an HTTP proxy

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp"
      ],
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

### Docker

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "ODOO_URL=https://your-odoo-instance.com",
        "-e",
        "ODOO_DB=your-database-name",
        "-e",
        "ODOO_USERNAME=your-username",
        "-e",
        "ODOO_PASSWORD=your-password-or-api-key",
        "alanogic/mcp-odoo-adv:latest"
      ]
    }
  }
}
```

## Quick Start

### Install from Source
```bash
git clone https://github.com/AlanOgic/mcp-odoo-adv.git
cd mcp-odoo-adv
pip install -e ".[dev]"
```

### Run with STDIO (Claude Desktop)
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your Odoo credentials

# Run server
python run_server.py
```

### Run with SSE (Web Browsers)
```bash
# Run SSE server
python run_server_sse.py

# Access at http://localhost:8000/sse
```

### Run with Streamable HTTP (API)
```bash
# Run HTTP server
python run_server_http.py

# Access at http://localhost:8000/mcp
```

### Docker
```bash
# STDIO transport
docker run -i --rm --env-file .env alanogic/mcp-odoo-adv:latest

# SSE transport
docker run -p 8000:8000 --env-file .env alanogic/mcp-odoo-adv:sse

# HTTP transport
docker run -p 8000:8000 --env-file .env alanogic/mcp-odoo-adv:http
```

## Documentation

- **[TRANSPORTS.md](TRANSPORTS.md)**: Complete transport options guide (STDIO, SSE, HTTP)
- **[CLAUDE.md](CLAUDE.md)**: Development guide for contributors
- **[CHANGELOG.md](CHANGELOG.md)**: Version history and changes



## Parameter Formatting Guidelines

When using the MCP tools for Odoo, pay attention to these parameter formatting guidelines:

1. **Domain Parameter**:
   * The following domain formats are supported:
     * List format: `[["field", "operator", value], ...]`
     * Object format: `{"conditions": [{"field": "...", "operator": "...", "value": "..."}]}`
     * JSON string of either format
   * Examples:
     * List format: `[["is_company", "=", true]]`
     * Object format: `{"conditions": [{"field": "date_order", "operator": ">=", "value": "2025-03-01"}]}`
     * Multiple conditions: `[["date_order", ">=", "2025-03-01"], ["date_order", "<=", "2025-03-31"]]`

2. **Fields Parameter**:
   * Should be an array of field names: `["name", "email", "phone"]`
   * The server will try to parse string inputs as JSON

## What's New in v0.0.4

### MCP 2025 Upgrades ✨
- ✅ **FastMCP 2.12+**: Upgraded from legacy MCP SDK to latest FastMCP framework
- ✅ **Output Schemas**: Type-safe tool responses with Pydantic models
- ✅ **Resource Annotations**: Priority, audience, and metadata for AI optimization
- ✅ **fastmcp.json**: Configuration file for FastMCP 2.12+ (replaces deprecated dependencies param)

### New Resources 🎯
- ✅ **odoo://fields/{model_name}**: Quick field definitions lookup
- ✅ **odoo://methods/{model_name}**: Method catalog with usage examples
- ✅ **odoo://server/info**: Server metadata (version, modules, database)

### Python & Compatibility 🐍
- ✅ **Python 3.13 Support**: Full support for Python 3.10-3.13
- ✅ **Docker Python Version**: Configurable via ARG (default: 3.10)

### Developer Experience 🛠️
- ✅ **Enhanced Documentation**: Comprehensive CLAUDE.md for development
- ✅ **Improved Logging**: Timestamped logs in ./logs/ directory
- ✅ **Better Error Messages**: Context-aware error handling

### Research & Understanding 📚
- ✅ **MCP Spec Compliance**: Verified against MCP 2025-06-18 specification
- ✅ **Production Patterns**: Analyzed ivnvxd/mcp-server-odoo and hachecito/odoo-mcp-improved
- ✅ **Resource Templates**: Confirmed FastMCP auto-categorization (Resources vs Templates)

## Roadmap

See our planned improvements in the [dev branch](https://github.com/AlanOgic/mcp-odoo-adv/tree/dev):

### Completed ✅
- [x] **Multiple Transports**: STDIO, SSE, and Streamable HTTP support
- [x] **JSON-RPC Support**: ~75% faster than XML-RPC (617 vs 353 req/sec)

### High Priority
- [ ] **Prompts**: Business workflow templates (sales analysis, inventory check, etc.)
- [ ] **Context Logging**: Structured logging for AI debugging (ctx.info, ctx.debug)
- [ ] **Progress Reporting**: Real-time progress for long operations
- [ ] **Error Codes**: Actionable error codes for better AI responses

### Quality Improvements
- [ ] **Input Validation**: Systematic validation and sanitization
- [ ] **Better Documentation**: Usage examples in all docstrings
- [ ] **Comprehensive Test Suite**: Unit and integration tests

### Advanced Features
- [ ] **Resource Subscriptions**: Real-time update notifications
- [ ] **Rate Limiting**: Production safety and abuse prevention
- [ ] **Health Check Tool**: Monitoring and deployment support
- [ ] **Caching Layer**: Performance optimization
- [ ] **Batch Operations**: Multi-record operations tool

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

For detailed development instructions, see [CLAUDE.md](CLAUDE.md).

## License

This MCP server is licensed under the MIT License.

## Acknowledgments

- Original project by [Lê Anh Tuấn](https://github.com/tuanle96/mcp-odoo)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Follows [Model Context Protocol](https://modelcontextprotocol.io) specification
