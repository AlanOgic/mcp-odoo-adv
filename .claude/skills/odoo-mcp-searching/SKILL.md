---
name: odoo-mcp-searching
description: Build Odoo domain filters and search queries via MCP execute_method. Use when searching/reading records from Odoo models (res.partner, crm.lead, sale.order, mail.message, etc.), constructing complex domains with AND/OR/NOT operators, or when a search returns wrong results and you need to fix the filter. Triggers on mentions of "search", "filter", "find records", "domain", "search_read", "search_count", or any Odoo model name in a read context.
---

# Odoo MCP — Searching & reading records

Use `execute_method` on the `odoo-joliemachine` MCP server (tool `mcp__odoo-joliemachine__execute_method`). Always pass `args_json` and `kwargs_json` as JSON strings, never Python dicts.

## Universal shape

```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',     # domain (list of triples)
    kwargs_json='{"fields": ["name", "email"], "limit": 50}'
)
```

Response envelope:
```python
{"success": True, "result": [...]} | {"success": False, "error": "..."}
```

Always check `success` before touching `result`.

## Method selection

| Goal | Method |
|---|---|
| Get matching IDs only (cheap) | `search` |
| Get records + fields in one call | `search_read` (preferred for most reads) |
| Count without fetching | `search_count` |
| Read specific records by ID | `read` (args_json='[[ids], [fields]]') |
| Autocomplete by name | `name_search` |

## Domain construction

A domain is a list of triples `[field, operator, value]` plus optional logic operators `"&"` (AND, default), `"|"` (OR), `"!"` (NOT) in **prefix notation**.

**AND (default, no operator needed):**
```python
'[[["customer_rank", ">", 0], ["country_id", "=", 75]]]'
```

**OR — use `"|"` prefix before the two conditions it joins:**
```python
'[[["|", ["city", "=", "Paris"], ["city", "=", "Lyon"]]]]'
```

**Nested logic — two `"|"` followed by conditions = OR of 3 terms:**
```python
'[[["|", "|", ["state", "=", "draft"], ["state", "=", "sent"], ["state", "=", "done"]]]]'
```

## Operators

| Operator | Use |
|---|---|
| `=`, `!=`, `>`, `>=`, `<`, `<=` | Scalar comparisons |
| `in`, `not in` | Against lists — **required for many2many fields** |
| `like`, `ilike` | Substring match (ilike is case-insensitive) |
| `=like`, `=ilike` | Pattern with `%` wildcard |
| `child_of`, `parent_of` | Hierarchical (parent_id trees) |

## Many2many gotcha

Never use `=` on a many2many field. Always use `in` with a list, even for a single ID:

```python
# WRONG — silent empty result
'[[["category_id", "=", 5]]]'

# CORRECT
'[[["category_id", "in", [5]]]]'
```

## Efficient reads

Always scope with `fields` to avoid pulling every column:

```python
kwargs_json='{"fields": ["name", "email", "phone"], "limit": 100}'
```

Smart-limit auto-applies `limit=100` if you forget — don't rely on it as documentation. Be explicit.

## Common recipes

**Find customers in a country:**
```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0], ["country_id", "=", 75]]]',
    kwargs_json='{"fields": ["name", "email"], "limit": 100}'
)
```

**Leads modified in the last 7 days:**
```python
execute_method(
    model="crm.lead",
    method="search_read",
    args_json='[[["write_date", ">=", "2026-04-12"]]]',
    kwargs_json='{"fields": ["name", "stage_id", "expected_revenue"], "order": "write_date desc", "limit": 50}'
)
```

**Draft or sent sale orders for a partner:**
```python
execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[["partner_id", "=", 42], "|", ["state", "=", "draft"], ["state", "=", "sent"]]]',
    kwargs_json='{"fields": ["name", "amount_total", "state"]}'
)
```

**Traverse relations with dotted fields:**
```python
# Orders from customers in Belgium
execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[["partner_id.country_id.code", "=", "BE"]]]',
    kwargs_json='{"fields": ["name", "partner_id", "amount_total"]}'
)
```

## When a search returns nothing

1. Check the field exists — `resource odoo://model/{model}/schema`
2. Many2many with `=`? → swap to `in`
3. Date string format? → `"YYYY-MM-DD"` or `"YYYY-MM-DD HH:MM:SS"`
4. Archived records excluded by default — add `["active", "in", [true, false]]` or use `.with_context({"active_test": False})`
5. Check permissions — `odoo://model/{model}/access`

## When to stop guessing

After the first failed search, read `odoo://cookbook/patterns` for recipes covering non-obvious domain shapes. After ≥4 failures on the same problem, document the resolution via `add_cookbook_pattern`.
