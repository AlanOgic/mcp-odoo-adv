"""Tests for ``odoo_mcp.batch`` references and ``batch_execute`` semantics."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from odoo_mcp.batch import (
    FAILED,
    BatchReferenceError,
    has_references,
    substitute_references,
)
from odoo_mcp.limits import DEFAULT_LIMIT, MAX_LIMIT
from odoo_mcp.server import batch_execute


class TestSubstituteReferences:
    def test_plain_scalar_passthrough(self) -> None:
        assert substitute_references(5, []) == 5
        assert substitute_references(None, []) is None

    def test_resolves_single_reference(self) -> None:
        assert substitute_references("@1", [42]) == 42

    def test_resolves_nested_reference(self) -> None:
        out = substitute_references({"partner_id": "@1", "lines": ["@2"]}, [7, 9])
        assert out == {"partner_id": 7, "lines": [9]}

    @pytest.mark.parametrize(
        "value", ["info@acme.com", "@mention", "a@1", "@1x", "@", ""]
    )
    def test_non_reference_strings_untouched(self, value: str) -> None:
        assert substitute_references(value, [1]) == value

    def test_does_not_mutate_input(self) -> None:
        original = {"a": ["@1"]}
        substitute_references(original, [1])
        assert original == {"a": ["@1"]}

    def test_tuple_is_rebuilt(self) -> None:
        assert substitute_references(("@1", 2), [8]) == (8, 2)

    def test_zero_index_rejected(self) -> None:
        with pytest.raises(BatchReferenceError, match="1-indexed"):
            substitute_references("@0", [1])

    def test_forward_reference_rejected(self) -> None:
        with pytest.raises(BatchReferenceError, match="only 1 operation"):
            substitute_references("@2", [1])

    def test_reference_to_failed_operation_rejected(self) -> None:
        with pytest.raises(BatchReferenceError, match="failed"):
            substitute_references("@1", [FAILED])


class TestHasReferences:
    def test_detects_nested(self) -> None:
        assert has_references({"a": [{"b": "@3"}]}) is True

    def test_ignores_emails(self) -> None:
        assert has_references({"email": "a@b.com"}) is False


def _ctx(odoo: Any) -> Any:
    ctx = MagicMock()
    ctx.request_context.lifespan_context.odoo = odoo
    return ctx


class RecordingOdoo:
    """Records calls; raises for any model listed in ``fail_models``."""

    def __init__(self, fail_models: set[str] | None = None) -> None:
        self.calls: list[tuple] = []
        self.fail_models = fail_models or set()

    def execute_method(self, model, method, *args, **kwargs):
        self.calls.append((model, method, args, kwargs))
        if model in self.fail_models:
            raise ValueError(f"boom in {model}")
        return len(self.calls)


_fn = getattr(batch_execute, "fn", batch_execute)


class TestBatchExecuteHonesty:
    def test_reports_no_rollback_and_names_committed_count(self) -> None:
        odoo = RecordingOdoo(fail_models={"sale.order"})
        resp = _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args": [{}]},
                {"model": "sale.order", "method": "create", "args": [{}]},
            ],
        )
        assert resp.success is False
        assert resp.rolled_back is False
        assert resp.successful_operations == 1
        assert "were NOT rolled back" in resp.error
        assert "no operations committed" not in resp.error

    def test_stop_on_error_halts_immediately(self) -> None:
        odoo = RecordingOdoo(fail_models={"res.partner"})
        _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args": [{}]},
                {"model": "sale.order", "method": "create", "args": [{}]},
            ],
            stop_on_error=True,
        )
        assert [c[0] for c in odoo.calls] == ["res.partner"]

    def test_continue_mode_attempts_every_operation(self) -> None:
        odoo = RecordingOdoo(fail_models={"res.partner"})
        resp = _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args": [{}]},
                {"model": "sale.order", "method": "create", "args": [{}]},
            ],
            stop_on_error=False,
        )
        assert [c[0] for c in odoo.calls] == ["res.partner", "sale.order"]
        assert resp.failed_operations == 1
        assert resp.successful_operations == 1

    def test_deprecated_atomic_alias_still_controls_stopping(self) -> None:
        odoo = RecordingOdoo(fail_models={"res.partner"})
        _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args": [{}]},
                {"model": "sale.order", "method": "create", "args": [{}]},
            ],
            atomic=False,
        )
        assert len(odoo.calls) == 2


class TestBatchExecuteReferences:
    def test_reference_resolves_to_earlier_result(self) -> None:
        odoo = RecordingOdoo()
        _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args": [{}]},
                {
                    "model": "sale.order",
                    "method": "create",
                    "args_json": '[{"partner_id": "@1"}]',
                },
            ],
        )
        assert odoo.calls[1][2] == ({"partner_id": 1},)

    def test_unresolvable_reference_is_reported_as_failure(self) -> None:
        odoo = RecordingOdoo()
        resp = _fn(
            _ctx(odoo),
            operations=[
                {"model": "sale.order", "method": "create", "args": [{"x": "@1"}]}
            ],
        )
        assert resp.success is False
        assert odoo.calls == []


class TestBatchExecuteGuardrails:
    def test_default_limit_applied_to_search(self) -> None:
        odoo = RecordingOdoo()
        _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "search_read", "args": [[]]}
            ],
        )
        assert odoo.calls[0][3]["limit"] == DEFAULT_LIMIT

    def test_max_limit_capped_in_batch(self) -> None:
        odoo = RecordingOdoo()
        _fn(
            _ctx(odoo),
            operations=[
                {
                    "model": "res.partner",
                    "method": "search_read",
                    "args": [[]],
                    "kwargs": {"limit": 999999},
                }
            ],
        )
        assert odoo.calls[0][3]["limit"] == MAX_LIMIT

    def test_domain_normalized_in_batch(self) -> None:
        odoo = RecordingOdoo()
        _fn(
            _ctx(odoo),
            operations=[
                {
                    "model": "res.partner",
                    "method": "search_read",
                    "args": [["name", "=", "Acme"]],
                }
            ],
        )
        assert odoo.calls[0][2][0] == [["name", "=", "Acme"]]

    def test_bad_argument_type_rejected(self) -> None:
        odoo = RecordingOdoo()
        resp = _fn(
            _ctx(odoo),
            operations=[
                {"model": "res.partner", "method": "create", "args_json": '{"a": 1}'}
            ],
        )
        assert resp.success is False
        assert "must be a list" in resp.results[0]["error"]
