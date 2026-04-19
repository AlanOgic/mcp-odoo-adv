---
name: odoo-mcp-learned-patterns
description: Check the cookbook of recipes learned from ≥4 failed attempts on hard Odoo problems. Use AFTER your first failure on any Odoo MCP call — before retrying with a new guess. The cookbook is a living record of non-obvious solutions (many2many search operators, mail.message type distinctions, workflow side effects) that weren't discoverable from the schema alone. Triggers on "why isn't this working", "search returns empty", "silent failure", "I've tried everything", "stuck on", "last resort", or after any `execute_method` returns an unexpected result.
---

# Odoo MCP — Learned Patterns (after your first failure)

The `odoo-joliemachine` MCP server exposes a resource that surfaces hard-won recipes collected from past sessions. **Read it BEFORE you try a 3rd approach to the same problem.**

## The workflow

```
Try execute_method/batch_execute
  │
  ├── success → done
  │
  └── fail → Read `odoo://cookbook/patterns` (this skill's signal)
                │
                ├── recipe matches → apply it
                │
                └── no recipe → keep trying
                         │
                         └── 4+ total failures → call `add_cookbook_pattern`
                                                (write what worked for next time)
```

## How to read the cookbook

Fetch the resource (or ask the user to) — most Claude Code sessions will have it available as:

```
odoo://cookbook/patterns
```

Returns a JSON envelope with `content` holding the Learned Patterns section of `COOKBOOK.md` verbatim. Each pattern has:

- **Problem**: what was being attempted
- **Failed approaches**: the tried-and-failed routes with reasons
- **Working solution**: the code that finally worked
- **Why it works**: the technical reason
- **Key lesson**: the portable takeaway

## When to write a new pattern (add_cookbook_pattern)

Use the `add_cookbook_pattern` tool when **all four** conditions hold:

1. You tried **≥4 distinct approaches** (not small variations — genuinely different ideas)
2. You finally found a working solution
3. The failures weren't obvious from the schema/error messages
4. The lesson generalizes (not just your specific record IDs)

The tool enforces the 4-failure minimum. Documenting shallow trial-and-error pollutes the cookbook — resist the urge.

## Tool signature

```python
add_cookbook_pattern(
    problem="Search products by attribute value",
    failed_approaches=[
        "Used `=` on many2many field attribute_line_ids",
        "Tried dotted notation attribute_line_ids.value_ids",
        "Used wrong model product.product instead of product.template",
        "Passed single int instead of list to the `in` operator"
    ],
    working_solution='execute_method(model="product.template", method="search_read", args_json=\'[[["product_template_attribute_value_ids", "in", [123]]]]\', kwargs_json=\'{"fields": ["name"]}\')',
    why_it_works="Many2many fields require 'in' operator with a list, not '='. The real m2m field is product_template_attribute_value_ids (the values), not attribute_line_ids (the lines).",
    key_lesson="For many2many: always 'in' with a list, never '=' with scalar.",
    related_links="https://www.odoo.com/documentation/ — search 'many2many domain'"
)
```

After a successful add, announce to the user: **"✅ New pattern documented: <key_lesson>"**

## Why this exists

LLMs re-make the same mistakes. A mistake that cost 4 failed attempts is worth a 30-second write so the next session doesn't pay the same cost. The cookbook is that savings account.

## Known recipes (current)

The cookbook is live; check `odoo://cookbook/patterns` for the current list. As of writing it contains:

- **Searching many2many fields** — the canonical example; use `in` with a list, pick the right m2m field (e.g., `product_template_attribute_value_ids` not `attribute_line_ids`)

The section will grow as more hard-won solutions are captured. Don't pre-seed it — only real trial-and-error earns a spot.

## Anti-patterns

- ❌ **Documenting a recipe after 1-2 tries** — tool will refuse, but don't even attempt
- ❌ **Pattern: "I forgot to add fields kwarg"** — not a Learned Pattern, it's a basic CRUD miss. Belongs in odoo-mcp-crud, not the cookbook.
- ❌ **Documenting a record-specific fix** ("order 42 needed this") — cookbook patterns must generalize
- ❌ **Cluttering with near-duplicates** — if a recipe already covers your case loosely, update it rather than add a second
