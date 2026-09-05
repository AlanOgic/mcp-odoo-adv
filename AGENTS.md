# AGENTS.md — using this MCP server as an AI assistant

This file is the quick reference for AI assistants (Claude, Cursor, ChatGPT-via-MCP, others) talking to the Odoo MCP server. Humans should read [README.md](./README.md) instead.

## What this server gives you

| Surface | Count | Purpose |
|---|---|---|
| **Tools** | 3 | `execute_method`, `batch_execute`, `add_cookbook_pattern` |
| **Resources** | 8 | discovery (`odoo://models`, `odoo://model/{m}/schema`, …) + `odoo://cookbook/patterns` |
| **Prompts** | 3 | `search-customers`, `create-sales-order`, `odoo-exploration` |

You don't need a tool per Odoo operation. `execute_method` lets you call **any** method on **any** model — that's the entire Odoo ORM.

## The two universal tools

### `execute_method(model, method, args_json, kwargs_json)`

Call any Odoo method. Both `args_json` and `kwargs_json` are **JSON strings**, not Python dicts.

```python
execute_method(
    model="res.partner",
    method="search_read",
    args_json='[[["customer_rank", ">", 0]]]',
    kwargs_json='{"fields": ["name", "email"], "limit": 50}'
)
# → {"success": True, "result": [...]}
```

Every response is `{"success": bool, "result": ...}` or `{"success": False, "error": "..."}`. Always check `success` before touching `result`.

### `batch_execute(operations, stop_on_error=True)`

Run multiple operations in order. Use `@N` to reference a previous operation's result (1-indexed) anywhere in `args_json`/`kwargs_json`.

**This is not a transaction.** Odoo commits each operation independently and this server cannot roll back.

```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "create",
         "args_json": '[{"name": "Acme"}]'},
        {"model": "sale.order", "method": "create",
         "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 5, "product_uom_qty": 1}]]}]'},
        {"model": "sale.order", "method": "action_confirm",
         "args_json": '[["@2"]]'}
    ],
    stop_on_error=True
)
```

If a step fails with `stop_on_error=True` (default), the batch halts there —
but every operation that already succeeded **stays committed**. Nothing is
undone. Check `successful_operations` in the response to see what landed, and
clean up yourself if the partial state is wrong. `rolled_back` is always
`False`; it exists to make that explicit.

For genuine all-or-nothing work, write an Odoo-side method that does the whole
unit of work and call it with `execute_method`.

`atomic=` is still accepted as a deprecated alias for `stop_on_error=`.

## Discovery resources

Read these **before guessing**. They cost less than a failed `execute_method` call.

| Resource | Returns |
|---|---|
| `odoo://models` | All Odoo models in this instance |
| `odoo://model/{model}` | Model summary + field list |
| `odoo://model/{model}/schema` | Full schema: fields, types, requireds, relationships |
| `odoo://model/{model}/access` | Your CRUD permissions on this model |
| `odoo://fields/{model}` | Field definitions only |
| `odoo://methods/{model}` | Methods available on this model |
| `odoo://workflows` | Business workflows enabled by installed modules |
| `odoo://server/info` | Odoo version, database, installed modules |
| `odoo://record/{model}/{id}` | A single record |
| `odoo://search/{model}/{domain}` | Search results for a quoted domain |

## The cookbook (after your first failure)

When `execute_method` returns an unexpected result or error, **read this resource before retrying**:

```
odoo://cookbook/patterns
```

It returns the **Learned Patterns** section of `COOKBOOK.md` — recipes that took ≥4 failed attempts in past sessions to discover. Examples: many2many search needs `in` with a list (not `=`), `mail.message.message_type` distinguishes drafts from real emails.

## Writing back to the cookbook

If you tried **≥4 distinct approaches** and finally found a working solution worth remembering, document it:

```python
add_cookbook_pattern(
    problem="Brief description of what you were trying to do",
    failed_approaches=[
        "First attempt — why it failed",
        "Second attempt — why it failed",
        "Third attempt — why it failed",
        "Fourth attempt — why it failed"
    ],
    working_solution='execute_method(...)',
    why_it_works="The technical reason this is correct",
    key_lesson="The portable takeaway",
    related_links=""  # optional
)
```

