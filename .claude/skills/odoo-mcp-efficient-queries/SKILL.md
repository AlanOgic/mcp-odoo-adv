---
name: odoo-mcp-efficient-queries
description: Paginate, scope fields, and count-before-fetch when working with Odoo models that hold lots of data (mail.message, stock.move.line, account.move.line, sale.order.line, ir.attachment, res.partner across multi-company). Use when building a report, syncing data, iterating through all records of a model, or when a query times out / hits the smart-limit cap (1000 records). Triggers on "pagination", "offset", "large dataset", "count first", "timeout", or any loop that fetches "all" records.
---

# Odoo MCP — Efficient querying

The smart-limit system auto-applies `limit=100` when you forget, and caps at `MAX_LIMIT=1000`. If you need more than 1000 records, you must paginate.

## Always specify `fields`

Without `fields`, Odoo returns every column of every record — including huge text blobs (`description`, `body`, `binary` attachments) and computed fields that trigger additional DB queries. Cost explodes:

```python
# BAD — returns ~200 fields per record
execute_method(model="res.partner", method="search_read", args_json='[]')

# GOOD — only what you need
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[]',
    kwargs_json='{"fields": ["name", "email"], "limit": 500}'
)
```

## Count before fetching

If you might be about to fetch a massive set, count first:

```python
count = execute_method(
    model="mail.message",
    method="search_count",
    args_json='[[["model", "=", "crm.lead"]]]'
)
# count["result"] tells you the total
```

Then decide: fetch all, paginate, or narrow the filter.

## Pagination pattern

```python
PAGE_SIZE = 100
domain = '[[["model", "=", "crm.lead"]]]'

# 1) count
total = execute_method(model="mail.message", method="search_count", args_json=domain)["result"]

# 2) iterate pages
for page in range((total // PAGE_SIZE) + 1):
    batch = execute_method(
        model="mail.message",
        method="search_read",
        args_json=domain,
        kwargs_json=f'{{"fields": ["id", "date", "subject"], "limit": {PAGE_SIZE}, "offset": {page * PAGE_SIZE}, "order": "id asc"}}'
    )
    for record in batch["result"]:
        ...
```

**Always order by a stable field** (`id asc` is safest) when paginating. Without `order`, Postgres is free to return rows in any order between pages, causing dupes and misses.

## Two-phase fetch (ids then batched reads)

For very large sets, search returns lightweight IDs; batched `read` fetches only the fields you need:

```python
# Phase 1: all matching IDs (cheap — one column)
all_ids = execute_method(
    model="sale.order",
    method="search",
    args_json='[[["date_order", ">=", "2026-01-01"]]]',
    kwargs_json='{"limit": 0}'   # 0 = unlimited, use sparingly
)["result"]

# Phase 2: process in chunks
CHUNK = 200
for i in range(0, len(all_ids), CHUNK):
    ids = all_ids[i:i + CHUNK]
    records = execute_method(
        model="sale.order",
        method="read",
        args_json=f'[{ids}, ["name", "partner_id", "amount_total"]]'
    )["result"]
```

## Filter aggressively on indexed fields

Prefer domains over post-processing:

```python
# BAD — fetch all then filter in Python
rows = execute_method(model="sale.order", method="search_read", args_json='[]')["result"]
recent = [r for r in rows if r["date_order"] > "2026-01-01"]

# GOOD — push filter to Odoo
rows = execute_method(
    model="sale.order",
    method="search_read",
    args_json='[[["date_order", ">=", "2026-01-01"]]]'
)["result"]
```

Indexed fields on most models: `id`, `name`, `create_date`, `write_date`, `state`, `partner_id`, `active`. Dates and `partner_id` are nearly always indexed.

## `read_group` for aggregations

Don't fetch rows just to sum/count them — use `read_group`:

```python
# Total revenue per salesperson this year
execute_method(
    model="sale.order",
    method="read_group",
    args_json='[[["date_order", ">=", "2026-01-01"], ["state", "in", ["sale", "done"]]], ["amount_total:sum"], ["user_id"]]'
)
# Returns one row per user_id with amount_total summed
```

## When you hit the 1000-record cap

The cap is protective but overridable. Override only when you know the dataset is bounded:

```python
kwargs_json='{"fields": ["id", "name"], "limit": 5000}'   # warned but allowed
kwargs_json='{"fields": ["id"], "limit": 0}'              # unlimited, use with care
```

If a tool call warns about the cap, it's a signal that pagination would be safer.

## Cost hierarchy (cheapest → most expensive)

1. `search_count` — one COUNT(*) query
2. `search` with small `limit` — one SELECT id
3. `search_read` with narrow `fields` + tight `limit` — one SELECT with chosen columns
4. `read_group` — one SELECT with GROUP BY (cheap aggregation)
5. `search_read` without `fields` — SELECT * plus all computed fields
6. Unbounded `search_read` — the above × record count

Pick the cheapest one that answers your question.
