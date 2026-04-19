---
name: odoo-mcp-batch
description: Execute multiple Odoo operations atomically (all succeed or all rollback) via batch_execute. Use when an operation spans multiple records or models that must be consistent — creating customer + sale order together, moving leads through stages + logging notes, or any workflow where partial success corrupts state. Triggers on "atomic", "transaction", "all or nothing", "rollback", "batch", "multi-operation", "create and link", or whenever partial success would be worse than total failure.
---

# Odoo MCP — Atomic batch operations

`batch_execute` runs a list of operations in a single transaction. Default mode is atomic: if any operation fails, all previous ones roll back. Use when records must be consistent across steps.

## Universal shape

```python
batch_execute(
    operations=[
        {"model": "res.partner", "method": "create", "args_json": '[{"name": "New Co"}]'},
        {"model": "sale.order", "method": "create", "args_json": '[{"partner_id": "@1", "order_line": [[0, 0, {"product_id": 101, "product_uom_qty": 1}]]}]'}
    ],
    atomic=True
)
```

Response:
```python
{
    "success": True,
    "results": [{"success": True, "result": 42}, {"success": True, "result": 1337}],
    "total_operations": 2,
    "successful_operations": 2,
    "failed_operations": 0
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
    {"model": "sale.order", "method": "action_confirm", "args_json": '[[@2]]'}
]
```

## Atomic vs non-atomic

**Atomic (default, `atomic=True`):**
- Any failure → all previous operations rolled back
- Use for: create + link, multi-step workflows, state transitions

**Non-atomic (`atomic=False`):**
- Each operation stands alone; failures don't affect siblings
- Use for: bulk imports where partial success is OK, parallel-like updates, reporting

```python
# Bulk tag update — one failure shouldn't block the rest
batch_execute(
    operations=[
        {"model": "res.partner", "method": "write", "args_json": '[[1], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[2], {"category_id": [[4, 5]]}]'},
        {"model": "res.partner", "method": "write", "args_json": '[[3], {"category_id": [[4, 5]]}]'},
    ],
    atomic=False
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
    atomic=True
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
    atomic=True
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
    atomic=True
)
```

## When NOT to use batch_execute

- **Single operation**: just use `execute_method`, less ceremony
- **Different reference data per op** with no result chaining: multiple independent `execute_method` calls are clearer
- **Long-running imports** (thousands of records): consider a dedicated import via Odoo's `load()` method or a one-shot server action; batch_execute holds a transaction the whole time

## Error messages

When atomic fails, the response tells you which operation failed:

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
