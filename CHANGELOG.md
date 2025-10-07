# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta] - 2025-10-06

### 🎯 Philosophy Change: Radical Simplification

**"Two tools. Infinite possibilities. Full Odoo API access."**

This release represents a fundamental shift in philosophy - from maintaining multiple specialized tools to providing two universal tools with comprehensive documentation.

### Removed (BREAKING CHANGES)

**Specialized Tools** (~600 lines removed):
- ❌ `search_employee` - Use `execute_method(model="hr.employee", method="search_read")`
- ❌ `search_holidays` - Use `execute_method(model="hr.leave", method="search_read")`
- ❌ `validate_before_execute` - Odoo's native error messages are more reliable
- ❌ `deep_read` - Was causing oversized responses; use `execute_method` with explicit fields
- ❌ `scan_pending_crm_responses` - Too domain-specific; examples now in COOKBOOK.md

**Prompts**:
- ❌ `troubleshoot-operation` - Generic troubleshooting is more effective
- ❌ `draft-crm-responses` - Replaced by COOKBOOK.md examples

### Added

**Smart Limits System**:
- DEFAULT_LIMIT: 100 records (auto-applied when no limit specified)
- MAX_LIMIT: 1000 records (hard cap on user requests)
- Override capability: Set explicit `"limit": N` in kwargs_json
- Unlimited option: Set `"limit": 0` with warning
- Prevents accidental GBs of data returns (e.g., mail.message queries)

**Documentation**:
- 📖 **COOKBOOK.md**: 40+ comprehensive examples covering all common operations
  - CRUD operations
  - Relationships (many2one, one2many, many2many)
  - Workflows and custom methods
  - Batch operations
  - Pagination strategies
  - Efficient querying patterns
- 📖 **DOCS/CLAUDE.md**: Complete rewrite for v1.0
  - Quick start with uvx
  - Architecture overview
  - Smart limits documentation
  - Troubleshooting guide
  - Best practices
  - Version history

**uvx Support**:
- Zero-installation execution: `uvx --from odoo-mcp odoo-mcp`
- Claude Desktop config with uvx
- From source: `uvx --from . odoo-mcp`

### Changed

**README.md**: Complete rewrite
- Minimalist philosophy front and center
- "What We Removed (And Why)" section
- Smart limits documentation
- uvx installation as Option 1

**Core Tools**:
- `execute_method`: Enhanced with smart limits for search methods
- `batch_execute`: Remains as atomic transaction tool

**Resources & Prompts**:
- Kept 3 essential resources: models list, model schemas, record search
- Kept 3 essential prompts: customer search, sales orders, exploration

### Fixed

- Python version requirement: Changed from `>=3.12` to `>=3.10` (matching classifiers)
- Removed inconsistency between pyproject.toml line 10 and classifiers

### Meta

**Why This Matters**:

Power users already knew how to do everything with `execute_method`. The specialized tools were:
1. **Redundant**: Everything can be done with execute_method
2. **Broken**: validate_before_execute and deep_read had issues
3. **Maintenance burden**: More code to maintain and test
4. **Complexity**: Harder to understand and use correctly

By focusing on two universal tools and comprehensive documentation, we've created a more reliable, maintainable, and powerful server.

**The Result**:
- Simpler codebase (~600 lines removed)
- Better documentation (COOKBOOK.md with 40+ examples)
- More reliable (fewer moving parts)
- Same functionality (full Odoo API access)
- Better user experience (smart limits prevent mistakes)

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
  - **Tested & Production Ready**: Comprehensive validation with proper error handling
- **`deep_read`** - Intelligent relationship navigator
  - Auto-follows many2one relationships by default (optimized for performance)
  - Configurable depth, field selection, and relation limits
  - `minimal_fields` parameter (default: True) prevents oversized responses
  - Returns: `{success, record, related_records{}, error}`
  - Use case: Get sales order with customer info in one call
  - **Optimized**: Only fetches id/name/display_name for relations by default
  - **Tested & Production Ready**: Smart defaults prevent oversized payloads
- **`batch_execute`** - Atomic multi-operation transactions
  - Execute multiple operations in single transaction
  - Atomic mode: all succeed or all rollback
  - Flexible parameter format: accepts both direct objects and JSON strings
  - Returns: `{success, results[], total_operations, successful_operations, failed_operations}`
  - Use case: Create customer + create order in one transaction
  - **Tested & Production Ready**: Atomic and non-atomic modes fully functional
- **`scan_pending_crm_responses`** - CRM customer communication assistant
  - Scans CRM leads for unanswered customer messages
  - Detects messages from external contacts without follow-up responses
  - Generates AI-powered draft responses using context analysis
  - Creates internal log notes with drafts for review before sending
  - Returns: `{success, scanned_leads, pending_messages, drafts_created, leads_with_pending[]}`
  - Use case: Daily customer communication management and response automation
  - **Features**: Template-based draft generation, urgency detection, customizable scanning

#### 💬 MCP Prompts (User Templates)
User-selectable prompt templates that appear in Claude's prompt menu:
- **`search-customers`** - Customer search template with city/country filters
- **`create-sales-order`** - Step-by-step sales order creation guide with validation
- **`odoo-exploration`** - Systematic capability discovery for new Odoo instances
- **`troubleshoot-operation`** - Debug failed operations with systematic troubleshooting steps
- **`draft-crm-responses`** - Automated CRM response drafting workflow
  - Scans user's leads for pending customer messages
  - Generates draft responses with customizable limit
  - Provides guidance on reviewing and sending drafts

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

### Fixed

- **`validate_before_execute`** - Fixed domain format for model existence check
  - Corrected search_count domain syntax: `[[('model', '=', model)]]`
  - Resolved false negatives when validating search_read operations
  - Model existence check now works correctly for all operations
- **`batch_execute`** - Fixed parameter handling
  - Now accepts both direct format (`args`, `kwargs`) and JSON string format (`args_json`, `kwargs_json`)
  - Handles structured objects passed by MCP clients
  - More flexible parameter handling for different use cases
- **`deep_read`** - Multiple optimizations to prevent oversized responses
  - Added `minimal_fields` parameter (default: True) - only fetches id/name/display_name
  - Changed default behavior to only follow many2one relations (not one2many/many2many)
  - Added `limit_per_relation` parameter with configurable limit (default: 10)
  - Explicit `follow_relations` parameter required for one2many/many2many
  - Now practical for production use with complex Odoo models

### Improved

- **MCP Compliance** - Fully aligned with MCP 2025-06-18 specification
  - Proper separation of Resources (context) vs Tools (actions) vs Prompts (templates)
  - Resources teach capabilities, tools perform actions, prompts guide users
- **Developer Experience**
  - All syntax validated (Python 3.12+ compatible)
  - Backward compatible with existing implementations
  - Enhanced inline documentation and type hints
  - Comprehensive testing completed (75% production ready)
- **Documentation**
  - README.md completely updated with new features
  - Clear examples for all new tools and resources
  - JSON-2 API migration guide
  - Tool usage best practices
  - Test findings and known limitations documented

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
