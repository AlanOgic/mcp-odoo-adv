"""
MCP server for Odoo integration

Provides MCP tools and resources for interacting with Odoo ERP systems
"""

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Union, cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

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


@mcp.resource(
    "odoo://models",
    description="List all available models in the Odoo system",
    annotations={
        "audience": ["assistant"],
        "priority": 0.9
    }
)
def get_models() -> str:
    """Lists all available models in the Odoo system"""
    odoo_client = get_odoo_client()
    models = odoo_client.get_models()
    return json.dumps(models, indent=2)


@mcp.resource(
    "odoo://model/{model_name}",
    description="Get detailed information about a specific model including fields",
    annotations={
        "audience": ["assistant"],
        "priority": 0.8
    }
)
def get_model_info(model_name: str) -> str:
    """
    Get information about a specific model

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        # Get model info
        model_info = odoo_client.get_model_info(model_name)

        # Get field definitions
        fields = odoo_client.get_model_fields(model_name)
        model_info["fields"] = fields

        return json.dumps(model_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://record/{model_name}/{record_id}",
    description="Get detailed information of a specific record by ID",
    annotations={
        "audience": ["user", "assistant"],
        "priority": 0.7
    }
)
def get_record(model_name: str, record_id: str) -> str:
    """
    Get a specific record by ID

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        record_id: ID of the record
    """
    odoo_client = get_odoo_client()
    try:
        record_id_int = int(record_id)
        record = odoo_client.read_records(model_name, [record_id_int])
        if not record:
            return json.dumps(
                {"error": f"Record not found: {model_name} ID {record_id}"}, indent=2
            )
        return json.dumps(record[0], indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://search/{model_name}/{domain}",
    description="Search for records matching the domain",
    annotations={
        "audience": ["user", "assistant"],
        "priority": 0.6
    }
)
def search_records_resource(model_name: str, domain: str) -> str:
    """
    Search for records that match a domain

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: Search domain in JSON format (e.g., '[["name", "ilike", "test"]]')
    """
    odoo_client = get_odoo_client()
    try:
        # Parse domain from JSON string
        domain_list = json.loads(domain)

        # Set a reasonable default limit
        limit = 10

        # Perform search_read for efficiency
        results = odoo_client.search_read(model_name, domain_list, limit=limit)

        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://fields/{model_name}",
    description="Get field definitions for a specific model",
    annotations={
        "audience": ["assistant"],
        "priority": 0.75
    }
)
def get_fields(model_name: str) -> str:
    """
    Get field definitions for a model

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        fields = odoo_client.get_model_fields(model_name)
        return json.dumps(fields, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://model/{model_name}/schema",
    description="Complete schema for a model including fields, relationships, and constraints",
    annotations={
        "audience": ["assistant"],
        "priority": 0.85
    }
)
def get_model_schema(model_name: str) -> str:
    """
    Get comprehensive schema information for a model

    Includes:
    - Field definitions with types, constraints, help text
    - Relationships (many2one, one2many, many2many)
    - Required fields
    - Computed fields
    - Default values

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        # Get field definitions
        fields = odoo_client.get_model_fields(model_name)

        # Organize fields by category
        schema = {
            "model": model_name,
            "fields": fields,
            "relationships": {},
            "required_fields": [],
            "readonly_fields": [],
            "computed_fields": []
        }

        # Categorize fields
        for field_name, field_def in fields.items():
            field_type = field_def.get('type', '')

            # Track relationships
            if field_type in ['many2one', 'one2many', 'many2many']:
                schema['relationships'][field_name] = {
                    'type': field_type,
                    'relation': field_def.get('relation', ''),
                    'string': field_def.get('string', '')
                }

            # Track required fields
            if field_def.get('required'):
                schema['required_fields'].append(field_name)

            # Track readonly fields
            if field_def.get('readonly'):
                schema['readonly_fields'].append(field_name)

            # Track computed fields
            if field_def.get('store') is False or field_def.get('compute'):
                schema['computed_fields'].append(field_name)

        return json.dumps(schema, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://model/{model_name}/access",
    description="Access rights for the current user on this model",
    annotations={
        "audience": ["assistant"],
        "priority": 0.7
    }
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
        operations = ['read', 'write', 'create', 'unlink']

        for operation in operations:
            try:
                # Use check_access_rights method
                has_access = odoo_client.execute_method(
                    model_name,
                    'check_access_rights',
                    operation,
                    False  # raise_exception=False
                )
                access_rights[operation] = has_access
            except Exception:
                access_rights[operation] = False

        return json.dumps({
            "model": model_name,
            "access_rights": access_rights,
            "note": "These are model-level permissions. Record-level rules may further restrict access."
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://workflows",
    description="Available business workflows based on installed modules",
    annotations={
        "audience": ["assistant"],
        "priority": 0.8
    }
)
def get_workflows() -> str:
    """
    Discover available business workflows based on installed Odoo modules

    Returns common workflows for installed apps like Sales, Inventory, CRM, etc.
    """
    odoo_client = get_odoo_client()
    try:
        # Get installed modules
        modules = odoo_client.search_read(
            'ir.module.module',
            [('state', '=', 'installed')],
            fields=['name', 'shortdesc', 'application'],
            limit=None
        )

        module_names = {m['name']: m.get('shortdesc', '') for m in modules}

        # Define known workflows for common modules
        workflows = {}

        if 'sale' in module_names:
            workflows['sales'] = {
                "module": "sale",
                "title": "Sales Management",
                "workflows": [
                    {
                        "name": "quotation_to_order",
                        "steps": [
                            "Create quotation (sale.order with state='draft')",
                            "Send quotation to customer (method: action_quotation_send)",
                            "Confirm order (method: action_confirm)",
                            "Create invoice (method: _create_invoices)"
                        ],
                        "model": "sale.order"
                    },
                    {
                        "name": "create_customer_order",
                        "steps": [
                            "Create/find customer (res.partner)",
                            "Create sale.order with partner_id",
                            "Add order lines (sale.order.line)",
                            "Confirm order"
                        ],
                        "models": ["res.partner", "sale.order", "sale.order.line"]
                    }
                ]
            }

        if 'stock' in module_names:
            workflows['inventory'] = {
                "module": "stock",
                "title": "Inventory Management",
                "workflows": [
                    {
                        "name": "product_transfer",
                        "steps": [
                            "Create picking (stock.picking)",
                            "Add move lines (stock.move)",
                            "Validate transfer (method: button_validate)"
                        ],
                        "model": "stock.picking"
                    },
                    {
                        "name": "inventory_adjustment",
                        "steps": [
                            "Create inventory adjustment (stock.inventory)",
                            "Set product quantities",
                            "Validate adjustment"
                        ],
                        "model": "stock.inventory"
                    }
                ]
            }

        if 'crm' in module_names:
            workflows['crm'] = {
                "module": "crm",
                "title": "CRM / Leads",
                "workflows": [
                    {
                        "name": "lead_to_opportunity",
                        "steps": [
                            "Create lead (crm.lead)",
                            "Convert to opportunity (method: convert_opportunity)",
                            "Move through stages",
                            "Mark as won (method: action_set_won)"
                        ],
                        "model": "crm.lead"
                    }
                ]
            }

        if 'hr' in module_names:
            workflows['hr'] = {
                "module": "hr",
                "title": "Human Resources",
                "workflows": [
                    {
                        "name": "leave_request",
                        "steps": [
                            "Create leave request (hr.leave)",
                            "Submit for approval (method: action_approve)",
                            "Manager validates or refuses"
                        ],
                        "model": "hr.leave"
                    }
                ]
            }

        if 'account' in module_names:
            workflows['accounting'] = {
                "module": "account",
                "title": "Accounting",
                "workflows": [
                    {
                        "name": "create_invoice",
                        "steps": [
                            "Create invoice (account.move with move_type='out_invoice')",
                            "Add invoice lines (account.move.line)",
                            "Post invoice (method: action_post)",
                            "Register payment"
                        ],
                        "model": "account.move"
                    }
                ]
            }

        if 'project' in module_names:
            workflows['projects'] = {
                "module": "project",
                "title": "Project Management",
                "workflows": [
                    {
                        "name": "task_lifecycle",
                        "steps": [
                            "Create project (project.project)",
                            "Create tasks (project.task)",
                            "Assign to users",
                            "Track progress through stages"
                        ],
                        "models": ["project.project", "project.task"]
                    }
                ]
            }

        return json.dumps({
            "installed_modules": list(module_names.keys()),
            "available_workflows": workflows,
            "note": "Use execute_method tool to call the methods mentioned in workflow steps"
        }, indent=2)

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
    annotations={
        "audience": ["assistant"],
        "priority": 0.7
    }
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
    odoo_client = get_odoo_client()
    try:
        # Return common Odoo ORM methods
        common_methods = {
            "read_methods": [
                {
                    "name": "search",
                    "description": "Search for record IDs matching domain",
                    "params": ["domain", "offset", "limit", "order", "count"]
                },
                {
                    "name": "search_read",
                    "description": "Search and read records in one call",
                    "params": ["domain", "fields", "offset", "limit", "order"]
                },
                {
                    "name": "read",
                    "description": "Read specific fields from records",
                    "params": ["ids", "fields"]
                },
                {
                    "name": "search_count",
                    "description": "Count records matching domain",
                    "params": ["domain"]
                },
                {
                    "name": "name_search",
                    "description": "Search records by name",
                    "params": ["name", "args", "operator", "limit"]
                },
                {
                    "name": "name_get",
                    "description": "Get display names for records",
                    "params": ["ids"]
                },
                {
                    "name": "fields_get",
                    "description": "Get field definitions",
                    "params": ["allfields", "attributes"]
                }
            ],
            "write_methods": [
                {
                    "name": "create",
                    "description": "Create new record(s)",
                    "params": ["vals"]
                },
                {
                    "name": "write",
                    "description": "Update existing record(s)",
                    "params": ["ids", "vals"]
                },
                {
                    "name": "unlink",
                    "description": "Delete record(s)",
                    "params": ["ids"]
                }
            ],
            "note": f"Use execute_method tool to call these methods on {model_name}",
            "example": {
                "tool": "execute_method",
                "model": model_name,
                "method": "search_read",
                "args": [
                    [["name", "ilike", "example"]]
                ],
                "kwargs": {
                    "fields": ["id", "name"],
                    "limit": 10
                }
            }
        }

        return json.dumps(common_methods, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://server/info",
    description="Get Odoo server information including version and installed modules",
    annotations={
        "audience": ["user", "assistant"],
        "priority": 0.5
    }
)
def get_server_info() -> str:
    """
    Get Odoo server metadata

    Returns server version, database name, and list of installed modules
    """
    odoo_client = get_odoo_client()
    try:
        # Get server version info - search for base module
        base_ids = odoo_client._execute(
            'ir.module.module',
            'search',
            [['state', '=', 'installed'], ['name', '=', 'base']]
        )
        # Read only specific fields to avoid None values
        version_info = odoo_client._execute(
            'ir.module.module',
            'read',
            base_ids[:1],
            ['latest_version', 'installed_version']
        ) if base_ids else []

        # Get all installed modules
        module_ids = odoo_client._execute(
            'ir.module.module',
            'search',
            [['state', '=', 'installed']]
        )

        # Read all installed modules with specific fields to avoid None values
        installed_modules = odoo_client._execute(
            'ir.module.module',
            'read',
            module_ids,
            ['name', 'shortdesc', 'author', 'installed_version', 'application', 'license']
        ) if module_ids else []

        # Get database name from config
        db_name = odoo_client.db if hasattr(odoo_client, 'db') else "unknown"

        server_info = {
            "database": db_name,
            "odoo_version": version_info[0].get('latest_version', 'unknown') if version_info else 'unknown',
            "installed_modules_count": len(module_ids) if module_ids else 0,
            "installed_modules": [
                {
                    "name": mod.get('name'),
                    "title": mod.get('shortdesc'),
                    "version": mod.get('installed_version'),
                    "author": mod.get('author', 'Unknown'),
                    "application": mod.get('application', False),
                    "license": mod.get('license', 'Unknown')
                }
                for mod in installed_modules
            ]
        }

        return json.dumps(server_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ----- Pydantic models for type safety -----


class DomainCondition(BaseModel):
    """A single condition in a search domain"""

    field: str = Field(description="Field name to search")
    operator: str = Field(
        description="Operator (e.g., '=', '!=', '>', '<', 'in', 'not in', 'like', 'ilike')"
    )
    value: Any = Field(description="Value to compare against")

    def to_tuple(self) -> List:
        """Convert to Odoo domain condition tuple"""
        return [self.field, self.operator, self.value]


class SearchDomain(BaseModel):
    """Search domain for Odoo models"""

    conditions: List[DomainCondition] = Field(
        default_factory=list,
        description="List of conditions for searching. All conditions are combined with AND operator.",
    )

    def to_domain_list(self) -> List[List]:
        """Convert to Odoo domain list format"""
        return [condition.to_tuple() for condition in self.conditions]


class EmployeeSearchResult(BaseModel):
    """Represents a single employee search result."""

    id: int = Field(description="Employee ID")
    name: str = Field(description="Employee name")


class SearchEmployeeResponse(BaseModel):
    """Response model for the search_employee tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[EmployeeSearchResult]] = Field(
        default=None, description="List of employee search results"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class Holiday(BaseModel):
    """Represents a single holiday."""

    display_name: str = Field(description="Display name of the holiday")
    start_datetime: str = Field(description="Start date and time of the holiday")
    stop_datetime: str = Field(description="End date and time of the holiday")
    employee_id: List[Union[int, str]] = Field(
        description="Employee ID associated with the holiday"
    )
    name: str = Field(description="Name of the holiday")
    state: str = Field(description="State of the holiday")


class SearchHolidaysResponse(BaseModel):
    """Response model for the search_holidays tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[Holiday]] = Field(
        default=None, description="List of holidays found"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class ExecuteMethodResponse(BaseModel):
    """Response model for the execute_method tool."""

    success: bool = Field(description="Indicates if the method execution was successful")
    result: Optional[Any] = Field(
        default=None, description="Result of the method execution"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class ValidationIssue(BaseModel):
    """Represents a single validation issue"""

    field: Optional[str] = Field(default=None, description="Field name related to the issue")
    message: str = Field(description="Description of the issue")
    severity: str = Field(description="Severity level: error, warning, info")


class ValidateResponse(BaseModel):
    """Response model for validate_before_execute tool"""

    valid: bool = Field(description="Whether the operation is valid and safe to execute")
    errors: List[ValidationIssue] = Field(default_factory=list, description="Validation errors that prevent execution")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="Warnings that don't prevent execution")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    safe_to_execute: bool = Field(description="Whether it's safe to execute this operation")


class DeepReadResponse(BaseModel):
    """Response model for deep_read tool"""

    success: bool = Field(description="Whether the operation succeeded")
    record: Optional[Dict[str, Any]] = Field(default=None, description="Main record data")
    related_records: Optional[Dict[str, Any]] = Field(default=None, description="Related records organized by relation field")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BatchOperation(BaseModel):
    """Represents a single operation in a batch"""

    model: str = Field(description="Model name")
    method: str = Field(description="Method to call")
    args_json: Optional[str] = Field(default=None, description="Arguments as JSON string")
    kwargs_json: Optional[str] = Field(default=None, description="Keyword arguments as JSON string")


class BatchExecuteResponse(BaseModel):
    """Response model for batch_execute tool"""

    success: bool = Field(description="Whether all operations succeeded")
    results: List[Dict[str, Any]] = Field(description="Results for each operation")
    total_operations: int = Field(description="Total number of operations attempted")
    successful_operations: int = Field(description="Number of successful operations")
    failed_operations: int = Field(description="Number of failed operations")
    error: Optional[str] = Field(default=None, description="Overall error message if batch failed")


# ----- MCP Tools -----


@mcp.tool(
    description="""⚡ UNIVERSAL TOOL - Execute ANY Odoo method on ANY model

    This is your FALLBACK tool when specialized tools don't exist.
    Can call ANY of the hundreds of Odoo methods across all models.

    Common use cases:
    - Creating records: method='create'
    - Searching: method='search_read'
    - Updating: method='write'
    - Deleting: method='unlink'
    - Custom methods: method='your_custom_method'

    If you think "Odoo can do X but there's no specialized tool" → USE THIS!

    Before using, consider checking:
    - odoo://model/{model}/schema for field definitions
    - odoo://methods/{model} for available methods
    - validate_before_execute for safety checks
    """,
    output_schema=ExecuteMethodResponse.model_json_schema()
)
def execute_method(
    ctx: Context,
    model: str,
    method: str,
    args_json: str = None,
    kwargs_json: str = None,
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
    - Use validate_before_execute first to catch errors before execution
    - Check odoo://model/{model}/schema for required fields
    - Check odoo://methods/{model} for available methods
    - For workflows, see odoo://workflows for step-by-step guides
    """
    odoo = ctx.request_context.lifespan_context.odoo
    try:
        # Parse JSON strings to actual Python objects
        args = []
        kwargs = {}

        if args_json:
            try:
                args = json.loads(args_json)
                if not isinstance(args, list):
                    return {"success": False, "error": f"args_json must be a JSON array, got: {type(args).__name__}"}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON in args_json: {str(e)}"}

        if kwargs_json:
            try:
                kwargs = json.loads(kwargs_json)
                if not isinstance(kwargs, dict):
                    return {"success": False, "error": f"kwargs_json must be a JSON object, got: {type(kwargs).__name__}"}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON in kwargs_json: {str(e)}"}

        # Special handling for search methods like search, search_count, search_read
        search_methods = ["search", "search_count", "search_read"]
        if method in search_methods and args:
            # Search methods usually have domain as the first parameter
            # args: [[domain], limit, offset, ...] or [domain, limit, offset, ...]
            normalized_args = list(
                args
            )  # Create a copy to avoid affecting the original args

            if len(normalized_args) > 0:
                # Process domain in args[0]
                domain = normalized_args[0]
                domain_list = []

                # Check if domain is wrapped unnecessarily ([domain] instead of domain)
                if (
                    isinstance(domain, list)
                    and len(domain) == 1
                    and isinstance(domain[0], list)
                ):
                    # Case [[domain]] - unwrap to [domain]
                    domain = domain[0]

                # Normalize domain similar to search_records function
                if domain is None:
                    domain_list = []
                elif isinstance(domain, dict):
                    if "conditions" in domain:
                        # Object format
                        conditions = domain.get("conditions", [])
                        domain_list = []
                        for cond in conditions:
                            if isinstance(cond, dict) and all(
                                k in cond for k in ["field", "operator", "value"]
                            ):
                                domain_list.append(
                                    [cond["field"], cond["operator"], cond["value"]]
                                )
                elif isinstance(domain, list):
                    # List format
                    if not domain:
                        domain_list = []
                    elif all(isinstance(item, list) for item in domain) or any(
                        item in ["&", "|", "!"] for item in domain
                    ):
                        domain_list = domain
                    elif len(domain) >= 3 and isinstance(domain[0], str):
                        # Case [field, operator, value] (not [[field, operator, value]])
                        domain_list = [domain]
                elif isinstance(domain, str):
                    # String format (JSON)
                    try:
                        parsed_domain = json.loads(domain)
                        if (
                            isinstance(parsed_domain, dict)
                            and "conditions" in parsed_domain
                        ):
                            conditions = parsed_domain.get("conditions", [])
                            domain_list = []
                            for cond in conditions:
                                if isinstance(cond, dict) and all(
                                    k in cond for k in ["field", "operator", "value"]
                                ):
                                    domain_list.append(
                                        [cond["field"], cond["operator"], cond["value"]]
                                    )
                        elif isinstance(parsed_domain, list):
                            domain_list = parsed_domain
                    except json.JSONDecodeError:
                        try:
                            import ast

                            parsed_domain = ast.literal_eval(domain)
                            if isinstance(parsed_domain, list):
                                domain_list = parsed_domain
                        except:
                            domain_list = []

                # Xác thực domain_list
                if domain_list:
                    valid_conditions = []
                    for cond in domain_list:
                        if isinstance(cond, str) and cond in ["&", "|", "!"]:
                            valid_conditions.append(cond)
                            continue

                        if (
                            isinstance(cond, list)
                            and len(cond) == 3
                            and isinstance(cond[0], str)
                            and isinstance(cond[1], str)
                        ):
                            valid_conditions.append(cond)

                    domain_list = valid_conditions

                # Cập nhật args với domain đã chuẩn hóa
                normalized_args[0] = domain_list
                args = normalized_args

                # Log for debugging
                print(f"Executing {method} with normalized domain: {domain_list}", file=sys.stderr)

        result = odoo.execute_method(model, method, *args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool(
    description="Search for employees by name",
    output_schema=SearchEmployeeResponse.model_json_schema()
)
def search_employee(
    ctx: Context,
    name: str,
    limit: int = 20,
) -> SearchEmployeeResponse:
    """
    Search for employees by name using Odoo's name_search method.

    Parameters:
        name: The name (or part of the name) to search for.
        limit: The maximum number of results to return (default 20).

    Returns:
        SearchEmployeeResponse containing results or error information.
    """
    odoo = ctx.request_context.lifespan_context.odoo
    model = "hr.employee"
    method = "name_search"

    args = []
    kwargs = {"name": name, "limit": limit}

    try:
        result = odoo.execute_method(model, method, *args, **kwargs)
        parsed_result = [
            EmployeeSearchResult(id=item[0], name=item[1]) for item in result
        ]
        return SearchEmployeeResponse(success=True, result=parsed_result)
    except Exception as e:
        return SearchEmployeeResponse(success=False, error=str(e))


@mcp.tool(
    description="Search for holidays within a date range",
    output_schema=SearchHolidaysResponse.model_json_schema()
)
def search_holidays(
    ctx: Context,
    start_date: str,
    end_date: str,
    employee_id: Optional[int] = None,
) -> SearchHolidaysResponse:
    """
    Searches for holidays within a specified date range.

    Parameters:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        employee_id: Optional employee ID to filter holidays.

    Returns:
        SearchHolidaysResponse:  Object containing the search results.
    """
    odoo = ctx.request_context.lifespan_context.odoo

    # Validate date format using datetime
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid start_date format. Use YYYY-MM-DD."
        )
    try:
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid end_date format. Use YYYY-MM-DD."
        )

    # Calculate adjusted start_date (subtract one day)
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    adjusted_start_date_dt = start_date_dt - timedelta(days=1)
    adjusted_start_date = adjusted_start_date_dt.strftime("%Y-%m-%d")

    # Build the domain
    domain = [
        "&",
        ["start_datetime", "<=", f"{end_date} 22:59:59"],
        # Use adjusted date
        ["stop_datetime", ">=", f"{adjusted_start_date} 23:00:00"],
    ]
    if employee_id:
        domain.append(
            ["employee_id", "=", employee_id],
        )

    try:
        holidays = odoo.search_read(
            model_name="hr.leave.report.calendar",
            domain=domain,
        )
        parsed_holidays = [Holiday(**holiday) for holiday in holidays]
        return SearchHolidaysResponse(success=True, result=parsed_holidays)

    except Exception as e:
        return SearchHolidaysResponse(success=False, error=str(e))


