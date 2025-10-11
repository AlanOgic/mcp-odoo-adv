# Odoo MCP Cookbook

**Two tools. Infinite possibilities.**

This guide shows you how to use `execute_method` and `batch_execute` to accomplish common Odoo operations.

## Installation

```bash
# install in virtual environment pipx
pipx install -e .

# Install traditionally
pip install -e .

# Run with uv, uvx, python
uv --directory /absolute/path/of/mcp-odoo-adv odoo-mcp
uvx --no-cache --directory /absolute/path/of/mcp-odoo-adv odoo-mcp
python -m odoo_mcp
python run_server.py
python run_server_sse.py
python run_server_html.py
```

## Table of Contents

- [Quick Start](#quick-start)
- [Searching & Reading](#searching--reading)
- [Creating Records](#creating-records)
- [Updating Records](#updating-records)
- [Deleting Records](#deleting-records)
- [Relationships](#relationships)
- [Workflows](#workflows)
- [Batch Operations](#batch-operations)
- [Advanced Patterns](#advanced-patterns)

---

## Quick Start

### The Universal Pattern

```python
execute_method(
    model="<odoo_model>",
    method="<odoo_method>",
    args_json='[...]',        # Positional arguments as JSON
    kwargs_json='{...}'       # Keyword arguments as JSON
)
```

### 🛡️ Smart Limits (Automatic Protection)

**To prevent returning GBs of data, smart limits are automatically applied:**

- **Default limit**: 100 records (if you don't specify)
- **Maximum limit**: 1000 records (hard cap)
- **Override**: Set `"limit": 500` in kwargs_json
- **Unlimited**: Set `"limit": 0` or `"limit": false` (will warn you!)

```python
# ✅ Good: No limit specified → automatically limited to 100
execute_method(model="mail.message", method="search_read")

# ✅ Good: Explicit limit
execute_method(model="mail.message", method="search_read",
               kwargs_json='{"limit": 50}')

# ⚠️  Warning: Requesting too much → capped at 1000
execute_method(model="mail.message", method="search_read",
               kwargs_json='{"limit": 5000}')

# ⚠️  Danger: Unlimited query (use with caution!)
execute_method(model="mail.message", method="search_read",
               kwargs_json='{"limit": 0}')
```

### Before You Start

**Always check the schema first:**
```
odoo://model/{model_name}/schema
```

This shows you:
- All available fields
- Required fields
- Field types
- Relationships

---

## Searching & Reading

### 1. Search for Records (IDs only)

```python
execute_method(
    model="res.partner",
    method="search",
    args_json='[[["is_company", "=", true]]]',
    kwargs_json='{"limit": 10}'
)
```

### 2. Search and Read (One Query)

```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{"fields": ["name", "email", "phone"], "limit": 20}'
)
```

### 3. Read Specific Records by ID

```python
execute_method(
    model="res.partner",
    method="read",
    args_json='[[1, 2, 3], ["name", "email", "country_id"]]'
)
```

### 4. Count Records

```python
execute_method(
    model="crm.lead",
    method="search_count",
    args_json='[[["stage_id.is_won", "=", false]]]'
)
```

### 5. Name Search (Autocomplete-style)

```python
execute_method(
    model="hr.employee",
    method="name_search",
    kwargs_json='{"name": "john", "limit": 10}'
)
```

### 6. Complex Domain - Multiple Conditions

```python
# AND conditions (default)
execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[
        ["date_order", ">=", "2025-01-01"],
        ["date_order", "<=", "2025-12-31"],
        ["state", "in", ["sale", "done"]]
    ]]',
    kwargs_json='{"fields": ["name", "partner_id", "amount_total"]}'
)
```

### 7. Complex Domain - OR Logic

```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[
        "|",
        ["city", "=", "Paris"],
        ["city", "=", "Lyon"]
    ]]',
    kwargs_json='{"fields": ["name", "city"]}'
)
```

### 8. Complex Domain - Nested Conditions

```python
# (city=Paris OR city=Lyon) AND customer_rank>0
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[
        "&",
        "|",
        ["city", "=", "Paris"],
        ["city", "=", "Lyon"],
        ["customer_rank", ">", 0]
    ]]'
)
```

### 9. Search with Related Field

```python
execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[["partner_id.country_id.code", "=", "US"]]]',
    kwargs_json='{"fields": ["name", "partner_id"]}'
)
```

### 10. Get Field Definitions

```python
execute_method(
    model="product.product",
    method="fields_get",
    kwargs_json='{"allfields": ["name", "list_price", "type"]}'
)
```

---

## Efficient Querying Patterns

### 11. Pagination for Large Datasets

```python
# Page 1 (records 0-99)
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 100, "offset": 0, "order": "date desc"}'
)

# Page 2 (records 100-199)
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 100, "offset": 100, "order": "date desc"}'
)

# Page 3 (records 200-299)
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 100, "offset": 200, "order": "date desc"}'
)
```

### 12. Count Before Fetching (Good Practice)

```python
# First, count how many records match
execute_method(
    model="mail.message",
    method="search_count",
    args_json='[[["model", "=", "crm.lead"]]]'
)
# Returns: 5847 messages

# Then fetch in manageable chunks
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[["model", "=", "crm.lead"]]]',
    kwargs_json='{"limit": 100, "fields": ["date", "author_id", "subject"]}'
)
```

### 13. Fetch Only What You Need (Specify Fields!)

```python
# ❌ BAD: Fetching ALL fields (slow, huge data)
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[["model", "=", "crm.lead"]]]'
)

# ✅ GOOD: Fetch only specific fields
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[["model", "=", "crm.lead"]]]',
    kwargs_json='{"fields": ["id", "date", "author_id", "subject"], "limit": 100}'
)
```

### 14. Filter Aggressively (Use Domains!)

```python
# ❌ BAD: Fetching all messages, then filtering in code
execute_method(
    model="mail.message",
    method="search_read",
    kwargs_json='{"limit": 1000}'
)
# Then filter for recent messages in Python → SLOW!

# ✅ GOOD: Let Odoo filter on the database side
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[
        ["model", "=", "crm.lead"],
        ["date", ">=", "2025-01-01"],
        ["message_type", "=", "email"]
    ]]',
    kwargs_json='{"fields": ["date", "subject", "author_id"], "limit": 100}'
)
```

### 15. Get IDs First, Then Fetch Details

```python
# Strategy: Get IDs first (fast), then fetch only what you need

# Step 1: Get IDs matching criteria
execute_method(
    model="mail.message",
    method="search",
    args_json='[[
        ["model", "=", "crm.lead"],
        ["date", ">=", "2025-01-01"]
    ]]',
    kwargs_json='{"limit": 100}'
)
# Returns: [12345, 12346, 12347, ...]

# Step 2: Fetch only specific fields for those IDs
execute_method(
    model="mail.message",
    method="read",
    args_json='[[12345, 12346, 12347], ["date", "subject", "body"]]'
)
```

---

## Creating Records

### 16. Create a Simple Record

```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[{
        "name": "Acme Corporation",
        "email": "contact@acme.com",
        "customer_rank": 1
    }]'
)
```

### 17. Create with Many2one Relation

```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[{
        "name": "John Doe",
        "country_id": 75,  # France
        "email": "john@example.com"
    }]'
)
```

### 18. Create with One2many (Order + Lines)

```python
execute_method(
    model="sale.order",
    method="create",
    args_json='[{
        "partner_id": 8,
        "order_line": [
            [0, 0, {
                "product_id": 5,
                "product_uom_qty": 2,
                "price_unit": 50.00
            }],
            [0, 0, {
                "product_id": 12,
                "product_uom_qty": 1,
                "price_unit": 100.00
            }]
        ]
    }]'
)
```

### 19. Create Multiple Records at Once

```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[
        {"name": "Customer 1", "email": "c1@example.com"},
        {"name": "Customer 2", "email": "c2@example.com"},
        {"name": "Customer 3", "email": "c3@example.com"}
    ]'
)
```

---

## Updating Records

### 20. Update Single Field

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[7], {"phone": "+33 1 23 45 67 89"}]'
)
```

### 21. Update Multiple Records

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[1, 2, 3], {"active": true}]'
)
```

### 22. Update Multiple Fields

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {
        "phone": "+1 555 1234",
        "mobile": "+1 555 5678",
        "email": "updated@example.com",
        "website": "https://example.com"
    }]'
)
```

### 23. Update with Related Records

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[15], {
        "category_id": [[6, 0, [2, 5, 8]]]  # Replace tags with IDs 2, 5, 8
    }]'
)
```

---

## Deleting Records

### 24. Delete Records

```python
execute_method(
    model="res.partner",
    method="unlink",
    args_json='[[123, 124, 125]]'
)
```

### 25. Archive Instead of Delete

```python
# Safer: archive records instead of deleting
execute_method(
    model="res.partner",
    method="write",
    args_json='[[123], {"active": false}]'
)
```

---

## Relationships

### 26. Read Record with Relations

```python
# First, read the main record
execute_method(
    model="sale.order",
    method="read",
    args_json='[[5], ["name", "partner_id", "order_line"]]'
)
# Returns: partner_id: [8, "Customer Name"], order_line: [101, 102, 103]

# Then read related records if needed
execute_method(
    model="sale.order.line",
    method="read",
    args_json='[[101, 102, 103], ["product_id", "product_uom_qty", "price_unit"]]'
)
```

### 27. Search Through Relations

```python
# Find sales orders for customers in France
execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[["partner_id.country_id.code", "=", "FR"]]]',
    kwargs_json='{"fields": ["name", "partner_id", "amount_total"]}'
)
```

### 28. Add Many2many Relations

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {
        "category_id": [[4, 5]]  # Add tag ID 5
    }]'
)
```

### 29. Remove Many2many Relations

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {
        "category_id": [[3, 5]]  # Remove tag ID 5
    }]'
)
```

### 30. Replace All Many2many Relations

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {
        "category_id": [[6, 0, [2, 5, 8]]]  # Replace with tags 2, 5, 8
    }]'
)
```

---

## Workflows

### 31. Confirm Sales Order

```python
execute_method(
    model="sale.order",
    method="action_confirm",
    args_json='[[5]]'  # Order ID
)
```

### 32. Post Invoice

```python
execute_method(
    model="account.move",
    method="action_post",
    args_json='[[123]]'  # Invoice ID
)
```

### 33. Validate Stock Picking

```python
execute_method(
    model="stock.picking",
    method="button_validate",
    args_json='[[87]]'
)
```

### 34. Mark CRM Lead as Won

```python
execute_method(
    model="crm.lead",
    method="action_set_won",
    args_json='[[42]]'
)
```

### 35. Convert Lead to Opportunity

```python
execute_method(
    model="crm.lead",
    method="convert_opportunity",
    args_json='[[15]]'
)
```

---

## Batch Operations

### 36. Create Customer + Sales Order (Atomic)

```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "create",
            "args_json": '[{"name": "New Customer", "email": "new@customer.com"}]'
        },
        {
            "model": "sale.order",
            "method": "create",
            "args_json": '[{"partner_id": 8, "order_line": [[0, 0, {"product_id": 5, "product_uom_qty": 1}]]}]'
        }
    ],
    atomic=True
)
```

### 37. Update Multiple Models

```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "write",
            "args_json": '[[1], {"phone": "+123"}]'
        },
        {
            "model": "crm.lead",
            "method": "write",
            "args_json": '[[42], {"priority": "high"}]'
        },
        {
            "model": "sale.order",
            "method": "action_confirm",
            "args_json": '[[5]]'
        }
    ],
    atomic=False  # Continue even if one fails
)
```

### 38. Batch Create Many Records

```python
batch_execute(
    operations=[
        {
            "model": "res.partner",
            "method": "create",
            "args_json": f'[{{"name": "Partner {i}", "email": "p{i}@example.com"}}]'
        }
        for i in range(1, 51)  # Create 50 partners
    ],
    atomic=False
)
```

---

## Advanced Patterns

### 39. Search Employees by Name

```python
execute_method(
    model="hr.employee",
    method="search_read",
    args_json='[[["name", "ilike", "alan"]]]',
    kwargs_json='{"fields": ["name", "job_id", "department_id"], "limit": 20}'
)
```

### 40. Time Off / Holiday Requests

```python
execute_method(
    model="hr.leave",
    method="search_read",
    args_json='[[
        ["employee_id", "=", 1],
        ["date_from", ">=", "2025-01-01"],
        ["date_to", "<=", "2025-12-31"]
    ]]',
    kwargs_json='{"fields": ["employee_id", "holiday_status_id", "date_from", "date_to", "state"]}'
)
```

### 41. Find Pending CRM Messages

```python
# 1. Find my leads
execute_method(
    model="crm.lead",
    method="search_read",
    args_json='[[["user_id", "=", uid], ["active", "=", true]]]',
    kwargs_json='{"fields": ["id", "name"], "limit": 20}'
)

