# Odoo MCP Server Advanced

An advanced MCP (Model Context Protocol) server implementation for Odoo ERP systems, enabling AI assistants to interact with Odoo data and functionality through the standardized Model Context Protocol.

**Forked from [tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)** - Thanks to Lê Anh Tuấn for the excellent foundation.

This advanced version includes enhanced features, improved performance, and follows the latest MCP 2025-06-18 specification.

## What's New in v0.0.5 (Unreleased)

### 🧠 Self-Aware Capabilities Discovery
The MCP server now intelligently discovers and exposes what it can do:
- **Enhanced Schema Resources**: Complete model schemas with relationships, constraints, and field categorization
- **Access Rights Discovery**: Real-time permission checking per model and operation
- **Business Workflow Mapping**: Automatic workflow detection based on installed Odoo modules
- **Smart Fallback Teaching**: Resources explicitly teach LLMs when to use `execute_method` as universal tool

### 🔧 New Powerful Tools
- **`validate_before_execute`**: Pre-flight safety checks (permissions, required fields, types)
- **`deep_read`**: Intelligent relationship following - fetch records with related data in one call
- **`batch_execute`**: Atomic multi-operation transactions with rollback support

### 💬 MCP Prompts (User Templates)
User-selectable prompt templates appear in Claude's prompt menu:
- **`search-customers`**: Customer search with location filters
- **`create-sales-order`**: Step-by-step sales order creation guide
- **`odoo-exploration`**: Systematic instance capability discovery
- **`troubleshoot-operation`**: Debug failed operations systematically

### 🚀 Future-Proof API Support
- **JSON-2 API Ready**: Support for Odoo 19+ JSON-2 API with Bearer token authentication
- **Migration Path**: Smooth transition from JSON-RPC (deprecated in Odoo 20, fall 2026)
- **Dual API Support**: Both `json-rpc` and `json-2` work simultaneously
- **Environment Variables**: `ODOO_API_VERSION`, `ODOO_API_KEY`

### 📊 Enhanced Resources
- **`odoo://model/{model}/schema`**: Complete schema (fields, relationships, required/readonly/computed)
- **`odoo://model/{model}/access`**: User permissions (read, write, create, unlink)
- **`odoo://workflows`**: Business workflows for Sales, CRM, Inventory, HR, Accounting, Projects
- **`odoo://methods/{model}`**: Now explicitly teaches `execute_method` as universal fallback

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

### Core Tools

* **execute_method** ⚡ UNIVERSAL TOOL
  * Execute ANY Odoo method on ANY model - your fallback for everything
  * **Use this when**: No specialized tool exists for what you need
  * Inputs:
    * `model` (string): The model name (e.g., 'res.partner', 'sale.order', 'crm.lead')
    * `method` (string): Method name (e.g., 'create', 'search_read', 'write', 'action_confirm')
    * `args_json` (string): JSON string of positional arguments
    * `kwargs_json` (string): JSON string of keyword arguments
  * Returns: `{success, result, error}`
  * Examples:
    * Create customer: `execute_method(model='res.partner', method='create', args_json='[{"name": "Acme Corp"}]')`
    * Search: `execute_method(model='res.partner', method='search_read', args_json='[[["customer_rank", ">", 0]]]')`
    * Update: `execute_method(model='res.partner', method='write', args_json='[[1], {"phone": "+123"}]')`

### Advanced Tools

* **validate_before_execute**
  * Pre-flight safety check before operations
  * Validates: Model exists, permissions, required fields, field types
  * Inputs: `model`, `method`, `args_json`, `kwargs_json` (same as execute_method)
  * Returns: `{valid, errors[], warnings[], suggestions[], safe_to_execute}`
  * **Best Practice**: Always validate before `create` or `write` operations

* **deep_read**
  * Fetch record with related data in one intelligent query
  * Auto-follows relationships (many2one, one2many, many2many)
  * Inputs:
    * `model` (string): Model name
    * `record_id` (int): Record ID to fetch
    * `follow_relations` (optional array): Specific fields to follow (default: all many2one)
    * `depth` (int): How deep to follow (1 = direct, 2 = relations of relations)
  * Returns: `{success, record, related_records{}, error}`
  * Example: Get sales order with customer + lines + products in one call

* **batch_execute**
  * Execute multiple operations in atomic transaction
  * All succeed or all rollback (when atomic=true)
  * Inputs:
    * `operations` (array): List of {model, method, args_json, kwargs_json}
    * `atomic` (bool): Transaction mode (default: true)
  * Returns: `{success, results[], total_operations, successful_operations, failed_operations}`
  * Example: Create customer + create order in one transaction

### Domain-Specific Tools

* **search_employee**
  * Search for employees by name (convenience wrapper)
  * Inputs: `name` (string), `limit` (int, default: 20)
  * Returns: `{success, result[], error}`

