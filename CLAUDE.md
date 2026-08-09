# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Odoo MCP Server Advanced** — an MCP server giving AI assistants full access to Odoo ERP through universal tools rather than dozens of specialized ones.

**Core philosophy: radical simplicity.** `execute_method` can call *any* method on *any* Odoo model — that is the entire ORM. Specialized tools were removed in v1.0 as redundant. When a capability is missing, the fix is almost always a COOKBOOK recipe or a skill, **not a new tool**.

Package `odoo-mcp` v1.0.0-beta.2, Python ≥3.10 (developed on 3.14), **FastMCP 3.x** (`>=3.2,<4`), license GPL-3.0-or-later.

The MCP protocol revision is negotiated by FastMCP and the `mcp` SDK — this repo does not implement or pin one. Don't assert a specific spec date in docs; state the FastMCP major instead, which is what actually constrains the code.

## Commands

### Setup

```bash
pip install -e ".[dev]"      # editable install + dev tooling
```

A `.venv/` exists in the repo — prefix commands with `.venv/bin/python -m …` when using it.

### Running

Each transport has a console script (from `[project.scripts]`) and an equivalent module path:

| Transport | Console script | Module | Default bind |
|---|---|---|---|
| STDIO (Claude Desktop/Code, Cursor) | `odoo-mcp` | `python -m odoo_mcp` | — |
| Streamable HTTP | `odoo-mcp-http` | `python -m odoo_mcp.runners.http` | `127.0.0.1:8008/mcp` |
| SSE — ⚠️ deprecated | `odoo-mcp-sse` | `python -m odoo_mcp.runners.sse` | `127.0.0.1:8009/sse` |
| HTTP + Bearer auth | `odoo-mcp-http-secure` | `python -m odoo_mcp.runners.http_secure` | `0.0.0.0:8008/mcp` |

Override with `MCP_HOST` / `MCP_PORT` / `MCP_HTTP_PATH` / `MCP_SSE_PATH`. `http_secure` **requires** `MCP_BEARER_TOKEN` and exits 1 without it; the plain `http`/`sse` runners have no auth and warn when bound to `0.0.0.0`.

**SSE is deprecated upstream** — MCP deprecated HTTP+SSE in protocol revision `2025-03-26` and formally classified it Deprecated (twelve-month minimum removal window) in `2026-07-28`. It still works and we're not dropping it before upstream does, but route new work to Streamable HTTP, which covers browsers too. Migration steps: `DOCS/TRANSPORTS.md`.

Every runner tees stderr to `logs/mcp_server_<transport>_<timestamp>.log` via `logging_util.setup_file_logging`.

Docker: `Dockerfile` (STDIO), `Dockerfile.sse` (8009), `Dockerfile.http` (8008) — each `ENTRYPOINT`s the matching console script. `docker-compose.yml` runs the sse + http services.

### Tests

```bash
pytest                                       # all 95 tests, ~0.5s
pytest tests/test_domain.py                  # one file
pytest tests/test_domain.py::TestCanonicalFormat::test_single_triple_list  # one test
pytest -k "prompt"                           # by keyword
pytest --cov=src --cov-report=term-missing   # coverage
pytest -m "not integration"                  # skip live-Odoo tests
```

`pythonpath = ["src"]` is set in `pyproject.toml`, so tests import `odoo_mcp` without installing. Tests are organized in classes (`class TestReadPatterns:`), not bare functions — grep accordingly.

Two kinds of test live here:

- `test_domain.py`, `test_limits.py`, `test_cookbook.py` — pure functions, no I/O
- `test_mcp_surface.py` — drives the **real FastMCP machinery** through an in-memory `Client(mcp)` with a `FakeOdoo` injected via `monkeypatch.setattr(srv, "get_odoo_client", …)`

**Put anything that can break at registration or render time in `test_mcp_surface.py`.** The pure suites structurally cannot see that class of bug: when FastMCP 3 tightened the prompt return contract, all three prompts broke at `prompts/get` while import, startup, and `prompts/list` all still succeeded, and every existing test stayed green.

