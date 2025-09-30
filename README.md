# Odoo MCP Server Advanced

An advanced MCP (Model Context Protocol) server implementation for Odoo ERP systems, enabling AI assistants to interact with Odoo data and functionality through the standardized Model Context Protocol.

**Forked from [tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)** - Thanks to Lê Anh Tuấn for the excellent foundation.

This advanced version includes enhanced features, improved performance, and follows the latest MCP 2025-06-18 specification.

## Features

* **Comprehensive Odoo Integration**: Full access to Odoo models, records, and methods
* **XML-RPC Communication**: Secure connection to Odoo instances via XML-RPC (JSON-RPC support planned)
* **Flexible Configuration**: Support for config files and environment variables
* **Resource Pattern System**: URI-based access to Odoo data structures
* **Enhanced Error Handling**: Clear error messages with detailed logging
* **Stateless Operations**: Clean request/response cycle for reliable integration
* **MCP 2025 Compliant**: Implements latest Model Context Protocol specification (2025-06-18)
* **Advanced Domain Normalization**: Supports multiple domain input formats for flexible querying
* **Custom Transport**: HTTP proxy support, SSL verification control, automatic redirects
* **Production Ready**: Enhanced logging, timeout configuration, and error recovery

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

* **odoo://models**
  * Lists all available models in the Odoo system
  * Returns: JSON array of model information

* **odoo://model/{model_name}**
  * Get information about a specific model including fields
  * Example: `odoo://model/res.partner`
  * Returns: JSON object with model metadata and field definitions

* **odoo://record/{model_name}/{record_id}**
  * Get a specific record by ID
  * Example: `odoo://record/res.partner/1`
  * Returns: JSON object with record data

* **odoo://search/{model_name}/{domain}**
  * Search for records that match a domain
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

## Installation Methods

### 1. From Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/AlanOgic/mcp-odoo-adv.git
cd mcp-odoo-adv

# Install with dev dependencies
pip install -e ".[dev]"

# Run the server
odoo-mcp
```

### 2. Docker Build and Run

```bash
# Build the Docker image
docker build -t alanogic/mcp-odoo-adv:latest -f Dockerfile .

# Run the container
docker run -i --rm \
  -e ODOO_URL=https://your-instance.odoo.com \
  -e ODOO_DB=your-database \
  -e ODOO_USERNAME=your-username \
  -e ODOO_PASSWORD=your-password \
  alanogic/mcp-odoo-adv:latest
```

### 3. Running the Server

```bash
# Using the installed package
odoo-mcp

# With enhanced logging (logs to ./logs/)
python run_server.py

# Using MCP development tools
mcp dev src/odoo_mcp/server.py
```



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

## Roadmap

See our planned improvements in the [dev branch](https://github.com/AlanOgic/mcp-odoo-adv/tree/dev):

- [ ] JSON-RPC support (30-40% faster than XML-RPC)
- [ ] MCP resource annotations (audience, priority, lastModified)
- [ ] Resource templates for dynamic queries
- [ ] Batch operations tool
- [ ] Output schemas for better type safety
- [ ] Comprehensive test suite
- [ ] Caching layer for performance
- [ ] Rate limiting and security enhancements

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
