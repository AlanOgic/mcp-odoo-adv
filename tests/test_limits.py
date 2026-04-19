"""Tests for ``odoo_mcp.limits`` smart-limit policy."""
from __future__ import annotations

import pytest

from odoo_mcp.limits import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SEARCH_METHODS,
    apply_limits,
    warn_large_read,
    warn_large_result,
)


class TestSearchMethodsSet:
    def test_contains_expected_methods(self) -> None:
        assert SEARCH_METHODS == {"search", "search_count", "search_read"}


class TestApplyLimitsNonSearchMethods:
    @pytest.mark.parametrize(
        "method", ["create", "write", "unlink", "read", "fields_get"]
    )
    def test_passthrough_for_non_search(self, method: str) -> None:
        kwargs = {"limit": 999999}  # deliberately absurd
        new_kwargs, warnings = apply_limits(method, kwargs)
        assert new_kwargs == {"limit": 999999}
        assert warnings == []


class TestApplyLimitsMissingLimit:
    @pytest.mark.parametrize("method", ["search", "search_count", "search_read"])
    def test_applies_default(self, method: str) -> None:
        new_kwargs, warnings = apply_limits(method, {})
        assert new_kwargs == {"limit": DEFAULT_LIMIT}
        assert len(warnings) == 1
        assert "default" in warnings[0].lower()

    def test_default_matches_constant(self) -> None:
        new_kwargs, _ = apply_limits("search_read", {})
        assert new_kwargs["limit"] == DEFAULT_LIMIT


class TestApplyLimitsNoneLimit:
    def test_none_treated_as_missing(self) -> None:
        new_kwargs, warnings = apply_limits("search_read", {"limit": None})
        assert new_kwargs["limit"] == DEFAULT_LIMIT
        assert len(warnings) == 1


class TestApplyLimitsUnlimited:
    def test_zero_kept_with_warning(self) -> None:
        new_kwargs, warnings = apply_limits("search_read", {"limit": 0})
        assert new_kwargs["limit"] == 0
        assert len(warnings) == 1
        assert "unlimited" in warnings[0].lower()

    def test_false_kept_with_warning(self) -> None:
        new_kwargs, warnings = apply_limits("search_read", {"limit": False})
        assert new_kwargs["limit"] is False
        assert len(warnings) == 1


class TestApplyLimitsOverMax:
    def test_over_max_is_capped(self) -> None:
        new_kwargs, warnings = apply_limits(
            "search_read", {"limit": MAX_LIMIT + 5000}
        )
        assert new_kwargs["limit"] == MAX_LIMIT
        assert len(warnings) == 1
        assert "capping" in warnings[0].lower() or "cap" in warnings[0].lower()


class TestApplyLimitsWithinRange:
    @pytest.mark.parametrize("limit", [1, 50, 99, DEFAULT_LIMIT, 500, MAX_LIMIT])
    def test_passthrough(self, limit: int) -> None:
        new_kwargs, warnings = apply_limits("search_read", {"limit": limit})
        assert new_kwargs["limit"] == limit
        assert warnings == []


class TestApplyLimitsPurity:
    def test_input_kwargs_not_mutated(self) -> None:
        kwargs = {"limit": 10, "offset": 5, "fields": ["name"]}
        snapshot = dict(kwargs)
        apply_limits("search_read", kwargs)
        assert kwargs == snapshot

    def test_preserves_other_kwargs(self) -> None:
        kwargs = {"offset": 20, "order": "name ASC", "fields": ["a", "b"]}
        new_kwargs, _ = apply_limits("search_read", kwargs)
        assert new_kwargs["offset"] == 20
        assert new_kwargs["order"] == "name ASC"
        assert new_kwargs["fields"] == ["a", "b"]


class TestWarnLargeRead:
    def test_small_read_no_warning(self) -> None:
        args = [[1, 2, 3], ["name"]]
        assert warn_large_read(args) == []

    def test_exactly_max_no_warning(self) -> None:
        args = [list(range(MAX_LIMIT)), ["name"]]
        assert warn_large_read(args) == []

    def test_over_max_warns(self) -> None:
        args = [list(range(MAX_LIMIT + 1)), ["name"]]
        warnings = warn_large_read(args)
        assert len(warnings) == 1
        assert str(MAX_LIMIT + 1) in warnings[0]

    def test_empty_args(self) -> None:
        assert warn_large_read([]) == []

    def test_non_list_first_arg(self) -> None:
        assert warn_large_read(["not a list"]) == []


class TestWarnLargeResult:
    def test_small_result_no_warning(self) -> None:
        assert warn_large_result([1, 2, 3]) == []

    def test_at_max_warns(self) -> None:
        warnings = warn_large_result(list(range(MAX_LIMIT)))
        assert len(warnings) == 1

    def test_over_max_warns(self) -> None:
        warnings = warn_large_result(list(range(MAX_LIMIT + 500)))
        assert len(warnings) == 1

    def test_non_list_no_warning(self) -> None:
        assert warn_large_result({"some": "dict"}) == []
        assert warn_large_result(42) == []
        assert warn_large_result(None) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