`odoo_client.py` still has no direct coverage — it needs a live Odoo. The `integration` marker is declared for that purpose but currently unused.

### Code quality — read this before running formatters

The tooling is configured but **has never been applied to the codebase**. Right now:

- `black .` would reformat **13 of 16 files** (line-length 88 vs. the hand-wrapped ~79 style actually in the tree)
- `ruff check .` reports 5 errors (unused imports in `odoo_client.py`/`server.py`, one unused local in `server.py:get_methods`)
- `mypy src/` reports 13 errors — `disallow_untyped_defs = true` but `server.py` and `odoo_client.py` are largely unannotated legacy

**Do not run repo-wide `black .` / `ruff --fix .` as part of an unrelated change** — it buries your diff under hundreds of reformatting lines. Scope to files you actually touch:

```bash
black path/to/file.py && isort path/to/file.py && ruff check path/to/file.py
```

New modules (`domain.py`, `limits.py`, `cookbook.py`, `logging_util.py`, `runners/*`) are fully typed with `from __future__ import annotations` — match that style. The two legacy modules are not; don't half-migrate them.

## Architecture

### Layering rule

`odoo_client.py` owns **only transport + auth**. Business logic, normalization, limits, and error envelopes live in `server.py` and the pure-function modules. Don't push policy down into the client.

### Module map

```
src/odoo_mcp/
├── server.py         MCP surface: 3 tools, 8 resources, 3 prompts. Orchestration only —
│                     delegates to the pure modules below, wraps results in JSON envelopes.
├── odoo_client.py    OdooClient: JSON-RPC (Odoo 14–18) + JSON-2 (19+), config loading,
│                     lru_cache'd singleton get_odoo_client().
├── domain.py         normalize_domain() — pure. Coerces any LLM-emitted domain shape
│                     into canonical Odoo triples.
├── limits.py         apply_limits() / warn_large_read() / warn_large_result() — pure.
│                     DEFAULT_LIMIT=100, MAX_LIMIT=1000, SEARCH_METHODS frozenset.
├── cookbook.py       read_patterns() / add_pattern() over COOKBOOK.md — pure.
│                     MIN_FAILED_APPROACHES=4 threshold enforced here.
├── logging_util.py   TeeLogger — stderr → terminal + file, closed via atexit.
├── __main__.py       STDIO entry point; masks *_PASSWORD/*_KEY/*_SECRET/*_TOKEN env vars.
└── runners/          http.py, sse.py, http_secure.py — thin transport wrappers over `mcp`.
```

The pure modules return `(value, warnings)` or plain dicts and never log. `server.py` decides what to print to stderr. Keep it that way — it's what makes them testable without a live Odoo.

### execute_method request path

1. Parse `args_json` / `kwargs_json` (must be a JSON array / object respectively, else error envelope)
2. If method ∈ `SEARCH_METHODS` and args present → `normalize_domain(args[0])`
3. `apply_limits(method, kwargs)` → possibly-modified kwargs + warnings to stderr
4. `warn_large_read(args)` when method is `read`
5. `odoo.execute_method(model, method, *args, **kwargs)`
6. `warn_large_result(result)` → stderr
7. Return `{"success": True, "result": …}` or `{"success": False, "error": str(e)}`

Every exception becomes an error envelope; nothing propagates out of the tool.

### Authentication paths

**JSON-RPC (default, Odoo 14–18)** — `_connect()` authenticates at construction to get `uid`; every call posts `execute_kw` to `/jsonrpc` with `db, uid, password`. `_jsonrpc_call` unwraps `result["result"]` and raises `ValueError` on `result["error"]`. Deprecated in Odoo 20 (fall 2026).

**JSON-2 (Odoo 19+ only, opt-in)** — Bearer token in `Authorization`, db in `X-Odoo-Database`, POST to `/api/v2/{model}/{method}`. No pre-auth round trip.

