---
name: odoo-mcp-real-world
description: Recurring end-to-end recipes for HR (employees, time off), CRM (pending responses, pipeline analysis), inventory (products with stock, warehouse moves), accounting (invoices by period), and users/groups. Use when asked to pull a report, audit, or cross-model overview rather than a single CRUD action. Triggers on "employees without X", "time off pending", "invoices this quarter", "stock level", "pending CRM responses", "project tasks", "permissions audit", or any request that joins 2-3 Odoo models to answer a business question.
---

# Odoo MCP — Real-world recipes

Recipes for cross-model questions that occur frequently enough to memorize the shape.

## HR

**Employees by department with manager:**
```python
execute_method(
    model="hr.employee",
    method="search_read",
    args_json='[[["active", "=", true], ["department_id", "=", dept_id]]]',
    kwargs_json='{"fields": ["name", "job_title", "work_email", "parent_id"]}'
)
```

**Pending time-off requests (HR to approve):**
```python
execute_method(
    model="hr.leave",
    method="search_read",
    args_json='[[["state", "=", "confirm"]]]',
    kwargs_json='{"fields": ["employee_id", "holiday_status_id", "number_of_days", "date_from", "date_to"], "order": "date_from asc"}'
)
```

**Currently off (today):**
```python
today = "2026-04-19"
execute_method(
    model="hr.leave",
    method="search_read",
    args_json=f'[[["state", "=", "validate"], ["date_from", "<=", "{today}"], ["date_to", ">=", "{today}"]]]',
    kwargs_json='{"fields": ["employee_id", "holiday_status_id", "date_from", "date_to"]}'
)
```

## CRM — pending responses

Find leads where the last message was from the customer (we owe a response):

```python
# 1. Get recently-active leads
leads = execute_method(
    model="crm.lead",
    method="search_read",
    args_json='[[["active", "=", true], ["type", "=", "opportunity"]]]',
    kwargs_json='{"fields": ["name", "partner_id", "user_id"], "order": "write_date desc", "limit": 100}'
)["result"]

# 2. For each, get last message
for lead in leads:
    msgs = execute_method(
        model="mail.message",
        method="search_read",
        args_json=f'[[["model", "=", "crm.lead"], ["res_id", "=", {lead["id"]}], ["message_type", "=", "email"]]]',
        kwargs_json='{"fields": ["author_id", "email_from", "date"], "order": "date desc", "limit": 1}'
    )["result"]
    # If author_id matches partner_id → customer's turn to respond
```

**Better** — use `read_group` on `mail.message` for a bulk answer. See the pending-responses recipe in COOKBOOK.

## Inventory

**Products with current stock level:**
```python
execute_method(
    model="product.product",
    method="search_read",
    args_json='[[["type", "=", "product"], ["active", "=", true]]]',
    kwargs_json='{"fields": ["name", "default_code", "qty_available", "virtual_available", "list_price"], "limit": 500}'
)
# qty_available = on hand
# virtual_available = forecast (on hand + incoming − outgoing)
```

**Stock per warehouse for one product:**
```python
execute_method(
    model="stock.quant",
    method="search_read",
    args_json='[[["product_id", "=", product_id], ["location_id.usage", "=", "internal"]]]',
    kwargs_json='{"fields": ["location_id", "quantity", "reserved_quantity"]}'
)
```

**Reorder candidates (below reorder rule):**
```python
execute_method(
    model="stock.warehouse.orderpoint",
    method="search_read",
    args_json='[[["qty_to_order", ">", 0]]]',
    kwargs_json='{"fields": ["product_id", "product_min_qty", "product_max_qty", "qty_to_order"]}'
)
```

## Accounting

**Unpaid invoices past due date:**
```python
today = "2026-04-19"
execute_method(
    model="account.move",
    method="search_read",
    args_json=f'[[["move_type", "=", "out_invoice"], ["state", "=", "posted"], ["payment_state", "in", ["not_paid", "partial"]], ["invoice_date_due", "<", "{today}"]]]',
    kwargs_json='{"fields": ["name", "partner_id", "amount_total", "amount_residual", "invoice_date_due"], "order": "invoice_date_due asc"}'
)
```

**Revenue by customer (this quarter):**
```python
execute_method(
    model="account.move",
    method="read_group",
    args_json='[[["move_type", "=", "out_invoice"], ["state", "=", "posted"], ["invoice_date", ">=", "2026-01-01"], ["invoice_date", "<=", "2026-03-31"]], ["amount_untaxed_signed:sum"], ["partner_id"]]'
)
```

**Cash flow — payments in/out this month:**
```python
execute_method(
    model="account.payment",
    method="read_group",
    args_json='[[["state", "=", "posted"], ["date", ">=", "2026-04-01"]], ["amount:sum"], ["payment_type"]]'
)
```

## Projects

**Tasks per project with current assignee:**
```python
execute_method(
    model="project.task",
    method="search_read",
    args_json=f'[[["project_id", "=", {project_id}], ["stage_id.fold", "=", false]]]',
    kwargs_json='{"fields": ["name", "user_ids", "stage_id", "date_deadline"], "order": "date_deadline asc"}'
)
```

**Tasks blocked (kanban_state):**
```python
execute_method(
    model="project.task",
    method="search_read",
    args_json='[[["kanban_state", "=", "blocked"]]]',
    kwargs_json='{"fields": ["name", "project_id", "user_ids"]}'
)
```

## Users & groups

**Who has admin access:**
```python
execute_method(
    model="res.users",
    method="search_read",
    args_json='[[["groups_id.name", "=", "Settings"], ["active", "=", true]]]',
    kwargs_json='{"fields": ["name", "login"]}'
)
```

**Users by security group:**
```python
execute_method(
    model="res.groups",
    method="read",
    args_json='[[group_id], ["name", "users"]]'
)
# Then read the user records by id
```

## Multi-company awareness

All of these recipes respect the calling user's `allowed_company_ids`. If results look short:

```python
kwargs_json='{"context": {"allowed_company_ids": [1, 2, 3]}, "fields": [...]}'
```

Check which companies the MCP user has access to:
```python
execute_method(model="res.users", method="read", args_json='[[uid], ["company_id", "company_ids"]]')
```

## Pro tips

- **`read_group` over loops**: whenever you're aggregating, `read_group` is dramatically faster
- **Index fields in domains**: `date`, `state`, `partner_id`, `company_id` are indexed; full-text `name` lookups with `ilike` are slower
- **`fields_get` for discovery**: `execute_method(model=..., method="fields_get", args_json='[]')` returns the full field map with types
