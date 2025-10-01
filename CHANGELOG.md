# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Multiple Transport Support**: SSE and Streamable HTTP transports for web and API clients
  - `run_server_sse.py`: SSE transport entry point with enhanced logging
  - `run_server_http.py`: Streamable HTTP transport entry point
  - `Dockerfile.sse`: Docker build for SSE transport
  - `Dockerfile.http`: Docker build for Streamable HTTP transport
  - `TRANSPORTS.md`: Comprehensive 350+ line transport documentation with examples
  - Environment variables: `MCP_HOST`, `MCP_PORT`, `MCP_SSE_PATH`, `MCP_HTTP_PATH`
- **Documentation Enhancements**
  - Updated README.md with v0.0.5 features and Quick Start section
  - Updated CLAUDE.md with transport-specific running instructions (streamlined to 228 lines)
  - Added transport comparison table and deployment guides

### Changed
- **CLAUDE.md Streamlined**: Reduced from 410 to 228 lines (~45% reduction)
  - Consolidated Quick Start section with all transport options
  - Emphasized critical patterns with line references
  - Removed verbose troubleshooting in favor of TRANSPORTS.md
- **README.md Enhanced**: Added What's New section, transport quick start, documentation links
- **.gitignore**: Added patterns for `.env.*`, `!.env.example`, `.dockerignore`

## [0.0.4] - 2025-10-01

### Added
- **MCP 2025 Specification Compliance**
  - Upgraded from legacy MCP SDK to FastMCP 2.12+ framework
  - Output schemas for all tools using Pydantic models:
    - `ExecuteMethodResponse`: Type-safe execute_method responses
    - `SearchEmployeeResponse`: Typed employee search results
    - `SearchHolidaysResponse`: Typed holiday search results
  - Resource annotations with audience and priority metadata for AI optimization
  - `fastmcp.json` configuration (replaces deprecated dependencies parameter)
- **Enhanced Resource System**
  - `odoo://fields/{model_name}`: Lightweight field definitions lookup
  - `odoo://methods/{model_name}`: Method catalog with usage examples
  - `odoo://server/info`: Odoo version and installed modules metadata
  - All resources include priority scores for better AI context
- **Python Ecosystem Improvements**
  - Extended support from Python 3.10-3.11 to Python 3.10-3.13
  - Docker builds support configurable Python version via `ARG PYTHON_VERSION`
  - Optimized Dockerfile with layer caching (pyproject.toml → dependencies → source code)
- **Documentation**
  - Comprehensive CLAUDE.md for development guidance
  - Enhanced logging with timestamps to ./logs/ directory

### Changed
- **JSON-RPC Migration**: Migrated from XML-RPC to JSON-RPC 1.x for performance
  - ~75% performance improvement (617 req/sec vs 353 req/sec)
  - Native JSON-RPC implementation using `requests` library
  - Connection pooling and keep-alive via `requests.Session`
  - Better MCP compatibility (MCP uses JSON-RPC 2.0 natively)
  - Default timeout: 30s (configurable via `ODOO_TIMEOUT`)
  - HTTP proxy support via `HTTP_PROXY` environment variable
  - SSL verification toggle via `ODOO_VERIFY_SSL`
- **Transport Layer Enhancements**
  - Custom `OdooClient._jsonrpc_call()` method for JSON-RPC 1.x protocol
  - Replaced XML-RPC endpoints with `/jsonrpc` endpoint
  - Detailed connection logging to stderr for debugging

### Fixed
- **execute_method Claude Desktop Bug Workaround**
  - Changed `args` and `kwargs` parameters to `args_json` and `kwargs_json` (JSON strings)
  - Works around Claude Desktop's MCP parameter serialization issue
  - Parses JSON strings internally to execute Odoo methods correctly
  - Maintains sophisticated domain normalization for search methods

### Research & Understanding
- Analyzed production MCP servers (ivnvxd/mcp-server-odoo, hachecito/odoo-mcp-improved)
- Studied MCP 2025-06-18 specification for output schemas and annotations
- Documented FastMCP 2.12+ patterns and AppContext injection
- Researched Odoo API evolution: XML-RPC → JSON-RPC → JSON-2 (Odoo 19+)
- Confirmed Odoo 18 compatibility with JSON-RPC 1.x
- Benchmarked JSON-RPC performance vs XML-RPC

## [0.0.3] - 2025-03-18

### Fixed
- Fixed `OdooClient` class by adding missing methods: `get_models()`, `get_model_info()`, `get_model_fields()`, `search_read()`, and `read_records()`
- Ensured compatibility with different Odoo versions by using only basic fields when retrieving model information

### Added
- Support for retrieving all models from an Odoo instance
- Support for retrieving detailed information about specific models
- Support for searching and reading records with various filtering options

## [0.0.2] - 2025-03-18

### Fixed
- Added missing dependencies in pyproject.toml: `mcp>=0.1.1`, `requests>=2.31.0`, `xmlrpc>=0.4.1`

## [0.0.1] - 2025-03-18

### Added
- Initial release with basic Odoo XML-RPC client support
- MCP Server integration for Odoo
- Command-line interface for quick setup and testing 