⚠️ **Asymmetry:** the JSON-2 branch returns `response.json()` — the *whole* HTTP body — while JSON-RPC returns the unwrapped `result` field. Response shapes differ between API versions. Anything consuming results generically must account for this.

### Configuration resolution (`load_config`)

1. Load the first `.env` found: `$ODOO_CONFIG_DIR/.env` → `./.env` → `~/.config/odoo/.env` → `~/.env` (with `override=True`)
2. If **all four** of `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` are set → use them
3. Else fall back to `./odoo_config.json` → `~/.config/odoo/config.json` → `~/.odoo_config.json`
4. Else raise `FileNotFoundError` listing every path searched

⚠️ **Trap:** step 2 requires `ODOO_PASSWORD` even when `ODOO_API_VERSION=json-2` (where auth actually comes from `ODOO_API_KEY`). A JSON-2 setup without `ODOO_PASSWORD` silently skips to the JSON-config fallback and usually fails with "No Odoo configuration found".

`get_odoo_client()` is `@lru_cache(maxsize=1)` — one client per process. Call `get_odoo_client.cache_clear()` to force a rebuild (tests only).

Env vars: `ODOO_API_VERSION` (`json-rpc`|`json-2`), `ODOO_API_KEY`, `ODOO_TIMEOUT` (30), `ODOO_VERIFY_SSL` (true), `HTTP_PROXY`, `ODOO_CONFIG_DIR`.

### Smart limits

Applies only to `search`, `search_read`, `search_count`. Missing/`None` limit → `DEFAULT_LIMIT=100`. `limit > 1000` → capped to `MAX_LIMIT`. `limit=0`/`False` → allowed, warned (unbounded). Results ≥ `MAX_LIMIT` trigger a "consider adding filters" warning. Constants live in `limits.py`, not `server.py`.

The system is intentionally restrictive: it prevents accidentally pulling GBs (e.g. every `mail.message`). To go past 1000, **paginate** — `search_count` first, then loop with `limit`/`offset`. Don't raise the cap.

### Domain normalization

`normalize_domain` accepts, in order: canonical triple lists, a bare `["field","op",val]` triple (auto-wrapped), doubly-wrapped `[[triple]]` (unwrapped one level), `{"conditions":[{field,operator,value}]}`, JSON strings, Python-literal strings (via `ast.literal_eval`), `None`/empty → `[]`.

**Invalid conditions are dropped silently.** Logic operators `&`, `|`, `!` pass through. Callers wanting strictness must compare input vs. output length themselves.

### Self-learning cookbook

`COOKBOOK.md` has a `## 🧠 Learned Patterns` section that grows from experience:

- **Read** — MCP resource `odoo://cookbook/patterns` returns the section between that heading and the next `##`
- **Write** — tool `add_cookbook_pattern` splices new entries in just before the `### How to Use This Section` footer, and **refuses payloads with fewer than 4 failed approaches**
- Discovery order: `<repo>/COOKBOOK.md` → parent dir (editable installs) → `/app/COOKBOOK.md` (Docker)

Your own workflow when using these MCP tools: try first → after the **first** failure read `odoo://cookbook/patterns` → after **≥4** distinct failed approaches, call `add_cookbook_pattern` and announce `✅ New pattern documented: <key lesson>`. The 4-approach threshold is enforced server-side, so a rejected write means the problem wasn't hard enough to be worth recording.

If you edit `COOKBOOK.md` by hand, keep both marker headings intact — `cookbook.py` locates its read range and insertion point by exact string match.

## MCP surface

**Tools (3):** `execute_method`, `batch_execute`, `add_cookbook_pattern`

**Resources (8), but clients see them in two lists:**

