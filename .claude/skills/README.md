# Odoo MCP — Claude Code skill book

Skills are auto-activated in Claude Code when a user's request matches the skill's `description`. They teach Claude how to use this project's `execute_method` / `batch_execute` tools correctly, so every session starts with the lessons from all past sessions.

These skills ship with the repo — anyone who clones it and uses Claude Code gets them automatically.

## Inventory

| Skill | Use when the user wants to… |
|---|---|
| [`odoo-mcp-searching`](./odoo-mcp-searching/SKILL.md) | Build domain filters, run `search` / `search_read` / `search_count`, navigate relations |
| [`odoo-mcp-efficient-queries`](./odoo-mcp-efficient-queries/SKILL.md) | Paginate, scope fields, count before fetching, use `read_group` |
| [`odoo-mcp-crud`](./odoo-mcp-crud/SKILL.md) | Create / write / unlink records; archive vs delete |
| [`odoo-mcp-relationships`](./odoo-mcp-relationships/SKILL.md) | Handle many2one / one2many / many2many writes (the `[[0, 0, {...}]]` command tuples) |
| [`odoo-mcp-workflows`](./odoo-mcp-workflows/SKILL.md) | Confirm sale orders, post invoices, validate pickings, mark leads won/lost |
| [`odoo-mcp-batch`](./odoo-mcp-batch/SKILL.md) | Atomic multi-op transactions — create + link + confirm in one shot |
| [`odoo-mcp-real-world`](./odoo-mcp-real-world/SKILL.md) | Cross-model recipes: HR, CRM pipeline, stock levels, unpaid invoices |
| [`odoo-mcp-learned-patterns`](./odoo-mcp-learned-patterns/SKILL.md) | Check the `odoo://cookbook/patterns` resource after a failure; write new patterns after ≥4 failures |

## Relationship to the MCP server

The server (this repo) exposes two tools — `execute_method` and `batch_execute` — plus discovery resources like `odoo://models`, `odoo://model/{model}/schema`, and `odoo://cookbook/patterns`.

The skills above are **Claude Code specific** — they're markdown instructions that activate when a user's request matches. They don't affect the MCP server's behavior; they shape how Claude Code uses the MCP server.

For portability across MCP clients (Claude Desktop, Cursor, etc.), the same knowledge is also available as:

- **`COOKBOOK.md`** — the full 45+ recipes
- **`odoo://cookbook/patterns`** — MCP resource exposing the Learned Patterns section

Both of those work anywhere. The skills are a Claude-Code-specific convenience on top.

## Contributing

Adding a new skill:

1. Create `.claude/skills/<skill-name>/SKILL.md`
2. Start with frontmatter: `name` (matches directory name) and `description` (the trigger — write it as "Use when the user wants to…")
3. Body: concrete examples, common gotchas, when-to-use / when-not-to-use
4. Keep it focused — one skill per topic, not one mega-skill

Extending an existing skill: just edit its `SKILL.md`. Keep examples short and specific.