* **search_holidays**
  * Search holidays within date range (convenience wrapper)
  * Inputs: `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `employee_id` (optional int)
  * Returns: `{success, result[], error}`

## Resources

MCP resources provide URI-based discovery and context. The LLM reads these to understand capabilities.

### Discovery Resources

* **odoo://models**
  * Lists all available models in the Odoo system
  * Priority: 0.9 (high - essential for discovery)
  * Returns: `{model_names[], models_details{}}`

* **odoo://server/info**
  * Server metadata: version, database, installed modules
  * Priority: 0.5
  * Returns: `{database, odoo_version, installed_modules_count, installed_modules[]}`

* **odoo://workflows**
  * Business workflows based on installed modules
  * Priority: 0.8
  * Auto-detects: Sales, CRM, Inventory, HR, Accounting, Projects
  * Returns: `{installed_modules[], available_workflows{sales, crm, inventory, hr, accounting, projects}}`
  * Each workflow includes: steps, models, method names

### Schema Resources (Parameterized)

* **odoo://model/{model_name}/schema** 🆕
  * Complete schema with relationships and categorization
  * Priority: 0.85
  * Example: `odoo://model/sale.order/schema`
  * Returns: `{model, fields{}, relationships{}, required_fields[], readonly_fields[], computed_fields[]}`

* **odoo://model/{model_name}/access** 🆕
  * User permissions for current user
  * Priority: 0.7
  * Returns: `{model, access_rights{read, write, create, unlink}}`
  * Note: Model-level permissions; record rules may further restrict

* **odoo://fields/{model_name}**
  * Field definitions (lighter than full schema)
  * Priority: 0.75
  * Example: `odoo://fields/sale.order`
  * Returns: Field definitions dictionary

* **odoo://methods/{model_name}**
  * Available ORM methods with execute_method examples
  * Priority: 0.7
  * **Explicitly teaches** using `execute_method` as fallback
  * Returns: `{read_methods[], write_methods[], universal_tool{}, example{}}`

* **odoo://model/{model_name}**
  * Basic model info with fields
  * Priority: 0.8
  * Returns: Model metadata + field definitions

* **odoo://record/{model_name}/{record_id}**
  * Specific record by ID
  * Priority: 0.7
  * Example: `odoo://record/res.partner/1`

* **odoo://search/{model_name}/{domain}**
  * Search records matching domain
  * Priority: 0.6
  * Example: `odoo://search/res.partner/[["customer_rank",">",0]]`
  * Returns: Up to 10 matching records

## Prompts

User-selectable templates that appear in Claude's prompt menu:

* **search-customers** - Customer search with city/country filters
* **create-sales-order** - Step-by-step sales order creation guide
* **odoo-exploration** - Systematic capability discovery for new instances
* **troubleshoot-operation** - Debug failed operations with systematic checks

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
   * `ODOO_PASSWORD`: Password (for JSON-RPC, deprecated in Odoo 20)
   * `ODOO_API_KEY`: API key for JSON-2 API (Odoo 19+, recommended)
   * `ODOO_API_VERSION`: `json-rpc` (default) or `json-2` (Odoo 19+)
   * `ODOO_TIMEOUT`: Connection timeout in seconds (default: 30)
   * `ODOO_VERIFY_SSL`: Whether to verify SSL certificates (default: true)
   * `HTTP_PROXY`: Force the ODOO connection to use an HTTP proxy

### Odoo 19+ JSON-2 API (Recommended)

For better security with Odoo 19+, use API key authentication:

```bash
export ODOO_API_VERSION=json-2
export ODOO_API_KEY=your_api_key_here  # Generate in Odoo user preferences
```

The JSON-2 API offers:
- Bearer token authentication (more secure)
- Better performance
- Forward compatibility (JSON-RPC deprecated in Odoo 20)

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

### Completed in v0.0.5 ✅
- [x] **Self-Aware Capabilities**: Schema, access, workflow resources
- [x] **Advanced Tools**: validate_before_execute, deep_read, batch_execute
- [x] **MCP Prompts**: User-selectable workflow templates
- [x] **JSON-2 API Support**: Future-proof for Odoo 19+
- [x] **Multiple Transports**: STDIO, SSE, and Streamable HTTP support
- [x] **JSON-RPC Support**: ~75% faster than XML-RPC (617 vs 353 req/sec)

### High Priority
- [ ] **Context Logging**: Structured logging for AI debugging (ctx.info, ctx.debug)
- [ ] **Progress Reporting**: Real-time progress for long operations
- [ ] **Error Codes**: Actionable error codes for better AI responses

### Quality Improvements
- [ ] **Input Validation**: Enhanced systematic validation
- [ ] **Better Documentation**: More usage examples
- [ ] **Comprehensive Test Suite**: Unit and integration tests
- [ ] **Performance Benchmarks**: Tool execution profiling

### Advanced Features
- [ ] **Resource Subscriptions**: Real-time update notifications
- [ ] **Rate Limiting**: Production safety and abuse prevention
- [ ] **Health Check Tool**: Monitoring and deployment support
- [ ] **Caching Layer**: Resource caching for performance
- [ ] **Bulk Import/Export**: CSV/Excel data tools

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