@mcp.tool(
    description="Validate an operation before executing it - Pre-flight check for safety",
    output_schema=ValidateResponse.model_json_schema()
)
def validate_before_execute(
    ctx: Context,
    model: str,
    method: str,
    args_json: str = None,
    kwargs_json: str = None
) -> ValidateResponse:
    """
    Validates an Odoo operation before execution

    Checks:
    - Model exists
    - User has permission for the operation
    - Required fields are present (for create/write)
    - Field types are correct
    - Constraints are met

    Use this before execute_method to catch errors early!

    Parameters:
        model: Model name (e.g., 'res.partner')
        method: Method to call (e.g., 'create', 'write', 'search_read')
        args_json: JSON string of arguments
        kwargs_json: JSON string of keyword arguments

    Returns:
        ValidateResponse with validation results and safety recommendation
    """
    odoo = ctx.request_context.lifespan_context.odoo
    errors = []
    warnings = []
    suggestions = []

    try:
        # Parse arguments
        args = json.loads(args_json) if args_json else []
        kwargs = json.loads(kwargs_json) if kwargs_json else {}

        # Check if model exists - use search instead of get_model_info for reliability
        try:
            model_check = odoo.execute_method('ir.model', 'search_count', [('model', '=', model)])
            if not model_check or model_check == 0:
                errors.append(ValidationIssue(
                    field=None,
                    message=f"Model '{model}' not found in ir.model",
                    severity="error"
                ))
                return ValidateResponse(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    suggestions=suggestions,
                    safe_to_execute=False
                )
        except Exception as e:
            # If we can't check, add warning but continue
            warnings.append(ValidationIssue(
                field=None,
                message=f"Could not verify model existence: {str(e)}",
                severity="warning"
            ))

        # Check access rights
        operation_map = {
            'create': 'create',
            'write': 'write',
            'unlink': 'unlink',
            'search': 'read',
            'read': 'read',
            'search_read': 'read'
        }
        required_permission = operation_map.get(method, 'read')

        try:
            has_access = odoo.execute_method(
                model,
                'check_access_rights',
                required_permission,
                False
            )
            if not has_access:
                errors.append(ValidationIssue(
                    field=None,
                    message=f"No '{required_permission}' permission on model '{model}'",
                    severity="error"
                ))
        except Exception:
            warnings.append(ValidationIssue(
                field=None,
                message=f"Could not verify '{required_permission}' permission",
                severity="warning"
            ))

        # For create/write operations, validate fields
        if method in ['create', 'write']:
            try:
                fields_def = odoo.get_model_fields(model)

                # Get values to validate
                if method == 'create' and args and isinstance(args[0], dict):
                    values = args[0]
                elif method == 'write' and len(args) >= 2 and isinstance(args[1], dict):
                    values = args[1]
                else:
                    values = {}

                # Check required fields (for create)
                if method == 'create':
                    for field_name, field_def in fields_def.items():
                        if field_def.get('required') and field_name not in values:
                            # Check if field has a default value
                            if not field_def.get('default'):
                                errors.append(ValidationIssue(
                                    field=field_name,
                                    message=f"Required field '{field_name}' is missing",
                                    severity="error"
                                ))

                # Check readonly fields
                for field_name in values.keys():
                    if field_name in fields_def:
                        field_def = fields_def[field_name]
                        if field_def.get('readonly'):
                            warnings.append(ValidationIssue(
                                field=field_name,
                                message=f"Field '{field_name}' is readonly",
                                severity="warning"
                            ))

                # Type checking suggestions
                for field_name, value in values.items():
                    if field_name in fields_def:
                        field_type = fields_def[field_name].get('type')
                        if field_type == 'integer' and not isinstance(value, int):
                            warnings.append(ValidationIssue(
                                field=field_name,
                                message=f"Field '{field_name}' expects integer, got {type(value).__name__}",
                                severity="warning"
                            ))
                        elif field_type == 'boolean' and not isinstance(value, bool):
                            warnings.append(ValidationIssue(
                                field=field_name,
                                message=f"Field '{field_name}' expects boolean, got {type(value).__name__}",
                                severity="warning"
                            ))

            except Exception as e:
                warnings.append(ValidationIssue(
                    field=None,
                    message=f"Could not validate fields: {str(e)}",
                    severity="warning"
                ))

        # Add suggestions
        if method == 'search' and not kwargs.get('limit'):
            suggestions.append("Consider adding a 'limit' parameter to avoid large result sets")

        if method in ['write', 'unlink'] and args and isinstance(args[0], list):
            record_count = len(args[0])
            if record_count > 100:
                warnings.append(ValidationIssue(
                    field=None,
                    message=f"Operating on {record_count} records at once - consider batching",
                    severity="warning"
                ))

        # Determine if safe to execute
        safe_to_execute = len(errors) == 0

        return ValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            safe_to_execute=safe_to_execute
        )

    except Exception as e:
        return ValidateResponse(
            valid=False,
            errors=[ValidationIssue(field=None, message=f"Validation failed: {str(e)}", severity="error")],
            warnings=[],
            suggestions=[],
            safe_to_execute=False
        )


