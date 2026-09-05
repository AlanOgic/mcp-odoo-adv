---
name: odoo-mcp-batch
description: Run several Odoo operations in one call via batch_execute, passing results between them with @N references. Use for create-then-link sequences, multi-step workflows, and bulk updates. Note that batch_execute is NOT atomic and cannot roll back — read this skill before relying on all-or-nothing behaviour. Triggers on "batch", "multi-operation", "create and link", "atomic", "transaction", "all or nothing", "rollback".
---

# Odoo MCP — Batch operations

`batch_execute` runs a list of operations in order and lets each one reference
earlier results.

## ⚠️ It is not atomic

Despite the historical `atomic=` parameter name, **there is no rollback**. Odoo
commits each operation as its own transaction, so anything that already
succeeded stays in the database when a later operation fails. `stop_on_error`
(default `True`) only stops the sequence early.

If partial success would corrupt state, do **not** rely on this tool to undo
things. Either:
- write an Odoo-side method that performs the whole unit of work and call it
  with a single `execute_method`, or
- check `successful_operations` in the response and compensate manually.

## Universal shape

```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "create", "args_json": '[{"name": "New Co"}]'},
        {"model": "sale.order", "method": "create", "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 101, "product_uom_qty": 1}]]}]'}
    ],
    stop_on_error=True
)
```

Response:
```python
{
    "success": True,
    "results": [{"success": True, "result": 42}, {"success": True, "result": 1337}],
    "total_operations": 2,
    "successful_operations": 2,
    "failed_operations": 0,
    "rolled_back": False        # always False — see the warning above
}
```

## Reference previous operation results

Use `@N` in `args_json` to reference the Nth operation's result (1-indexed). The batch engine substitutes before each call.

```python
operations=[
    {"model": "res.partner", "method": "create", "args_json": '[{"name": "Acme", "email": "acme@example.com"}]'},
    # @1 = partner id from step 1
    {"model": "sale.order", "method": "create", "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 101, "product_uom_qty": 2}]]}]'},
    # @2 = order id from step 2
    {"model": "sale.order", "method": "action_confirm", "args_json": '[["@2"]]'}
]
```

## Stop-on-error vs continue

**`stop_on_error=True` (default):**
- First failure halts the sequence; later operations are never attempted
- Earlier successes remain committed — the response tells you how many
- Use for: create + link chains, where continuing would compound the mess

**`stop_on_error=False`:**
- Every operation is attempted; failures are reported per item
- Use for: bulk imports where partial success is fine, independent updates

`atomic=` is accepted as a deprecated alias for `stop_on_error=`.

```python
# Bulk tag update — one failure shouldn't block the rest
batch_execute(
    operations=[
        {"model": "res.partner", "method": "write", "args_json": '[[1], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[2], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[3], {"category_id": [[4, 5]]}]'},
    ],
    stop_on_error=False
)
```

## Common patterns

**Create customer + sale order + confirm:**
```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "create",
         "args_json": '[{"name": "Zenith SA", "email": "info@zenith.be", "customer_rank": 1}]'},
        {"model": "sale.order", "method": "create",
         "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 101, "product_uom_qty": 3}]]}]'},
        {"model": "sale.order", "method": "action_confirm",
         "args_json": '[[@2]]'},
    ],
    stop_on_error=True
)
```

If `action_confirm` fails (credit limit, etc.), the partner and order are rolled back.

**Invoice + payment together:**
```python
batch_execute(
    operations=[
        {"model": "account.move", "method": "action_post", "args_json": '[[invoice_id]]'},
        {"model": "account.payment.register", "method": "create",
         "args_json": '[{"amount": 1500.0, "payment_date": "2026-04-19"}]',
         "kwargs_json": f'{{"context": {{"active_model": "account.move", "active_ids": [{invoice_id}]}}}}'},
        {"model": "account.payment.register", "method": "action_create_payments", "args_json": '[[@2]]'}
    ],
    stop_on_error=True
)
```

**Lead progression — update stage + log note + subscribe:**
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
    stop_on_error=True
)
```

## When NOT to use batch_execute

- **Single operation**: just use `execute_method`, less ceremony
- **Different reference data per op** with no result chaining: multiple independent `execute_method` calls are clearer
- **Long-running imports** (thousands of records): consider a dedicated import via Odoo's `load()` method or a one-shot server action; batch_execute holds a transaction the whole time

## Error messages

When an operation fails, the response tells you which one — and how many earlier operations were already committed:

```python
{
    "success": False,
    "results": [
        {"success": True, "result": 42},
        {"success": False, "error": "partner_id required"}
    ],
    "total_operations": 3,
    "successful_operations": 1,
    "failed_operations": 1,
    "error": "Batch rolled back at operation 2: partner_id required"
}
```

The error is your Odoo error — not a batch abstraction — so the fix is the same as a plain create/write.

## Why this matters

Without `batch_execute`, the sequence "create customer → create order → confirm" could leave you with:
- A partner but no order (second call failed)
- A partner + draft order (third call failed) — worse, because now you have a stale record polluting reports

Atomic batches remove that category of bug entirely.
