# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### 🧠 Self-Aware Capabilities Discovery
- **Enhanced Resource Hierarchy**: New MCP resources for intelligent capability discovery
  - `odoo://model/{model}/schema` - Complete schema with relationships, required/readonly/computed field categorization
  - `odoo://model/{model}/access` - Real-time user permission checking (read, write, create, unlink)
  - `odoo://workflows` - Automatic business workflow detection based on installed Odoo modules (Sales, CRM, Inventory, HR, Accounting, Projects)
- **Smart Fallback Teaching**: Resources explicitly teach LLMs when and how to use `execute_method` as universal tool
- **Enhanced Methods Resource**: `odoo://methods/{model}` now includes explicit guidance on using execute_method

#### 🔧 New Powerful Tools
- **`validate_before_execute`** - Pre-flight safety validation tool
  - Checks: Model exists, user permissions, required fields, field types, constraints
  - Returns: `{valid, errors[], warnings[], suggestions[], safe_to_execute}`
  - Use case: Validate before `create` or `write` operations to catch errors early
- **`deep_read`** - Intelligent relationship navigator
  - Auto-follows many2one, one2many, many2many relationships
  - Configurable depth and field selection
  - Returns: `{success, record, related_records{}, error}`
  - Use case: Get sales order with customer + order lines + products in one call
- **`batch_execute`** - Atomic multi-operation transactions
  - Execute multiple operations in single transaction
  - Atomic mode: all succeed or all rollback
  - Returns: `{success, results[], total_operations, successful_operations, failed_operations}`
  - Use case: Create customer + create order in one transaction

#### 💬 MCP Prompts (User Templates)
User-selectable prompt templates that appear in Claude's prompt menu:
- **`search-customers`** - Customer search template with city/country filters
- **`create-sales-order`** - Step-by-step sales order creation guide with validation
- **`odoo-exploration`** - Systematic capability discovery for new Odoo instances
- **`troubleshoot-operation`** - Debug failed operations with systematic troubleshooting steps

#### 🚀 Future-Proof API Support
- **JSON-2 API Support** - Full support for Odoo 19+ JSON-2 API
  - Bearer token authentication (more secure than password)
  - Better performance
  - Dual API support: both `json-rpc` and `json-2` work simultaneously
  - Environment variables: `ODOO_API_VERSION`, `ODOO_API_KEY`
  - Automatic API selection based on configuration
- **Migration Path** - Smooth transition from JSON-RPC (deprecated in Odoo 20, fall 2026)
- **Updated OdooClient** - Enhanced client class with dual API support

### Changed

#### Enhanced Existing Features
- **`execute_method` Tool** - Enhanced with comprehensive documentation
  - Updated description emphasizes universal fallback capability
  - Added extensive examples for common operations (create, search, update, delete)
  - Pro tips reference schema, methods, and workflow resources
  - Now SCREAMS that it can do anything Odoo can do
- **Resource Descriptions** - All resources updated with better context and examples
- **Tool Output Schemas** - Enhanced Pydantic models for new tools

### Improved

- **MCP Compliance** - Fully aligned with MCP 2025-06-18 specification
  - Proper separation of Resources (context) vs Tools (actions) vs Prompts (templates)
  - Resources teach capabilities, tools perform actions, prompts guide users
- **Developer Experience**
  - All syntax validated (Python 3.10-3.13 compatible)
  - Backward compatible with existing implementations
  - Enhanced inline documentation and type hints
- **Documentation**
  - README.md completely updated with new features
  - Clear examples for all new tools and resources
  - JSON-2 API migration guide
  - Tool usage best practices

### Technical Details

- **New Resource URIs**: 3 new resource patterns for enhanced discovery
- **New Tools**: 3 advanced tools for validation, deep reading, and batch operations
- **New Prompts**: 4 user-selectable templates for common workflows
- **API Versions Supported**: JSON-RPC (current) + JSON-2 (Odoo 19+)
- **Python Compatibility**: 3.10, 3.11, 3.12, 3.13
- **MCP Specification**: 2025-06-18
- **FastMCP Version**: 2.12+

## [0.0.4] - 2025-01-XX

### Added
- **Multiple Transport Support**: STDIO, SSE, and Streamable HTTP
- **FastMCP 2.12+**: Upgraded from legacy MCP SDK
- **Output Schemas**: Type-safe tool responses with Pydantic models
- **Resource Annotations**: Priority, audience, and metadata
- **New Resources**: `odoo://fields/{model}`, `odoo://methods/{model}`, `odoo://server/info`
- **Python 3.13 Support**: Full support for Python 3.10-3.13
- **Enhanced Logging**: Timestamped logs in ./logs/ directory
- **Docker Transport Images**: Separate images for SSE and HTTP transports

### Changed
- **Configuration**: Migrated to fastmcp.json from deprecated dependencies parameter
- **API Performance**: ~75% faster JSON-RPC vs XML-RPC (617 vs 353 req/sec)

### Improved
- **Error Handling**: Context-aware error messages
- **Documentation**: Comprehensive CLAUDE.md and TRANSPORTS.md
- **Docker Build**: Optimized layer caching for faster builds

## [0.0.3] - 2024-XX-XX

### Added
- Initial fork from tuanle96/mcp-odoo
- Basic MCP server implementation
- Core tools: execute_method, search_employee, search_holidays
- Basic resources: models, model info, records, search

### Technical Foundation
- JSON-RPC client for Odoo
- MCP SDK integration
- Docker support
- Environment variable configuration

---

**Note**: Dates in YYYY-MM-DD format. Version 0.0.5 is currently unreleased.

For detailed migration guides and usage examples, see [README.md](README.md).