The tool **refuses** patterns with fewer than 4 failed approaches — this guards against documenting trivial misses. After a successful add, announce: `✅ New pattern documented: <key lesson>`.

## Decision flow

```
User asks for Odoo data/action
  │
  ├── Need to know what fields exist? → odoo://model/{m}/schema
  ├── Need to know if you have permission? → odoo://model/{m}/access
  └── Otherwise → execute_method
        │
        ├── success → return result
        │
        └── unexpected result → read odoo://cookbook/patterns
              │
              ├── matching recipe → apply it
              │
              └── no recipe → try next approach
                    │
                    └── after ≥4 failures → call add_cookbook_pattern
```

## Hard-won rules (if you read nothing else)

1. **Many2many fields require `in` with a list**, never `=` with a scalar. Wrong: `[["category_id", "=", 5]]`. Right: `[["category_id", "in", [5]]]`.

2. **Always pass `fields` to `search_read`.** Without it, every column of every record is returned — including huge text blobs and computed fields. Costs explode silently.

3. **Smart limit is 100/1000.** Without an explicit `limit`, you get 100 records and a warning. Hard cap is 1000 — to go higher, paginate.

4. **`mail.message.message_type='comment'` for drafts/notes**, `'email'` for real sent/received messages. Picking `email` for a draft sends a real email.

5. **One2many / many2many writes use command tuples.** `[[0, 0, {vals}]]` creates a child, `[[6, 0, [ids]]]` replaces the set, `[[4, id]]` adds an existing record.

6. **Workflow methods are usually `action_*` or `button_*`.** Examples: `action_confirm` (sales), `action_post` (invoices), `button_validate` (stock pickings).

7. **Errors from Odoo are excellent.** Don't pre-validate. Try, read the error, fix.

## Configuration the user might mention

| Var | Meaning |
|---|---|
| `ODOO_URL` | Instance URL including `https://` |
| `ODOO_DB` | Database name |
| `ODOO_USERNAME` / `ODOO_PASSWORD` | Credentials (or API key in `ODOO_PASSWORD` for Odoo 14-18) |
| `ODOO_API_VERSION` | `json-rpc` (default, Odoo 14-18) or `json-2` (Odoo 19+) |
| `ODOO_API_KEY` | For JSON-2 only — Bearer token |
| `ODOO_TIMEOUT` | Connection timeout in seconds (default 30) |
| `ODOO_VERIFY_SSL` | Default `true` — set `false` only for self-signed dev instances |

## Skills (Claude Code only)

Eight Claude Code skills ship in `.claude/skills/` and auto-activate on relevant requests:

- `odoo-mcp-searching` — domains, operators, name_search
- `odoo-mcp-efficient-queries` — pagination, fields, read_group
- `odoo-mcp-crud` — create/write/unlink, archive vs delete
- `odoo-mcp-relationships` — m2o/o2m/m2m command tuples
- `odoo-mcp-workflows` — action_confirm, action_post, button_validate
- `odoo-mcp-batch` — sequenced multi-step operations with `@N` references
- `odoo-mcp-real-world` — HR/CRM/inventory cross-model recipes
- `odoo-mcp-learned-patterns` — cookbook read/write workflow

Other MCP clients (Claude Desktop, Cursor) don't see these. The same knowledge is available portably via `COOKBOOK.md` and the `odoo://cookbook/patterns` resource.

## What this server does NOT do

- **No specialized tools** — there's no `search_employee`, no `create_invoice`. Use `execute_method` with the right model/method.
- **No validation layer** — Odoo's own error messages are the source of truth. Don't guess required fields; try the create and read what's missing.
- **No auto-pagination** — if you need >1000 records, write a paginated loop. Smart limits warn but don't paginate for you.
- **No rate limiting** — if you hammer Odoo, it'll slow down. Use `batch_execute` to reduce round trips.