# 2. For each lead, check messages
execute_method(
    model="mail.message",
    method="search_read",
    args_json='[[
        ["model", "=", "crm.lead"],
        ["res_id", "=", 42],
        ["message_type", "in", ["email", "comment"]]
    ]]',
    kwargs_json='{"fields": ["date", "author_id", "body"], "order": "date desc"}'
)
```

### 42. Products with Stock Levels

```python
execute_method(
    model="product.product",
    method="search_read",
    args_json='[[["type", "=", "product"]]]',
    kwargs_json='{"fields": ["name", "list_price", "qty_available", "virtual_available"]}'
)
```

### 43. Invoices by Date Range

```python
execute_method(
    model="account.move",
    method="search_read",
    args_json='[[
        ["move_type", "=", "out_invoice"],
        ["invoice_date", ">=", "2025-01-01"],
        ["invoice_date", "<=", "2025-03-31"],
        ["state", "=", "posted"]
    ]]',
    kwargs_json='{"fields": ["name", "partner_id", "invoice_date", "amount_total"]}'
)
```

### 44. Projects and Tasks

```python
execute_method(
    model="project.task",
    method="search_read",
    args_json='[[
        ["project_id", "=", 5],
        ["stage_id.fold", "=", false]  # Active stages only
    ]]',
    kwargs_json='{"fields": ["name", "user_ids", "date_deadline", "stage_id"]}'
)
```

### 45. Users and Groups

```python
execute_method(
    model="res.users",
    method="search_read",
    args_json='[[["active", "=", true]]]',
    kwargs_json='{"fields": ["name", "login", "groups_id"]}'
)
```

---

## Domain Operators Reference

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `["country_id", "=", 75]` |
| `!=` | Not equal | `["active", "!=", false]` |
| `>` | Greater than | `["date_order", ">", "2025-01-01"]` |
| `>=` | Greater or equal | `["amount_total", ">=", 1000]` |
| `<` | Less than | `["create_date", "<", "2025-06-01"]` |
| `<=` | Less or equal | `["priority", "<=", 5]` |
| `like` | Case-sensitive match | `["name", "like", "Corp"]` |
| `ilike` | Case-insensitive match | `["email", "ilike", "@example.com"]` |
| `in` | In list | `["state", "in", ["draft", "sent"]]` |
| `not in` | Not in list | `["stage_id", "not in", [1, 2, 3]]` |
| `=like` | Pattern match | `["ref", "=like", "SO%"]` |
| `=ilike` | Pattern match (case-insensitive) | `["name", "=ilike", "acme%"]` |

---

## Many2one / One2many / Many2many Commands

### Many2one
```python
"partner_id": 8  # Link to partner ID 8
```

### One2many / Many2many Commands
```python
[0, 0, {...}]         # Create new record
[1, id, {...}]        # Update existing record
[2, id]               # Delete record (remove + delete)
[3, id]               # Unlink record (remove, don't delete)
[4, id]               # Link existing record
[5]                   # Unlink all
[6, 0, [ids]]         # Replace with list of IDs
```

---

## Error Messages are Your Friend

Odoo provides excellent error messages. No validation layer needed!

### Example 1: Missing Required Field
```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[{"email": "test@example.com"}]'
)
# Error: "The following fields are invalid: Name"
# ✅ Clear! Add "name" field.
```

### Example 2: Wrong Field Type
```python
execute_method(
    model="product.product",
    method="create",
    args_json='[{"name": "Product", "list_price": "invalid"}]'
)
# Error: "field 'list_price': expected a number, got 'invalid'"
# ✅ Clear! Use a number instead.
```

### Example 3: Invalid Domain
```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["invalid_field", "=", "value"]]]'
)
# Error: "Invalid field 'invalid_field' in domain"
# ✅ Clear! Check schema for valid fields.
```

---

## Pro Tips

### 1. Always Check Schema First
```
odoo://model/{model}/schema
```

### 2. Use Resources for Discovery
- `odoo://models` - All available models
- `odoo://workflows` - Business workflows
- `odoo://methods/{model}` - Available methods
- `odoo://server/info` - Odoo version & modules

### 3. Start Simple, Then Add
```python
# ✅ Good: Simple first
execute_method(model="res.partner", method="search_read", args_json='[]')

# Then add filters
execute_method(model="res.partner", method="search_read",
               args_json='[[["customer_rank", ">", 0]]]')

# Then add fields
execute_method(model="res.partner", method="search_read",
               args_json='[[["customer_rank", ">", 0]]]',
               kwargs_json='{"fields": ["name", "email"]}')
```

### 4. Use batch_execute for Atomic Operations
```python
# ✅ Both succeed or both fail
batch_execute(operations=[...], atomic=True)
```

### 5. Limit Your Queries
```python
# ✅ Always use limits for large datasets
kwargs_json='{"limit": 100}'
```

---

## Need More Help?

1. **Check the schema**: `odoo://model/{model}/schema`
2. **Check available methods**: `odoo://methods/{model}`
3. **Read Odoo's error message** - they're usually spot-on!
4. **Use Odoo documentation**: https://www.odoo.com/documentation/

---

**Remember**: You have the full Odoo API at your fingertips. These two tools can do anything Odoo can do. 🚀
