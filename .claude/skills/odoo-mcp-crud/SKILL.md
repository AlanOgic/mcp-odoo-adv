---
name: odoo-mcp-crud
description: Create, update, and delete Odoo records via MCP execute_method. Use when adding new records (res.partner, crm.lead, sale.order, product.product, account.move, etc.), updating fields on existing records, bulk-updating via write, archiving, or deleting (unlink). Triggers on "create record", "add customer", "update field", "write to", "archive", "delete", "unlink", "bulk update", or any operation that mutates Odoo state.
---

# Odoo MCP — Create, update, delete

## Create one record

```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[{"name": "Acme Inc", "email": "hello@acme.com", "customer_rank": 1}]'
)
# result = new record id (int)
```

`args_json` outer list wraps the single-vals dict (Odoo convention).

## Create multiple records (efficient)

Pass a list of dicts — one DB transaction, one call:

```python
execute_method(
    model="res.partner",
    method="create",
    args_json='[[{"name": "A"}, {"name": "B"}, {"name": "C"}]]'
)
# result = [id_a, id_b, id_c]
```

## Update records (`write`)

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {"phone": "+32 495 00 00 00"}]'
)
# result = True on success
```

Two arguments in the outer list: `[ids, vals]`. `ids` is always a list, even for a single record.

**Bulk update many records with the same values:**
```python
execute_method(
    model="crm.lead",
    method="write",
    args_json='[[1, 2, 3, 4, 5], {"user_id": 7, "team_id": 2}]'
)
```

**Different values per record → loop (no native bulk with mixed vals):**
```python
for record_id, new_name in updates:
    execute_method(
        model="res.partner",
        method="write",
        args_json=f'[[{record_id}], {{"name": "{new_name}"}}]'
    )
```

Or as one sequenced call via `batch_execute` — note it is not atomic (see odoo-mcp-batch skill).

## Delete (`unlink`) — destructive

```python
execute_method(
    model="res.partner",
    method="unlink",
    args_json='[[42]]'
)
# result = True
```

`unlink` is **permanent**. Most business records (sale.order, account.move) refuse unlink after confirmation — you must cancel first, then unlink.

## Archive instead of delete (preferred)

Most models inherit `active` field. Archived records are hidden by default but recoverable:

```python
execute_method(
    model="res.partner",
    method="write",
    args_json='[[42], {"active": false}]'
)
```

To find archived records later:
```python
args_json='[[["active", "in", [true, false]]]]'
```

## Required fields — let Odoo tell you

Don't guess required fields. Try the create, read the error:

```python
# Attempt
execute_method(
    model="sale.order",
    method="create",
    args_json='[{"name": "Test"}]'
)
# Error: "partner_id: A customer is required on a sale order."
# Fix:
args_json='[{"partner_id": 42}]'
```

Error messages name the missing field. Faster than reading `odoo://model/{model}/schema` first.

## Context flags

Some creates/writes need context to skip checks or set defaults:

```python
# Create partner without triggering company-rule enforcement
execute_method(
    model="res.partner",
    method="create",
    args_json='[{"name": "Temp"}]',
    kwargs_json='{"context": {"no_create_company": true}}'
)

# Create without sending welcome email
kwargs_json='{"context": {"mail_create_nosubscribe": true, "mail_auto_subscribe_no_notify": true}}'
```

Common context keys: `default_<field>` (set default for a linked sub-record create), `active_test: false` (include archived), `lang: "fr_FR"`, `tz: "Europe/Brussels"`.

## Common gotchas

**Boolean fields** — JSON booleans, not strings: `true`/`false`, not `"true"`.

**Date/datetime fields** — strings in ISO format: `"2026-04-19"` or `"2026-04-19 14:30:00"` (UTC).

**Decimal fields** — numbers, not strings: `99.99`, not `"99.99"`.

**Selection fields** — use the technical value, not the label. Check schema for valid options.

**Computed/readonly fields** — writes silently ignored. Error is silent — the field stays unchanged.

## Quick reference

| Goal | Method | args_json shape |
|---|---|---|
| Create 1 | `create` | `[{vals}]` |
| Create N | `create` | `[[{vals1}, {vals2}, ...]]` |
| Update | `write` | `[[ids], {vals}]` |
| Read | `read` | `[[ids], [fields]]` |
| Delete | `unlink` | `[[ids]]` |
| Archive | `write` | `[[ids], {"active": false}]` |

## When a write "succeeds" but nothing changed

- Field is `readonly` or computed → Odoo silently ignored
- Field is on a company-scoped model and your user lacks access to that company
- ORM constraint (`@api.constrains`) silently blocked the change (check chatter on the record)