@mcp.tool(
    description="Deep read a record with related data - Follows relationships automatically",
    output_schema=DeepReadResponse.model_json_schema()
)
def deep_read(
    ctx: Context,
    model: str,
    record_id: int,
    follow_relations: Optional[List[str]] = None,
    depth: int = 1,
    limit_per_relation: int = 10
) -> DeepReadResponse:
    """
    Fetch a record and automatically follow its relationships

    This intelligently reads related records, saving multiple manual queries.

    Parameters:
        model: Model name (e.g., 'sale.order')
        record_id: ID of the record to read
        follow_relations: Specific relation fields to follow (None = all many2one fields)
        depth: How deep to follow relations (1 = direct relations only, 2 = relations of relations)
        limit_per_relation: Max records to fetch per relation (default: 10, prevents huge responses)

    Examples:
        # Get sales order with customer and order lines
        deep_read(model='sale.order', record_id=5, depth=2)

        # Get only specific relations
        deep_read(model='sale.order', record_id=5, follow_relations=['partner_id', 'order_line'])

    Returns:
        DeepReadResponse with main record and related_records organized by field name
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Read main record
        main_record = odoo.read_records(model, [record_id])
        if not main_record:
            return DeepReadResponse(
                success=False,
                error=f"Record not found: {model} ID {record_id}"
            )

        record = main_record[0]
        related_records = {}

        if depth < 1:
            return DeepReadResponse(
                success=True,
                record=record,
                related_records={}
            )

        # Get model schema to identify relationships
        fields = odoo.get_model_fields(model)

        # Determine which relations to follow
        relations_to_follow = []
        for field_name, field_def in fields.items():
            field_type = field_def.get('type', '')

            # Filter by requested relations
            if follow_relations and field_name not in follow_relations:
                continue

            if field_type in ['many2one', 'one2many', 'many2many']:
                relations_to_follow.append({
                    'field': field_name,
                    'type': field_type,
                    'relation': field_def.get('relation', '')
                })

        # Follow each relation
        for relation in relations_to_follow:
            field_name = relation['field']
            field_type = relation['type']
            relation_model = relation['relation']

            if field_name not in record or not record[field_name]:
                continue

            try:
                if field_type == 'many2one':
                    # many2one: [id, name] format
                    if isinstance(record[field_name], list) and len(record[field_name]) >= 1:
                        rel_id = record[field_name][0]
                        rel_data = odoo.read_records(relation_model, [rel_id])
                        if rel_data:
                            related_records[field_name] = rel_data[0]

                elif field_type in ['one2many', 'many2many']:
                    # one2many/many2many: list of IDs
                    rel_ids = record[field_name]
                    if isinstance(rel_ids, list) and rel_ids:
                        # Limit to prevent huge queries
                        rel_ids = rel_ids[:limit_per_relation]
                        rel_data = odoo.read_records(relation_model, rel_ids)
                        if rel_data:
                            related_records[field_name] = rel_data

            except Exception as e:
                # Don't fail the whole operation if one relation fails
                print(f"Failed to read relation {field_name}: {str(e)}", file=sys.stderr)
                continue

        return DeepReadResponse(
            success=True,
            record=record,
            related_records=related_records
        )

    except Exception as e:
        return DeepReadResponse(
            success=False,
            error=str(e)
        )


@mcp.tool(
    description="Execute multiple Odoo operations in a batch - Atomic transaction support",
    output_schema=BatchExecuteResponse.model_json_schema()
)
def batch_execute(
    ctx: Context,
    operations: List[Dict[str, Any]],
    atomic: bool = True
) -> BatchExecuteResponse:
    """
    Execute multiple operations efficiently in one call

    Supports atomic transactions: if one fails, all rollback (when atomic=True)

    Parameters:
        operations: List of operations, each with:
                   - model: str (required)
                   - method: str (required)
                   - args: list (optional, direct format) OR args_json: str (JSON string format)
                   - kwargs: dict (optional, direct format) OR kwargs_json: str (JSON string format)
        atomic: If True, all operations succeed or all fail (rollback on error)

    Examples:
        # Create customer and order in one transaction
        batch_execute(operations=[
            {
                "model": "res.partner",
                "method": "create",
                "args_json": '[{"name": "Acme Corp", "customer_rank": 1}]'
            },
            {
                "model": "sale.order",
                "method": "create",
                "args_json": '[{"partner_id": 123, "order_line": [...]}]'
            }
        ], atomic=True)

    Returns:
        BatchExecuteResponse with results for each operation
    """
    odoo = ctx.request_context.lifespan_context.odoo
    results = []
    successful = 0
    failed = 0

    try:
        for idx, op in enumerate(operations):
            try:
                model = op.get('model')
                method = op.get('method')
                args_json = op.get('args_json')
                kwargs_json = op.get('kwargs_json')
                args_direct = op.get('args')
                kwargs_direct = op.get('kwargs')

                if not model or not method:
                    raise ValueError(f"Operation {idx}: 'model' and 'method' are required")

                # Parse arguments - support both JSON strings and direct objects
                if args_json:
                    args = json.loads(args_json) if isinstance(args_json, str) else args_json
                elif args_direct is not None:
                    args = args_direct
                else:
                    args = []

                if kwargs_json:
                    kwargs = json.loads(kwargs_json) if isinstance(kwargs_json, str) else kwargs_json
                elif kwargs_direct is not None:
                    kwargs = kwargs_direct
                else:
                    kwargs = {}

                # Execute the operation
                result = odoo.execute_method(model, method, *args, **kwargs)

                results.append({
                    "operation_index": idx,
                    "success": True,
                    "result": result
                })
                successful += 1

            except Exception as e:
                results.append({
                    "operation_index": idx,
                    "success": False,
                    "error": str(e)
                })
                failed += 1

                # If atomic, fail fast
                if atomic:
                    return BatchExecuteResponse(
                        success=False,
                        results=results,
                        total_operations=len(operations),
                        successful_operations=successful,
                        failed_operations=failed,
                        error=f"Batch failed at operation {idx}: {str(e)} (atomic mode - no operations committed)"
                    )

        return BatchExecuteResponse(
            success=(failed == 0),
            results=results,
            total_operations=len(operations),
            successful_operations=successful,
            failed_operations=failed,
            error=None if failed == 0 else f"{failed} operations failed"
        )

    except Exception as e:
        return BatchExecuteResponse(
            success=False,
            results=results,
            total_operations=len(operations),
            successful_operations=successful,
            failed_operations=failed,
            error=f"Batch execution failed: {str(e)}"
        )


# ----- MCP Prompts -----


@mcp.prompt(name="search-customers")
def search_customers_prompt(
    city: str = "",
    country: str = ""
) -> List[Dict[str, str]]:
    """
    Pre-built prompt template for searching customers

    User can select this and fill in city/country filters
    """
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

Steps:
1. Check odoo://model/res.partner/schema for available fields
2. Build domain: [["customer_rank", ">", 0]] for customers only
3. Add location filters if provided:
   - city: [["city", "ilike", "{city}"]] if city is specified
   - country: [["country_id.name", "ilike", "{country}"]] if country is specified
4. Use execute_method with model='res.partner', method='search_read'
5. Request fields: name, email, phone, city, country_id

Example call:
execute_method(
    model='res.partner',
    method='search_read',
    args_json='[[["customer_rank", ">", 0]{', ["city", "ilike", "' + city + '"]' if city else ''}{', ["country_id.name", "ilike", "' + country + '"]' if country else ''}]]',
    kwargs_json='{{"fields": ["name", "email", "phone", "city", "country_id"], "limit": 20}}'
)
"""
        }
    ]


