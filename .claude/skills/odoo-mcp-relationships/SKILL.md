---
name: odoo-mcp-relationships
description: Read and write relational fields in Odoo — many2one (single link), one2many (list of child records), many2many (tag-style set). Use when creating a sale.order with order lines, tagging a partner with multiple categories, adding/removing followers, replacing a set of attributes, or when writes to relational fields fail silently. Triggers on "m2o", "o2m", "m2m", "many2one", "one2many", "many2many", "relation", "tags", "followers", "order lines", "invoice lines", or any write that crosses a record boundary.
---

# Odoo MCP — Relational field writes

Relational writes use special command tuples. Getting the command wrong is the #1 cause of silent write failures.

## Many2one — single link

Just an integer ID:

```python
# On sale.order
{"partner_id": 42}

# On crm.lead
{"user_id": 7, "team_id": 2}
```

To clear a many2one: `{"partner_id": false}`.

## One2many — list of child records

The parent owns the children. Commands are tuples `(op, id, vals)` in a list:

| Command | Meaning |
|---|---|
| `[0, 0, {vals}]` | Create a new child |
| `[1, child_id, {vals}]` | Update existing child |
| `[2, child_id]` | Delete child (unlink + remove from list) |
| `[3, child_id]` | Remove from list but keep the record |
| `[4, child_id]` | Add existing child to the list |
| `[5]` | Unlink all children |
| `[6, 0, [ids]]` | Replace list with these children |

**Create sale.order with 3 lines in one call:**
```python
execute_method(
    model="sale.order",
    method="create",
    args_json='[{"partner_id": 42, "order_line": [[0, 0, {"product_id": 101, "product_uom_qty": 2}], [0, 0, {"product_id": 102, "product_uom_qty": 5}], [0, 0, {"product_id": 103, "product_uom_qty": 1}]]}]'
)
```

**Add a line to an existing order:**
```python
execute_method(
    model="sale.order",
    method="write",
    args_json='[[order_id], {"order_line": [[0, 0, {"product_id": 201, "product_uom_qty": 1}]]}]'
)
```

**Update an existing line:**
```python
execute_method(
    model="sale.order",
    method="write",
    args_json='[[order_id], {"order_line": [[1, line_id, {"product_uom_qty": 10}]]}]'
)
```

**Remove a line (delete it):**
```python
args_json='[[order_id], {"order_line": [[2, line_id]]}]'
```

## Many2many — tag-style sets

Same commands as one2many but semantically different (no "owner"). Most common:

**Add tags (command 4):**
```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {"category_id": [[4, 5]]}]'  # add tag id 5
)
```

**Remove tags (command 3 — unlinks, doesn't delete):**
```python
args_json='[[42], {"category_id": [[3, 5]]}]'
```

**Replace all tags (command 6 — most common for "set these tags"):**
```python
args_json='[[42], {"category_id": [[6, 0, [5, 10, 17]]]}]'  # partner now has exactly these 3 tags
```

## Reading relational fields

**Many2one returns `[id, display_name]`:**
```python
# result["partner_id"] = [42, "Acme Inc"]
```

**One2many and many2many return `[id, id, id, ...]` (just IDs):**
```python
# result["order_line"] = [101, 102, 103]
# result["category_id"] = [5, 10, 17]
```

To get full child records, do a second search:
```python
order = execute_method(model="sale.order", method="read", args_json='[[42], ["order_line"]]')["result"][0]
lines = execute_method(model="sale.order.line", method="read", args_json=f'[{order["order_line"]}, ["product_id", "product_uom_qty"]]')["result"]
```

## Dotted field access (read-only)

In domains and `fields` lists, you can traverse many2one and one2many:

```python
# Orders where customer is in France
args_json='[[["partner_id.country_id.code", "=", "FR"]]]'

# Fetch related data inline
kwargs_json='{"fields": ["name", "partner_id.email", "user_id.name"]}'
```

Dotted paths work one level at a time: `partner_id.country_id.code` reads the country code of the partner of the order.

## Searching many2many (gotcha)

Many2many fields **require `in` with a list**, never `=` with a scalar:

```python
# WRONG — returns nothing, no error
args_json='[[["category_id", "=", 5]]]'

# CORRECT
args_json='[[["category_id", "in", [5]]]]'
```

This is the #1 Learned Pattern in the cookbook. If a m2m search returns empty, check the operator first.

## Followers and activities

**Subscribe partners as followers (via `message_subscribe`):**
```python
execute_method(
    model="crm.lead",
    method="message_subscribe",
    args_json='[[lead_id]]',
    kwargs_json='{"partner_ids": [42, 43]}'
)
```

**Add an activity (reminder/todo):**
```python
execute_method(
    model="mail.activity",
    method="create",
    args_json='[{"res_model": "crm.lead", "res_id": lead_id, "activity_type_id": 1, "summary": "Call back", "date_deadline": "2026-04-25", "user_id": 7}]'
)
```

## Debugging silent failures

1. Check the command tuple — `[[0, 0, {vals}]]` not `[0, 0, {vals}]` (commands live inside a list)
2. Check field is actually m2m/o2m — `odoo://model/{model}/schema`
3. For `[4, id]` — id must exist, or Odoo throws IntegrityError (not silent)
4. For `[6, 0, [ids]]` — the `0` in position 2 is the new-record placeholder, not optional
