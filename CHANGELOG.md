# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed (BREAKING BEHAVIOUR CORRECTION)

- **`batch_execute` was never atomic.** It was documented as "all succeed or
  all rollback", but each operation is an independent Odoo call committed in
  its own transaction — no rollback ever existed. On failure it even reported
  "no operations committed", which was false. The behaviour is unchanged
  (fail-fast); the documentation, tool description, and error message now tell
  the truth. Responses gained `rolled_back`, which is always `False`.
  Use an Odoo-side method for genuine all-or-nothing work.
- **`atomic=` renamed to `stop_on_error=`** to match what it actually does.
  `atomic=` still works as a deprecated alias and logs a warning.
- **`@N` result references now work.** They were documented in README.md and
  AGENTS.md but never implemented; `"@1"` was passed to Odoo as a literal
  string. Substitution is implemented in the new `odoo_mcp.batch` module and
  resolves anywhere in an operation's args/kwargs. Referencing `@0`, a future
  operation, or a failed operation is now an explicit error.
- **`batch_execute` now applies the same guardrails as `execute_method`** —
  domain normalization and the smart-limit policy, which it previously
  bypassed entirely. Shared via a new `_prepare_call` helper.
- Documented example `'[[@2]]'` was invalid JSON; corrected to `'[["@2"]]'`.

### Security

- `.env.example` claimed `MCP_HOST` defaults to `0.0.0.0` "for all
  interfaces". The real default is `127.0.0.1`, and the SSE/HTTP runners have
  no authentication — following the example published unauthenticated Odoo
  read/write access. Corrected, with the auth alternative called out.
- Added `Dockerfile.http-secure`. It was referenced by `Dockerfile.http` but
  had never existed, leaving the Bearer-auth runner with no container path.
- `docker-compose.prod.yml` published both unauthenticated transports on all
  host interfaces. It now publishes only the Bearer-auth service; the no-auth
  runners are bound to `127.0.0.1`. Same loopback binding applied to
  `docker-compose.yml`.

### Added

- `tests/test_batch.py` — 26 tests covering reference substitution, batch
  failure honesty, and the newly-applied guardrails.
- CI workflow running black, isort, ruff, mypy, and pytest.

## [1.0.0-beta] - 2025-01-07

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
- uvx installation as Option

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

## [1.0.0-beta.2] - 2025-01-10

### Added

**Documentation**:
- 📖 **USER_GUIDE.md**: Comprehensive step-by-step setup guide for new users
- 📖 **CLAUDE.md**: AI assistant guidance for working in this codebase
- Enhanced `.env.example` with API version and HTTP transport configuration examples
- .claude directory support with .gitignore exclusion for local AI assistant config

**Dependencies**:
- `python-dotenv` for automatic .env file loading
- Expanded project keywords (odoo 17, odoo 18, odoo 19, docker, etc.)

### Changed

**Branding**:
- Renamed "Odoo MCP Server" → "Advanced Odoo MCP Server" throughout codebase
- Updated all server startup messages and documentation

**Infrastructure**:
- Docker base image: Python 3.12 → 3.13 for SSE and HTTP transports
- Claude Desktop configuration: Reordered options for better UX

**Documentation**:
- README.md: Complete rewrite for first-time users with clearer installation flow
- Enhanced acknowledgment text for original author contribution
- Code formatting improvements across `run_server*.py` files

### Fixed

- README Installation section order to match Claude Desktop setup flow
- Markdown inconsistencies and formatting errors across documentation
- Docker build configuration issues

### Removed

- Phase 1 code quality improvements (broken config.py module)

## [Unreleased]

### Changed

**Legal**:
- **License**: Changed from MIT License to GNU General Public License v3.0 or later (GPL-3.0-or-later)
  - Ensures all derivative works remain open source
  - Protects against proprietary forks
  - Updated in: LICENSE, pyproject.toml, fastmcp.json, README.md

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
