---
name: odoo-mcp-batch
description: Run several Odoo operations in one batch_execute call to cut round trips, with fail-fast ordering so a bad step stops the rest. Use when a task needs multiple independent writes against known ids — bulk tag updates, multi-record writes, a write plus a message_post plus a subscribe on the same record. Triggers on "batch", "multi-operation", "bulk update", "several records at once", "in one call", "transaction", "atomic", "all or nothing", "rollback". Note it does NOT roll back and has no result chaining — this skill explains what to do instead.
---

# Odoo MCP — batching operations

`batch_execute` sends a list of operations in one MCP call. They run **in order**, each as its own Odoo call.

Read this first, because the tool's name oversells it:

| What you might assume | What actually happens |
|---|---|
| All-or-nothing transaction | ❌ No. Each op is a separate JSON-RPC call. |
| Failure rolls back earlier ops | ❌ No. Earlier writes **stay written**. |
| `@N` references a previous result | ❌ No such syntax. `"@1"` is sent to Odoo as the literal string `"@1"`. |
| Fewer round trips than N calls | ✅ Yes. This is the real benefit. |
| `atomic=True` stops at the first error | ✅ Yes — fail-fast, so later ops never run. |

## Universal shape

```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "write",
         "args_json": '[[42], {"customer_rank": 1}]'},
        {"model": "res.partner", "method": "message_post",
         "args_json": '[[42]]',
         "kwargs_json": '{"body": "<p>Promoted to customer</p>", "message_type": "comment", "subtype_xmlid": "mail.mt_note"}'}
    ],
    atomic=True
)
```

Response:
```python
{
    "success": True,
    "results": [{"operation_index": 0, "success": True, "result": True},
                {"operation_index": 1, "success": True, "result": 1337}],
    "total_operations": 2,
    "successful_operations": 2,
    "failed_operations": 0,
    "error": None
}
```

## Chaining: you need two calls

There is no way to feed operation 1's result into operation 2. Do it client-side.

```python
# ❌ WRONG — "@1" reaches Odoo as a literal string and the create fails
batch_execute(operations=[
    {"model": "res.partner", "method": "create", "args_json": '[{"name": "Acme"}]'},
    {"model": "sale.order", "method": "create", "args_json": '[{"partner_id": "@1"}]'}
])

# ✅ RIGHT — read the id, then issue the dependent call
r = execute_method(model="res.partner", method="create",
                   args_json='[{"name": "Acme", "customer_rank": 1}]')
partner_id = r["result"]

execute_method(model="sale.order", method="create",
               args_json=f'[{{"partner_id": {partner_id}, "order_line": [[0, 0, {{"product_id": 101, "product_uom_qty": 2}}]]}}]')
```

Batching only helps when every operation's arguments are **already known**.

## atomic=True vs atomic=False

Neither mode rolls back. The difference is what happens *after* a failure.

**`atomic=True` (default) — stop at the first error.**
Later operations are never dispatched. Use when a later step is meaningless if an earlier one failed, and you'd rather stop than compound the mess.

**`atomic=False` — keep going.**
Each operation stands alone; one failure doesn't block its siblings. Use for bulk updates where partial success is fine.

```python
# Bulk tag update — one bad id shouldn't block the rest
batch_execute(
    operations=[
        {"model": "res.partner", "method": "write", "args_json": '[[1], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[2], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[3], {"category_id": [[4, 5]]}]'},
    ],
    atomic=False
)
```

## Ordering is your only safety mechanism

Since nothing rolls back, sequence operations so the **most likely to fail runs first**. A failure then costs you nothing already written.

```python
# Post the invoice first — it's the step that can fail on validation.
# If it fails with atomic=True, no note is posted and nothing is half-done.
batch_execute(
    operations=[
        {"model": "account.move", "method": "action_post",
         "args_json": f'[[{invoice_id}]]'},
        {"model": "account.move", "method": "message_post",
         "args_json": f'[[{invoice_id}]]',
         "kwargs_json": '{"body": "<p>Posted and sent to customer</p>", "message_type": "comment", "subtype_xmlid": "mail.mt_note"}'}
    ],
    atomic=True
)
```

## Good fit: several writes on one known record

```python
batch_execute(
    operations=[
        {"model": "crm.lead", "method": "write",
         "args_json": f'[[{lead_id}], {{"stage_id": 3, "user_id": 7}}]'},
        {"model": "crm.lead", "method": "message_post",
         "args_json": f'[[{lead_id}]]',
         "kwargs_json": '{"body": "<p>Moved to Qualified after intro call</p>", "message_type": "comment", "subtype_xmlid": "mail.mt_note"}'},
        {"model": "crm.lead", "method": "message_subscribe",
         "args_json": f'[[{lead_id}]]',
         "kwargs_json": '{"partner_ids": [42]}'}
    ],
    atomic=True
)
```

All three take `lead_id`, which you already have — no chaining needed.

## When NOT to use batch_execute

- **You need real atomicity.** It doesn't exist here. If a half-applied state is unacceptable, write an Odoo-side method that does the whole thing in one server call and invoke that with `execute_method`.
- **Later ops depend on earlier results.** Use sequential `execute_method` calls.
- **Single operation.** Just use `execute_method`.
- **Thousands of records.** Use Odoo's `load()` or a server action.

## Error messages

```python
{
    "success": False,
    "results": [
        {"operation_index": 0, "success": True, "result": 42},
        {"operation_index": 1, "success": False, "error": "partner_id required"}
    ],
    "total_operations": 3,
    "successful_operations": 1,
    "failed_operations": 1,
    "error": "Batch failed at operation 1: partner_id required (atomic mode - no operations committed)"
}
```

⚠️ **That error string is wrong.** It says "no operations committed", but operation 0 committed and stayed committed — partner 42 exists. Trust `results`, not the summary sentence. After any partial batch, verify actual state before retrying, or you'll create duplicates.

## Why batching still matters

Fewer round trips over the wire, one MCP call instead of N, and fail-fast ordering that stops a doomed sequence early. That's a real win for multi-write tasks — just don't mistake it for a transaction.
