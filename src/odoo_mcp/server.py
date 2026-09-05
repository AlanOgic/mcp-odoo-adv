"""
MCP server for Odoo integration

Provides MCP tools and resources for interacting with Odoo ERP systems
"""

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from . import cookbook as _cookbook
from .batch import FAILED, substitute_references
from .domain import normalize_domain
from .limits import SEARCH_METHODS, apply_limits, warn_large_read, warn_large_result
from .odoo_client import OdooClient, get_odoo_client


@dataclass
class AppContext:
    """Application context for the MCP server"""

    odoo: OdooClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Application lifespan for initialization and cleanup
    """
    # Initialize Odoo client on startup
    odoo_client = get_odoo_client()

    try:
        yield AppContext(odoo=odoo_client)
    finally:
        # No cleanup needed for Odoo client
        pass


# Create MCP server
mcp = FastMCP(
    "Odoo MCP Server",
    lifespan=app_lifespan,
)


# ----- MCP Resources -----
#
# Resources are discovery endpoints — read-only, side-effect-free views
# that help LLM clients orient before calling the universal tools. Each
# handler delegates to OdooClient.execute_method so the client layer only
# deals with transport+auth; business logic and error envelopes live here.


def _error(message: str) -> str:
    return json.dumps({"error": message}, indent=2)


@mcp.resource(
    "odoo://models",
    description="List all available models in the Odoo system",
    annotations={"audience": ["assistant"], "priority": 0.9},
)
def get_models() -> str:
    """List all available Odoo models with their display names."""
    odoo_client = get_odoo_client()
    try:
        model_ids = odoo_client.execute_method("ir.model", "search", [])
        if not model_ids:
            return json.dumps({"model_names": [], "models_details": {}}, indent=2)
        records = odoo_client.execute_method(
            "ir.model", "read", model_ids, ["model", "name"]
        )
        model_names = sorted(r["model"] for r in records)
        return json.dumps(
            {
                "model_names": model_names,
                "models_details": {
                    r["model"]: {"name": r.get("name", "")} for r in records
                },
            },
            indent=2,
        )
    except Exception as exc:
        return _error(str(exc))


@mcp.resource(
    "odoo://record/{model_name}/{record_id}",
    description="Get a specific record by ID (all fields)",
    annotations={"audience": ["user", "assistant"], "priority": 0.7},
)
def get_record(model_name: str, record_id: str) -> str:
    """Read a single record by ID.

    Parameters:
        model_name: Odoo model name (e.g. ``res.partner``)
        record_id: Integer record id as a string
    """
    odoo_client = get_odoo_client()
    try:
        record_id_int = int(record_id)
    except ValueError:
        return _error(f"record_id must be an integer, got {record_id!r}")
    try:
        records = odoo_client.execute_method(model_name, "read", [record_id_int])
        if not records:
            return _error(f"Record not found: {model_name} ID {record_id}")
        return json.dumps(records[0], indent=2)
    except Exception as exc:
        return _error(str(exc))


@mcp.resource(
    "odoo://model/{model_name}/schema",
    description=(
        "Complete schema for a model: field definitions, relationships, "
        "required/readonly/computed fields. This is the canonical discovery "
        "resource — prefer it over fetching raw fields."
    ),
    annotations={"audience": ["assistant"], "priority": 0.9},
)
def get_model_schema(model_name: str) -> str:
    """Return a categorized schema for ``model_name``.

    Includes:
        * Raw field definitions (types, constraints, help text, defaults)
        * Relationships (many2one / one2many / many2many) with target models
        * Required / readonly / computed field lists
    """
    odoo_client = get_odoo_client()
    try:
        fields = odoo_client.execute_method(model_name, "fields_get")

        # Organize fields by category
        schema = {
            "model": model_name,
            "fields": fields,
            "relationships": {},
            "required_fields": [],
            "readonly_fields": [],
            "computed_fields": [],
        }

        # Categorize fields
        for field_name, field_def in fields.items():
            field_type = field_def.get("type", "")

            # Track relationships
            if field_type in ["many2one", "one2many", "many2many"]:
                schema["relationships"][field_name] = {
                    "type": field_type,
                    "relation": field_def.get("relation", ""),
                    "string": field_def.get("string", ""),
                }

            # Track required fields
            if field_def.get("required"):
                schema["required_fields"].append(field_name)

            # Track readonly fields
            if field_def.get("readonly"):
                schema["readonly_fields"].append(field_name)

            # Track computed fields
            if field_def.get("store") is False or field_def.get("compute"):
                schema["computed_fields"].append(field_name)

        return json.dumps(schema, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://model/{model_name}/access",
    description="Access rights for the current user on this model",
    annotations={"audience": ["assistant"], "priority": 0.7},
)
def get_model_access(model_name: str) -> str:
    """
    Check what operations the current user can perform on a model

    Returns permissions for: read, write, create, unlink (delete)

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        # Check access rights for all CRUD operations
        access_rights = {}
        operations = ["read", "write", "create", "unlink"]

        for operation in operations:
            try:
                # Use check_access_rights method
                has_access = odoo_client.execute_method(
                    model_name,
                    "check_access_rights",
                    operation,
                    False,  # raise_exception=False
                )
                access_rights[operation] = has_access
            except Exception:
                access_rights[operation] = False

        return json.dumps(
            {
                "model": model_name,
                "access_rights": access_rights,
                "note": "These are model-level permissions. Record-level rules may further restrict access.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://workflows",
    description="Available business workflows based on installed modules",
    annotations={"audience": ["assistant"], "priority": 0.8},
)
def get_workflows() -> str:
    """
    Discover available business workflows based on installed Odoo modules

    Returns common workflows for installed apps like Sales, Inventory, CRM, etc.
    """
    odoo_client = get_odoo_client()
    try:
        # Get installed modules — fields list keeps the payload small even on
        # instances with hundreds of modules
        modules = odoo_client.execute_method(
            "ir.module.module",
            "search_read",
            [("state", "=", "installed")],
            fields=["name", "shortdesc", "application"],
            limit=1000,
        )

        module_names = {m["name"]: m.get("shortdesc", "") for m in modules}

        # Define known workflows for common modules
        workflows = {}

        if "sale" in module_names:
            workflows["sales"] = {
                "module": "sale",
                "title": "Sales Management",
                "workflows": [
                    {
                        "name": "quotation_to_order",
                        "steps": [
                            "Create quotation (sale.order with state='draft')",
                            "Send quotation to customer (method: action_quotation_send)",
                            "Confirm order (method: action_confirm)",
                            "Create invoice (method: _create_invoices)",
                        ],
                        "model": "sale.order",
                    },
                    {
                        "name": "create_customer_order",
                        "steps": [
                            "Create/find customer (res.partner)",
                            "Create sale.order with partner_id",
                            "Add order lines (sale.order.line)",
                            "Confirm order",
                        ],
                        "models": ["res.partner", "sale.order", "sale.order.line"],
                    },
                ],
            }

        if "stock" in module_names:
            workflows["inventory"] = {
                "module": "stock",
                "title": "Inventory Management",
                "workflows": [
                    {
                        "name": "product_transfer",
                        "steps": [
                            "Create picking (stock.picking)",
                            "Add move lines (stock.move)",
                            "Validate transfer (method: button_validate)",
                        ],
                        "model": "stock.picking",
                    },
                    {
                        "name": "inventory_adjustment",
                        "steps": [
                            "Create inventory adjustment (stock.inventory)",
                            "Set product quantities",
                            "Validate adjustment",
                        ],
                        "model": "stock.inventory",
                    },
                ],
            }

        if "crm" in module_names:
            workflows["crm"] = {
                "module": "crm",
                "title": "CRM / Leads",
                "workflows": [
                    {
                        "name": "lead_to_opportunity",
                        "steps": [
                            "Create lead (crm.lead)",
                            "Convert to opportunity (method: convert_opportunity)",
                            "Move through stages",
                            "Mark as won (method: action_set_won)",
                        ],
                        "model": "crm.lead",
                    }
                ],
            }

        if "hr" in module_names:
            workflows["hr"] = {
                "module": "hr",
                "title": "Human Resources",
                "workflows": [
                    {
                        "name": "leave_request",
                        "steps": [
                            "Create leave request (hr.leave)",
                            "Submit for approval (method: action_approve)",
                            "Manager validates or refuses",
                        ],
                        "model": "hr.leave",
                    }
                ],
            }

        if "account" in module_names:
            workflows["accounting"] = {
                "module": "account",
                "title": "Accounting",
                "workflows": [
                    {
                        "name": "create_invoice",
                        "steps": [
                            "Create invoice (account.move with move_type='out_invoice')",
                            "Add invoice lines (account.move.line)",
                            "Post invoice (method: action_post)",
                            "Register payment",
                        ],
                        "model": "account.move",
                    }
                ],
            }

        if "project" in module_names:
            workflows["projects"] = {
                "module": "project",
                "title": "Project Management",
                "workflows": [
                    {
                        "name": "task_lifecycle",
                        "steps": [
                            "Create project (project.project)",
                            "Create tasks (project.task)",
                            "Assign to users",
                            "Track progress through stages",
                        ],
                        "models": ["project.project", "project.task"],
                    }
                ],
            }

        return json.dumps(
            {
                "installed_modules": list(module_names.keys()),
                "available_workflows": workflows,
                "note": "Use execute_method tool to call the methods mentioned in workflow steps",
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://methods/{model_name}",
    description="""Available methods for a model.

    ⚡ IMPORTANT: If a specialized tool doesn't exist, use the execute_method tool!
    The execute_method tool can call ANY of these methods.

    Example: execute_method(model='res.partner', method='search_read',
                           args_json='[[...domain...]]', kwargs_json='{...}')
    """,
    annotations={"audience": ["assistant"], "priority": 0.7},
)
def get_methods(model_name: str) -> str:
    """
    Get available methods for a model

    Note: This returns common Odoo ORM methods. Custom methods may exist
    but require direct model inspection via execute_method.

    ⚡ UNIVERSAL TOOL: If no specialized tool exists for what you need,
    use execute_method to call any method listed here!

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    # Static ORM reference — no Odoo round-trip needed.
    try:
        # Return common Odoo ORM methods
        common_methods = {
            "read_methods": [
                {
                    "name": "search",
                    "description": "Search for record IDs matching domain",
                    "params": ["domain", "offset", "limit", "order", "count"],
                },
                {
                    "name": "search_read",
                    "description": "Search and read records in one call",
                    "params": ["domain", "fields", "offset", "limit", "order"],
                },
                {
                    "name": "read",
                    "description": "Read specific fields from records",
                    "params": ["ids", "fields"],
                },
                {
                    "name": "search_count",
                    "description": "Count records matching domain",
                    "params": ["domain"],
                },
                {
                    "name": "name_search",
                    "description": "Search records by name",
                    "params": ["name", "args", "operator", "limit"],
                },
                {
                    "name": "name_get",
                    "description": "Get display names for records",
                    "params": ["ids"],
                },
                {
                    "name": "fields_get",
                    "description": "Get field definitions",
                    "params": ["allfields", "attributes"],
                },
            ],
            "write_methods": [
                {
                    "name": "create",
                    "description": "Create new record(s)",
                    "params": ["vals"],
                },
                {
                    "name": "write",
                    "description": "Update existing record(s)",
                    "params": ["ids", "vals"],
                },
                {
                    "name": "unlink",
                    "description": "Delete record(s)",
                    "params": ["ids"],
                },
            ],
            "note": f"Use execute_method tool to call these methods on {model_name}",
            "example": {
                "tool": "execute_method",
                "model": model_name,
                "method": "search_read",
                "args": [[["name", "ilike", "example"]]],
                "kwargs": {"fields": ["id", "name"], "limit": 10},
            },
        }

        return json.dumps(common_methods, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://server/info",
    description="Get Odoo server information including version and installed modules",
    annotations={"audience": ["user", "assistant"], "priority": 0.5},
)
def get_server_info() -> str:
    """
    Get Odoo server metadata

    Returns server version, database name, and list of installed modules
    """
    odoo_client = get_odoo_client()
    try:
        base_info = odoo_client.execute_method(
            "ir.module.module",
            "search_read",
            [("state", "=", "installed"), ("name", "=", "base")],
            fields=["latest_version", "installed_version"],
            limit=1,
        )

        installed_modules = odoo_client.execute_method(
            "ir.module.module",
            "search_read",
            [("state", "=", "installed")],
            fields=[
                "name",
                "shortdesc",
                "author",
                "installed_version",
                "application",
                "license",
            ],
            limit=1000,
        )
        module_ids = [m.get("id") for m in installed_modules]
        version_info = base_info  # shape-compatible with old code

        # Get database name from config
        db_name = odoo_client.db if hasattr(odoo_client, "db") else "unknown"

        server_info = {
            "database": db_name,
            "odoo_version": (
                version_info[0].get("latest_version", "unknown")
                if version_info
                else "unknown"
            ),
            "installed_modules_count": len(module_ids) if module_ids else 0,
            "installed_modules": [
                {
                    "name": mod.get("name"),
                    "title": mod.get("shortdesc"),
                    "version": mod.get("installed_version"),
                    "author": mod.get("author", "Unknown"),
                    "application": mod.get("application", False),
                    "license": mod.get("license", "Unknown"),
                }
                for mod in installed_modules
            ],
        }

        return json.dumps(server_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://cookbook/patterns",
    description=(
        "Your personal COOKBOOK — Learned Patterns (recipes from "
        f"≥{_cookbook.MIN_FAILED_APPROACHES} failed attempts).\n\n"
        "Workflow:\n"
        "  1. Try execute_method/batch_execute first.\n"
        "  2. After the first failure, read this resource for similar recipes.\n"
        "  3. After ≥4 failed approaches, call add_cookbook_pattern to save what worked."
    ),
    annotations={"audience": ["assistant"], "priority": 0.95},
)
def get_cookbook_patterns() -> str:
    """Return the Learned Patterns section of COOKBOOK.md as a JSON envelope."""
    cookbook_path = _cookbook.find_cookbook(_cookbook.default_cookbook_paths())
    if cookbook_path is None:
        return json.dumps(
            {
                "found": False,
                "error": "COOKBOOK.md not found",
                "searched_paths": [str(p) for p in _cookbook.default_cookbook_paths()],
            },
            indent=2,
        )
    return json.dumps(_cookbook.read_patterns(cookbook_path), indent=2)


# ----- Pydantic response models -----


class ExecuteMethodResponse(BaseModel):
    """Response model for the execute_method tool."""

    success: bool = Field(
        description="Indicates if the method execution was successful"
    )
    result: Optional[Any] = Field(
        default=None, description="Result of the method execution"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class BatchExecuteResponse(BaseModel):
    """Response model for batch_execute tool"""

    success: bool = Field(description="Whether all operations succeeded")
    results: List[Dict[str, Any]] = Field(description="Results for each operation")
    total_operations: int = Field(description="Total number of operations attempted")
    successful_operations: int = Field(description="Number of successful operations")
    failed_operations: int = Field(description="Number of failed operations")
    rolled_back: bool = Field(
        default=False,
        description=(
            "Always False. Odoo commits each operation independently, so this "
            "server cannot roll back operations that already succeeded."
        ),
    )
    error: Optional[str] = Field(
        default=None, description="Overall error message if batch failed"
    )


def _odoo_from(ctx: Context) -> OdooClient:
    """Return the Odoo client held on the request's lifespan context."""
    request_context = ctx.request_context
    if request_context is None:  # pragma: no cover - FastMCP always sets this
        raise RuntimeError("batch/execute called without an active request context")
    return cast(OdooClient, request_context.lifespan_context.odoo)


def _prepare_call(method: str, args: list, kwargs: dict) -> tuple:
    """Apply domain normalization and the smart-limit policy to a single call.

    Shared by ``execute_method`` and ``batch_execute`` so both paths get the
    same guardrails. Warnings go to stderr; the adjusted ``(args, kwargs)``
    are returned.
    """
    if method in SEARCH_METHODS and args:
        args = list(args)
        args[0] = normalize_domain(args[0])
        print(f"Normalized domain for {method}: {args[0]}", file=sys.stderr)

    kwargs, limit_warnings = apply_limits(method, kwargs)
    for warning in limit_warnings:
        print(f"\u26a0\ufe0f  {warning}", file=sys.stderr)

    if method == "read":
        for warning in warn_large_read(args):
            print(f"\u26a0\ufe0f  {warning}", file=sys.stderr)

    return args, kwargs


def _batch_argument(
    raw_json: Any, direct: Any, kind: type, default: Any, label: str, idx: int
) -> Any:
    """Read one operation's args/kwargs from either the JSON or direct form."""
    if raw_json:
        value = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
    elif direct is not None:
        value = direct
    else:
        return default
    if not isinstance(value, kind):
        raise ValueError(
            f"Operation {idx}: {label} must be a {kind.__name__}, "
            f"got {type(value).__name__}"
        )
    return value


# ----- MCP Tools -----


@mcp.tool(
    description="""⚡ UNIVERSAL TOOL - Execute ANY Odoo method on ANY model

    This is THE CORE tool. Full Odoo API access. No limitations.
    Can call ANY of the hundreds of Odoo methods across all models.

    Common use cases:
    - Creating records: method='create'
    - Searching: method='search_read'
    - Reading records: method='read'
    - Updating: method='write'
    - Deleting: method='unlink'
    - Custom methods: method='action_confirm', 'action_post', etc.

    🛡️ SMART LIMITS (to prevent massive data returns):
    - Default limit: 100 records (if not specified)
    - Maximum limit: 1000 records (hard cap)
    - Override: Set "limit" in kwargs_json to your desired value
    - Unlimited: Set "limit": 0 or "limit": false (will warn)

    Before using, check:
    - odoo://model/{model}/schema for field definitions
    - odoo://methods/{model} for available methods

    Odoo provides excellent error messages for validation - no pre-check needed!
    """,
    output_schema=ExecuteMethodResponse.model_json_schema(),
)
def execute_method(
    ctx: Context,
    model: str,
    method: str,
    args_json: Optional[str] = None,
    kwargs_json: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute ANY method on an Odoo model - UNIVERSAL FALLBACK TOOL

    ⚡ This tool can call ANY Odoo method that doesn't have a specialized tool.
    It's your escape hatch for the full power of Odoo's API.

    Parameters:
        model: The model name (e.g., 'res.partner', 'sale.order', 'crm.lead')
        method: Method name to execute (e.g., 'create', 'search_read', 'write', 'action_confirm')
        args_json: JSON string for positional arguments (e.g., '[[["name", "=", "Test"]]]')
        kwargs_json: JSON string for keyword arguments (e.g., '{"fields": ["name", "email"], "limit": 10}')

    Common Examples:

        Create a customer:
            model='res.partner'
            method='create'
            args_json='[{"name": "Acme Corp", "email": "info@acme.com", "customer_rank": 1}]'

        Search partners:
            model='res.partner'
            method='search_read'
            args_json='[[["name", "ilike", "Acme"]]]'
            kwargs_json='{"fields": ["name", "email"], "limit": 5}'

        Update records:
            model='res.partner'
            method='write'
            args_json='[[1, 2, 3], {"phone": "+1234567890"}]'

        Delete records:
            model='res.partner'
            method='unlink'
            args_json='[[1, 2, 3]]'

        Get field definitions:
            model='crm.lead'
            method='fields_get'

        Call custom/business methods:
            model='sale.order'
            method='action_confirm'
            args_json='[[5]]'  # Order ID 5

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - result: Result of the method (if success)
        - error: Error message (if failure)

    Pro Tips:
    - Check odoo://model/{model}/schema for required fields
    - Check odoo://methods/{model} for available methods
    - For workflows, see odoo://workflows for step-by-step guides
    - Odoo's own validation errors are descriptive — let the call fail and
      read the error rather than pre-validating client-side
    """
    odoo = _odoo_from(ctx)
    try:
        # Parse JSON strings to actual Python objects
        args = []
        kwargs = {}

        if args_json:
            try:
                args = json.loads(args_json)
                if not isinstance(args, list):
                    return {
                        "success": False,
                        "error": f"args_json must be a JSON array, got: {type(args).__name__}",
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in args_json: {str(e)}",
                }

        if kwargs_json:
            try:
                kwargs = json.loads(kwargs_json)
                if not isinstance(kwargs, dict):
                    return {
                        "success": False,
                        "error": f"kwargs_json must be a JSON object, got: {type(kwargs).__name__}",
                    }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in kwargs_json: {str(e)}",
                }

        # Domain normalization + smart-limit policy (shared with batch_execute)
        args, kwargs = _prepare_call(method, args, kwargs)

        result = odoo.execute_method(model, method, *args, **kwargs)

        for warning in warn_large_result(result):
            print(f"⚠️  {warning}", file=sys.stderr)

        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool(
    description="""Execute multiple Odoo operations in sequence.

    ⚠️ NOT ATOMIC — this server cannot roll back. Odoo commits each operation
    as its own transaction, so any operation that has already succeeded stays
    committed even if a later one fails. `stop_on_error=True` (the default)
    halts at the first failure to limit the blast radius; it does NOT undo
    what came before. If you need true all-or-nothing semantics, write an
    Odoo-side method that does the whole unit of work and call that instead.

    Result references: a string of the exact form "@N" (1-indexed) anywhere in
    an operation's args/kwargs is replaced with the result of operation N.
    Create a partner, then pass "@1" as partner_id on the order.

    Each operation gets the same domain normalization and smart limits as
    execute_method.
    """,
    output_schema=BatchExecuteResponse.model_json_schema(),
)
def batch_execute(
    ctx: Context,
    operations: List[Dict[str, Any]],
    stop_on_error: bool = True,
    atomic: Optional[bool] = None,
) -> BatchExecuteResponse:
    """
    Execute multiple operations in one call, in order.

    NOT a transaction. See the tool description: earlier successes are not
    rolled back when a later operation fails.

    Parameters:
        operations: List of operations, each with:
                   - model: str (required)
                   - method: str (required)
                   - args: list (optional) OR args_json: str (JSON string)
                   - kwargs: dict (optional) OR kwargs_json: str (JSON string)
        stop_on_error: Stop at the first failure (default). When False, every
                   operation is attempted and failures are reported per-item.
        atomic: Deprecated alias for stop_on_error. It never provided rollback
                   despite the name; pass stop_on_error instead.

    Examples:
        # Create a customer, then an order referencing it via "@1"
        batch_execute(operations=[
            {
                "model": "res.partner",
                "method": "create",
                "args_json": '[{"name": "Acme Corp", "customer_rank": 1}]'
            },
            {
                "model": "sale.order",
                "method": "create",
                "args_json": '[{"partner_id": "@1"}]'
            }
        ])

    Returns:
        BatchExecuteResponse with per-operation results. `rolled_back` is
        always False.
    """
    odoo = _odoo_from(ctx)

    if atomic is not None:
        print(
            "⚠️  batch_execute: 'atomic' is deprecated — it never provided "
            "rollback. Use 'stop_on_error'.",
            file=sys.stderr,
        )
        stop_on_error = atomic

    results: List[Dict[str, Any]] = []
    op_results: List[Any] = []  # one entry per operation, for "@N" resolution
    successful = 0
    failed = 0

    for idx, op in enumerate(operations):
        try:
            model = op.get("model")
            method = op.get("method")
            if not model or not method:
                raise ValueError(f"Operation {idx}: 'model' and 'method' are required")

            args = _batch_argument(
                op.get("args_json"), op.get("args"), list, [], "args", idx
            )
            kwargs = _batch_argument(
                op.get("kwargs_json"), op.get("kwargs"), dict, {}, "kwargs", idx
            )

            # Resolve "@N" references against earlier results
            args = substitute_references(args, op_results)
            kwargs = substitute_references(kwargs, op_results)

            # Same guardrails as execute_method
            args, kwargs = _prepare_call(method, args, kwargs)

            result = odoo.execute_method(model, method, *args, **kwargs)

            for warning in warn_large_result(result):
                print(f"⚠️  {warning}", file=sys.stderr)

            op_results.append(result)
            results.append({"operation_index": idx, "success": True, "result": result})
            successful += 1

        except Exception as e:
            op_results.append(FAILED)
            results.append({"operation_index": idx, "success": False, "error": str(e)})
            failed += 1

            if stop_on_error:
                return BatchExecuteResponse(
                    success=False,
                    results=results,
                    total_operations=len(operations),
                    successful_operations=successful,
                    failed_operations=failed,
                    rolled_back=False,
                    error=(
                        f"Batch stopped at operation {idx}: {e}. "
                        f"{successful} earlier operation(s) were already "
                        f"committed to Odoo and were NOT rolled back."
                    ),
                )

    return BatchExecuteResponse(
        success=(failed == 0),
        results=results,
        total_operations=len(operations),
        successful_operations=successful,
        failed_operations=failed,
        rolled_back=False,
        error=(
            None if failed == 0 else f"{failed} of {len(operations)} operations failed"
        ),
    )


@mcp.tool(
    description=(
        "Add a learned pattern to COOKBOOK.md. Reserved for problems that "
        f"required ≥{_cookbook.MIN_FAILED_APPROACHES} failed approaches before "
        "the working solution was found.\n\n"
        "Provide: a brief problem statement, the list of failed approaches "
        "(each with the reason it failed), the working solution code, why it "
        "works, and the key lesson. After a successful add, announce: "
        "'✅ New pattern documented: <key lesson>'."
    )
)
def add_cookbook_pattern(
    problem: str,
    failed_approaches: List[str],
    working_solution: str,
    why_it_works: str,
    key_lesson: str,
    related_links: str = "",
) -> Dict[str, Any]:
    """Append a new pattern to COOKBOOK.md after validating the threshold."""
    cookbook_path = _cookbook.find_cookbook(_cookbook.default_cookbook_paths())
    if cookbook_path is None:
        return {
            "success": False,
            "error": "COOKBOOK.md not found",
            "searched_paths": [str(p) for p in _cookbook.default_cookbook_paths()],
        }
    return _cookbook.add_pattern(
        cookbook_path,
        problem=problem,
        failed_approaches=failed_approaches,
        working_solution=working_solution,
        why_it_works=why_it_works,
        key_lesson=key_lesson,
        related_links=related_links,
    )


# ----- MCP Prompts -----


@mcp.prompt(name="search-customers")
def search_customers_prompt(city: str = "", country: str = "") -> List[Dict[str, str]]:
    """Search for customers with optional location filters"""
    filter_desc = []
    if city:
        filter_desc.append(f"in {city}")
    if country:
        filter_desc.append(f"from {country}")

    location_filter = " ".join(filter_desc) if filter_desc else "with any location"

    return [
        {
            "role": "user",
            "content": f"""Find customers {location_filter}.

Use execute_method with:
- model='res.partner'
- method='search_read'
- domain: [["customer_rank", ">", 0]]
- Add location filters if needed

Example:
execute_method(
    model='res.partner',
    method='search_read',
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{{"fields": ["name", "email", "phone", "city", "country_id"], "limit": 20}}'
)

Check odoo://model/res.partner/schema for all available fields.
""",
        }
    ]


@mcp.prompt(name="create-sales-order")
def create_sales_order_prompt(customer_id: int = 0) -> List[Dict[str, str]]:
    """Create a sales order in Odoo"""
    return [
        {
            "role": "user",
            "content": f"""Create a new sales order{' for customer ID ' + str(customer_id) if customer_id > 0 else ''}.

Use execute_method to create:
1. Find customer (if not provided): model='res.partner', method='search_read'
2. Create order: model='sale.order', method='create'
3. Optionally confirm: model='sale.order', method='action_confirm'

Check schemas:
- odoo://model/sale.order/schema for required fields
- odoo://model/sale.order.line/schema for order lines

See odoo://workflows for complete sales workflow.
""",
        }
    ]


@mcp.prompt(name="odoo-exploration")
def odoo_exploration_prompt() -> List[Dict[str, str]]:
    """Discover capabilities of this Odoo instance"""
    return [
        {
            "role": "user",
            "content": """Explore this Odoo instance systematically:

1. **Server Info**: Read odoo://server/info
2. **Workflows**: Read odoo://workflows
3. **Key Models**: Check odoo://models
4. **Permissions**: Check odoo://model/{model}/access for key models

Provide summary of:
- Odoo version and installed apps
- Available workflows
- My permissions
- 3-5 suggested tasks
""",
        }
    ]