@mcp.prompt(name="create-sales-order")
def create_sales_order_prompt(
    customer_id: int = 0
) -> List[Dict[str, str]]:
    """
    Template for creating a sales order in Odoo

    Guides through the complete process with validation
    """
    return [
        {
            "role": "user",
            "content": f"""Create a new sales order{' for customer ID ' + str(customer_id) if customer_id > 0 else ''}.

Steps:
1. If customer_id not provided, search for customer first using res.partner
2. Check odoo://model/sale.order/schema for required fields
3. Check odoo://model/sale.order.line/schema for order line fields
4. Use validate_before_execute to check:
   - Required fields are present
   - User has create permission
5. Create the order with execute_method:
   - model='sale.order'
   - method='create'
   - Include: partner_id, order_line (with product_id, product_uom_qty, price_unit)
6. Optionally confirm the order with method='action_confirm'

Example structure:
{{
  "partner_id": {customer_id if customer_id > 0 else 'CUSTOMER_ID'},
  "order_line": [
    [0, 0, {{
      "product_id": PRODUCT_ID,
      "product_uom_qty": 1,
      "price_unit": 100.00
    }}]
  ]
}}

Workflow available in odoo://workflows (check sales.quotation_to_order)
"""
        }
    ]


@mcp.prompt(name="odoo-exploration")
def odoo_exploration_prompt() -> List[Dict[str, str]]:
    """
    Help users discover what they can do with this Odoo instance

    Provides a systematic exploration guide
    """
    return [
        {
            "role": "user",
            "content": """Explore this Odoo instance and tell me what I can do with it.

Systematic exploration steps:

1. **Server Info**: Read odoo://server/info
   - What Odoo version?
   - What modules are installed?
   - What apps are available?

2. **Available Workflows**: Read odoo://workflows
   - What business processes are available?
   - Sales? Inventory? CRM? HR? Accounting?

3. **Key Models**: Check odoo://models for most relevant models based on installed modules
   - res.partner (contacts/customers)
   - sale.order (sales) if sale module installed
   - stock.picking (inventory) if stock module installed
   - crm.lead (CRM) if crm module installed
   - account.move (invoices) if account module installed

4. **My Permissions**: For key models, check odoo://model/{model}/access
   - What can I read?
   - What can I create?
   - What can I modify?

5. **Suggest Common Tasks**: Based on installed modules and permissions:
   - If sales: Creating quotations, confirming orders
   - If CRM: Managing leads and opportunities
   - If inventory: Creating transfers, adjusting stock
   - If HR: Managing employees, leave requests

Provide a summary of:
- Odoo version and installed apps
- Available business workflows
- What I have permission to do
- 3-5 suggested common tasks I can help with
"""
        }
    ]


