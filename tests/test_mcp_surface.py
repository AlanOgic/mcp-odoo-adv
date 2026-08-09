"""End-to-end smoke tests for the MCP surface (tools, resources, prompts).

These exercise the real FastMCP machinery over an in-memory client, with a
fake Odoo client injected so nothing touches a live instance.

Why this file exists: the pure-function suites (``test_domain``,
``test_limits``, ``test_cookbook``) cannot see registration- or
render-time breakage. When FastMCP 3 tightened the prompt return contract,
all three prompts broke at ``prompts/get`` while import, startup and
``prompts/list`` all still succeeded — no existing test failed. Anything
that only breaks when a client actually calls the server belongs here.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from fastmcp import Client

import odoo_mcp.server as srv
from odoo_mcp.limits import DEFAULT_LIMIT

EXPECTED_TOOLS = {"execute_method", "batch_execute", "add_cookbook_pattern"}

EXPECTED_PROMPTS = {"search-customers", "create-sales-order", "odoo-exploration"}

EXPECTED_RESOURCES = {
    "odoo://models",
    "odoo://workflows",
    "odoo://server/info",
    "odoo://cookbook/patterns",
}

EXPECTED_TEMPLATES = {
    "odoo://record/{model_name}/{record_id}",
    "odoo://model/{model_name}/schema",
    "odoo://model/{model_name}/access",
    "odoo://methods/{model_name}",
}


class FakeOdoo:
    """Stand-in for ``OdooClient`` — echoes the call instead of dispatching."""

    db = "fake-db"

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def execute_method(self, model: str, method: str, *args: Any, **kwargs: Any):
        self.calls.append((model, method, args, kwargs))
        return {"_fake": True, "model": model, "method": method,
                "args": list(args), "kwargs": kwargs}


@pytest.fixture
def fake_odoo(monkeypatch: pytest.MonkeyPatch) -> FakeOdoo:
    """Patch the client factory in the server module namespace.

    Both ``app_lifespan`` and the resource handlers resolve
    ``get_odoo_client`` from ``odoo_mcp.server``'s globals, so patching
    there covers every path.
    """
    fake = FakeOdoo()
    monkeypatch.setattr(srv, "get_odoo_client", lambda: fake)
    return fake


def run(coro):
    """Run an async body from a sync test (no asyncio plugin required)."""
    return asyncio.run(coro)


# ---- registration ----------------------------------------------------------


class TestRegistration:
    def test_tools_registered(self, fake_odoo: FakeOdoo) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return {t.name for t in await c.list_tools()}

        assert run(body()) == EXPECTED_TOOLS

    def test_resources_and_templates_registered(self, fake_odoo: FakeOdoo) -> None:
        """Parameterized URIs land in templates, not resources — keep both."""
        async def body():
            async with Client(srv.mcp) as c:
                resources = {str(r.uri) for r in await c.list_resources()}
                templates = {
                    t.uriTemplate for t in await c.list_resource_templates()
                }
                return resources, templates

        resources, templates = run(body())
        assert resources == EXPECTED_RESOURCES
        assert templates == EXPECTED_TEMPLATES

    def test_prompts_registered(self, fake_odoo: FakeOdoo) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return {p.name for p in await c.list_prompts()}

        assert run(body()) == EXPECTED_PROMPTS

    def test_execute_method_exposes_output_schema(self, fake_odoo: FakeOdoo) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                tools = await c.list_tools()
                return next(t for t in tools if t.name == "execute_method")

        assert run(body()).outputSchema is not None


# ---- prompts (regression guard for the FastMCP 3 return contract) ----------


class TestPrompts:
    """A prompt that lists fine can still fail to render — always call it."""

    @pytest.mark.parametrize("name", sorted(EXPECTED_PROMPTS))
    def test_prompt_renders(self, fake_odoo: FakeOdoo, name: str) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.get_prompt(name, {})

        result = run(body())
        assert len(result.messages) >= 1
        message = result.messages[0]
        assert message.role == "user"
        assert message.content.text.strip()

    def test_search_customers_interpolates_arguments(
        self, fake_odoo: FakeOdoo
    ) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.get_prompt(
                    "search-customers", {"city": "Liege", "country": "Belgium"}
                )

        text = run(body()).messages[0].content.text
        assert "in Liege" in text
        assert "from Belgium" in text

    def test_search_customers_renders_literal_json_braces(
        self, fake_odoo: FakeOdoo
    ) -> None:
        """The f-string escapes ``{{`` — the example must survive as valid JSON."""
        async def body():
            async with Client(srv.mcp) as c:
                return await c.get_prompt("search-customers", {})

        text = run(body()).messages[0].content.text
        assert '{"fields":' in text
        assert "{{" not in text

    def test_create_sales_order_interpolates_customer(
        self, fake_odoo: FakeOdoo
    ) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.get_prompt("create-sales-order", {"customer_id": 42})

        assert "customer ID 42" in run(body()).messages[0].content.text


# ---- tool round-trips ------------------------------------------------------


class TestExecuteMethod:
    def test_applies_default_limit_and_normalizes_domain(
        self, fake_odoo: FakeOdoo
    ) -> None:
        """A bare triple is wrapped, and the missing limit defaults to 100."""
        async def body():
            async with Client(srv.mcp) as c:
                return await c.call_tool(
                    "execute_method",
                    {
                        "model": "res.partner",
                        "method": "search_read",
                        "args_json": '[["name", "=", "x"]]',
                    },
                )

        payload = run(body()).structured_content
        assert payload["success"] is True
        _, _, args, kwargs = fake_odoo.calls[0]
        assert args[0] == [["name", "=", "x"]]
        assert kwargs["limit"] == DEFAULT_LIMIT

    def test_invalid_args_json_returns_error_envelope(
        self, fake_odoo: FakeOdoo
    ) -> None:
        """Bad input is an envelope, never an exception out of the tool."""
        async def body():
            async with Client(srv.mcp) as c:
                return await c.call_tool(
                    "execute_method",
                    {
                        "model": "res.partner",
                        "method": "search_read",
                        "args_json": "{not json",
                    },
                )

        payload = run(body()).structured_content
        assert payload["success"] is False
        assert "args_json" in payload["error"]
        assert not fake_odoo.calls

    def test_non_array_args_json_rejected(self, fake_odoo: FakeOdoo) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.call_tool(
                    "execute_method",
                    {
                        "model": "res.partner",
                        "method": "search_read",
                        "args_json": '{"a": 1}',
                    },
                )

        payload = run(body()).structured_content
        assert payload["success"] is False
        assert "must be a JSON array" in payload["error"]


class TestBatchExecute:
    def test_runs_operations_in_order(self, fake_odoo: FakeOdoo) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.call_tool(
                    "batch_execute",
                    {
                        "operations": [
                            {"model": "res.partner", "method": "create",
                             "args_json": '[{"name": "A"}]'},
                            {"model": "sale.order", "method": "create",
                             "args_json": '[{"partner_id": 1}]'},
                        ]
                    },
                )

        payload = run(body()).structured_content
        assert payload["successful_operations"] == 2
        assert payload["failed_operations"] == 0
        assert [c[0] for c in fake_odoo.calls] == ["res.partner", "sale.order"]

    def test_atomic_stops_at_first_failure(self, fake_odoo: FakeOdoo) -> None:
        """atomic=True fails fast — the later op must never be dispatched."""
        async def body():
            async with Client(srv.mcp) as c:
                return await c.call_tool(
                    "batch_execute",
                    {
                        "operations": [
                            {"method": "create"},  # missing 'model'
                            {"model": "sale.order", "method": "create",
                             "args_json": "[{}]"},
                        ],
                        "atomic": True,
                    },
                )

        payload = run(body()).structured_content
        assert payload["success"] is False
        assert payload["failed_operations"] == 1
        assert fake_odoo.calls == []


# ---- resources -------------------------------------------------------------


class TestResources:
    def test_schema_resource_categorizes_fields(self, fake_odoo: FakeOdoo) -> None:
        """fields_get output is split into relationships/required/readonly."""
        def fake_execute(model, method, *args, **kwargs):
            assert method == "fields_get"
            return {
                "name": {"type": "char", "required": True, "string": "Name"},
                "partner_id": {"type": "many2one", "relation": "res.partner",
                               "string": "Partner"},
                "total": {"type": "float", "store": False, "string": "Total"},
                "code": {"type": "char", "readonly": True, "string": "Code"},
            }

        fake_odoo.execute_method = fake_execute  # type: ignore[method-assign]

        async def body():
            async with Client(srv.mcp) as c:
                return await c.read_resource("odoo://model/sale.order/schema")

        schema = json.loads(run(body())[0].text)
        assert schema["model"] == "sale.order"
        assert schema["relationships"]["partner_id"]["relation"] == "res.partner"
        assert "name" in schema["required_fields"]
        assert "code" in schema["readonly_fields"]
        assert "total" in schema["computed_fields"]

    def test_record_resource_rejects_non_integer_id(
        self, fake_odoo: FakeOdoo
    ) -> None:
        async def body():
            async with Client(srv.mcp) as c:
                return await c.read_resource("odoo://record/res.partner/abc")

        payload = json.loads(run(body())[0].text)
        assert "must be an integer" in payload["error"]
