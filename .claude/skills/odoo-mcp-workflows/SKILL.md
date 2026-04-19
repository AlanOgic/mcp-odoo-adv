---
name: odoo-mcp-workflows
description: Trigger Odoo business actions — confirm sale orders, post invoices, validate stock pickings, mark CRM leads won/lost, convert leads to opportunities, validate timesheets. Use when a record needs a state transition beyond a simple field write (states like draft → confirmed / posted / done, cancel / reopen). Triggers on "confirm order", "post invoice", "validate picking", "mark won", "mark lost", "action_confirm", "action_post", "button_validate", "action_cancel", or any reference to an Odoo workflow button.
---

# Odoo MCP — Workflow actions

Odoo workflows are just methods on the record. Most are prefixed `action_*` (confirm, cancel, etc.) or `button_*` (validate). Call them via `execute_method` with the list of record IDs as args.

## Universal shape

```python
execute_method(
    model="sale.order",
    method="action_confirm",
    args_json='[[order_id]]'
)
```

`args_json` is `[[ids]]` — outer list for the method args, inner list for record IDs.

## Sales

**Confirm a quote → sale order:**
```python
execute_method(
    model="sale.order",
    method="action_confirm",
    args_json='[[order_id]]'
)
```

**Cancel:**
```python
execute_method(
    model="sale.order",
    method="action_cancel",
    args_json='[[order_id]]'
)
```

**Send by email (opens wizard in UI; headless version):**
```python
execute_method(
    model="sale.order",
    method="action_quotation_send",
    args_json='[[order_id]]'
)
# Returns an action dict — to actually send, use the wizard:
execute_method(
    model="mail.compose.message",
    method="create",
    args_json='[{"model": "sale.order", "res_id": order_id, "composition_mode": "comment", "template_id": template_id}]'
)
```

## Invoicing

**Post a draft invoice (draft → posted):**
```python
execute_method(
    model="account.move",
    method="action_post",
    args_json='[[invoice_id]]'
)
```

**Create invoice from sale order:**
```python
execute_method(
    model="sale.order",
    method="_create_invoices",
    args_json='[[order_id]]'
)
# Returns list of invoice record references
```

**Register payment (opens wizard):**
```python
execute_method(
    model="account.payment.register",
    method="create",
    args_json='[{"payment_date": "2026-04-19", "amount": 1500.0, "communication": "INV/2026/0042"}]',
    kwargs_json='{"context": {"active_model": "account.move", "active_ids": [invoice_id]}}'
)
```

## Inventory / Stock

**Validate a picking (delivery/receipt):**
```python
execute_method(
    model="stock.picking",
    method="button_validate",
    args_json='[[picking_id]]'
)
# If quantities don't match, returns a wizard action — handle or force
```

**Force backorder handling:**
```python
execute_method(
    model="stock.backorder.confirmation",
    method="process",
    args_json='[[wizard_id]]'
)
```

**Transfer stock:**
```python
execute_method(
    model="stock.move",
    method="_action_confirm",
    args_json='[[move_id]]'
)
execute_method(
    model="stock.move",
    method="_action_assign",
    args_json='[[move_id]]'
)
```

## CRM

**Mark lead as won:**
```python
execute_method(
    model="crm.lead",
    method="action_set_won",
    args_json='[[lead_id]]'
)
# Or newer API:
execute_method(
    model="crm.lead",
    method="action_set_won_rainbowman",
    args_json='[[lead_id]]'
)
```

**Mark as lost (opens wizard for reason):**
```python
execute_method(
    model="crm.lead",
    method="action_set_lost",
    args_json='[[lead_id]]',
    kwargs_json='{"context": {"default_lost_reason_id": 3}}'
)
```

**Convert lead → opportunity:**
```python
execute_method(
    model="crm.lead",
    method="convert_opportunity",
    args_json='[[lead_id]]',
    kwargs_json='{"partner_id": 42}'
)
```

## HR

**Validate timesheet:**
```python
execute_method(
    model="account.analytic.line",
    method="action_validate",
    args_json='[[line_ids]]'
)
```

**Approve leave request:**
```python
execute_method(
    model="hr.leave",
    method="action_approve",
    args_json='[[leave_id]]'
)
```

## Finding the right method

If you don't know the method name:

1. Check the UI — hover the button to see its XML id
2. Query methods resource — `odoo://methods/{model_name}`
3. Read the model source — `grep -r "action_" odoo/addons/<module>/models/` in an Odoo checkout
4. Common conventions:
   - `action_confirm` — draft → confirmed
   - `action_cancel` — → cancelled (usually reversible with `action_draft`)
   - `action_post` — for account.move only (posting entries)
   - `button_validate` — for stock.picking and similar
   - `_action_done` — internal; may require context

## Workflows that return wizards

Many workflow actions return an action dict describing a wizard to open in the UI:

```python
{
  "type": "ir.actions.act_window",
  "res_model": "stock.backorder.confirmation",
  "view_mode": "form",
  "target": "new",
  "context": {...}
}
```

From MCP, you can't show the wizard — but you can:
1. Create the wizard record with the same context
2. Call the wizard's "process"/"confirm"/"apply" method

Example for backorder:
```python
# The validate returned a wizard — emulate it
execute_method(
    model="stock.backorder.confirmation",
    method="create",
    args_json='[{"pick_ids": [[6, 0, [picking_id]]]}]'
)
execute_method(
    model="stock.backorder.confirmation",
    method="process",
    args_json='[[wizard_id]]'
)
```

## Check the result

Workflow methods return varied types: `True`, an action dict, nothing. What matters is the state change:

```python
execute_method(model="sale.order", method="action_confirm", args_json='[[order_id]]')

# Verify state flipped
execute_method(model="sale.order", method="read", args_json=f'[[{order_id}], ["state"]]')
# state should now be "sale" (or "done")
```

## Gotchas

- **State guards**: Workflows enforce order. `action_post` on an already-posted invoice raises `UserError`. Always check `state` first or handle the error.
- **Multi-company**: Workflows run in the record's company context. If the MCP user isn't in that company, silent failures happen. Pass `{"context": {"allowed_company_ids": [1, 2]}}`.
- **Record locks**: A record being edited in the UI by another user may block the workflow. The error mentions a concurrent update.