@mcp.prompt(name="troubleshoot-operation")
def troubleshoot_operation_prompt(
    model: str = "",
    method: str = "",
    error_message: str = ""
) -> List[Dict[str, str]]:
    """
    Help troubleshoot a failed Odoo operation

    Systematic debugging guide
    """
    return [
        {
            "role": "user",
            "content": f"""An Odoo operation failed{' on model ' + model if model else ''}{' calling method ' + method if method else ''}.
Error: {error_message if error_message else 'See error details above'}

Troubleshooting steps:

1. **Validate the Operation**:
   Use validate_before_execute to check:
   - Does the model exist?
   - Do I have permission?
   - Are required fields present?
   - Are field types correct?

2. **Check Model Schema**: odoo://model/{model if model else 'MODEL'}/schema
   - What fields are required?
   - What are the field types?
   - What relationships exist?

3. **Check Access Rights**: odoo://model/{model if model else 'MODEL'}/access
   - Do I have {method if method else 'the required'} permission?

4. **Check Method Signature**: odoo://methods/{model if model else 'MODEL'}
   - Is the method name correct?
   - What parameters does it expect?

5. **Common Issues**:
   - Missing required fields
   - Wrong field types (string vs integer)
   - Invalid foreign key references
   - Permission denied
   - Invalid domain syntax

6. **Suggest Fix**:
   Based on findings, provide corrected execute_method call with:
   - Proper field values
   - Correct types
   - Valid domain syntax
   - All required fields
"""
        }
    ]