- *Concrete* → `resources/list`: `odoo://models`, `odoo://workflows`, `odoo://server/info`, `odoo://cookbook/patterns`
- *Templates* → `resources/templates/list`: `odoo://model/{m}/schema`, `odoo://model/{m}/access`, `odoo://methods/{m}`, `odoo://record/{m}/{id}`

A client that only reads `resources/list` never sees the schema resource. Worth knowing when debugging "the client can't find it".

**Prompts (3):** `search-customers`, `create-sales-order`, `odoo-exploration`

Prompt functions **return a plain `str`** (or a `Message`, or a list of those). FastMCP 3 rejects the 2.x `[{"role": …, "content": …}]` shape at render time — `prompts/list` still succeeds, so the failure only surfaces when a client calls `prompts/get`. `test_mcp_surface.py::TestPrompts` guards this.

`odoo://workflows` hardcodes step-by-step recipes keyed off installed modules (`sale`, `stock`, `crm`, `hr`, `account`, `project`) — extend the dict there when adding module coverage.

### Adding a resource

```python
@mcp.resource(
    "odoo://your-resource/{param}",
    description="Resource description",
    annotations={"audience": ["assistant"], "priority": 0.8},
)
def get_your_resource(param: str) -> str:
    odoo_client = get_odoo_client()
    try:
        ...
        return json.dumps(result, indent=2)
    except Exception as exc:
        return _error(str(exc))
```

Resources return **JSON strings**, never raise, and use the `_error()` helper for failures. Then update `README.md`, `AGENTS.md`, and `DOCS/CLAUDE.md`, and add a COOKBOOK example if user-facing.

## batch_execute: two things it does not do

Both were once documented as working. The docs are corrected; the behavior is unchanged, so keep these in mind when writing recipes:

- **No `@N` back-references.** `batch_execute` parses each op's args and executes them in order with no placeholder substitution. An op cannot consume an earlier op's result. Chaining means reading op *N*'s result client-side and issuing a second call.
- **`atomic=True` fails fast; it does not roll back.** It stops at the first error and reports which op failed, but anything already written to Odoo stays written — there is no shared transaction across JSON-RPC calls. The error string still says "no operations committed", which is misleading and worth fixing.

Real atomicity would require a single server-side call (an Odoo-side wrapper method), not N round trips — a design change, not a doc fix.

## Claude Code skills

Eight skills ship in `.claude/skills/` and auto-activate on matching requests: `odoo-mcp-searching`, `-efficient-queries`, `-crud`, `-relationships`, `-workflows`, `-batch`, `-real-world`, `-learned-patterns`. They shape how Claude Code drives the server; they don't change server behavior. Other MCP clients don't see them — the portable equivalent is `COOKBOOK.md` + `odoo://cookbook/patterns`. Adding one: `.claude/skills/<name>/SKILL.md` with `name` + `description` frontmatter (see `.claude/skills/README.md`).

## Conventions

- **Resist adding tools.** New capability → COOKBOOK recipe or skill. Two universal tools is the design, not a limitation.
- **Pass Odoo errors through verbatim.** They're descriptive; don't pre-validate client-side or wrap them in friendlier text.
- **Always pass `fields` to `search_read`** in examples and recipes — omitting it returns every column including large text blobs.
- **Never add `Claude Code` attribution** to commits or docs (global user config).
- Use the `context7` MCP tool to verify current Odoo API behavior before modifying `odoo_client.py`.

## Reference docs

| File | Contents |
|---|---|
| `AGENTS.md` | Assistant-facing quick reference |
| `COOKBOOK.md` | 45+ recipes + the Learned Patterns section |
| `DOCS/CLAUDE.md` | Long-form technical reference |
| `DOCS/TRANSPORTS.md` | STDIO / SSE / HTTP details |
| `DOCS/DOCKER.md`, `DOCS/STREAMINGHTTP_GUIDE.md`, `DOCS/SECURITY.md` | Deployment and hardening |
| `USER_GUIDE.md` | End-user setup |
| `nginx.conf.example` | Reverse-proxy template for the HTTP transports |
