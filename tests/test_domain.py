"""Tests for ``odoo_mcp.domain.normalize_domain``."""

from __future__ import annotations

import pytest

from odoo_mcp.domain import normalize_domain


class TestEmptyInputs:
    def test_none(self) -> None:
        assert normalize_domain(None) == []

    def test_empty_list(self) -> None:
        assert normalize_domain([]) == []

    def test_empty_dict(self) -> None:
        assert normalize_domain({}) == []

    def test_empty_string(self) -> None:
        assert normalize_domain("") == []

    def test_unparseable_string(self) -> None:
        assert normalize_domain("not json, not python") == []


class TestCanonicalFormat:
    def test_single_triple_list(self) -> None:
        result = normalize_domain([["name", "=", "Acme"]])
        assert result == [["name", "=", "Acme"]]

    def test_multiple_triples(self) -> None:
        result = normalize_domain([["name", "=", "Acme"], ["active", "=", True]])
        assert result == [["name", "=", "Acme"], ["active", "=", True]]

    def test_with_logic_operators(self) -> None:
        result = normalize_domain(["|", ["name", "=", "A"], ["name", "=", "B"]])
        assert result == ["|", ["name", "=", "A"], ["name", "=", "B"]]

    def test_with_and_operator(self) -> None:
        result = normalize_domain(["&", ["a", "=", 1], ["b", "=", 2]])
        assert result == ["&", ["a", "=", 1], ["b", "=", 2]]

    def test_with_not_operator(self) -> None:
        result = normalize_domain(["!", ["x", "=", 1]])
        assert result == ["!", ["x", "=", 1]]

    def test_value_can_be_any_type(self) -> None:
        result = normalize_domain([["ids", "in", [1, 2, 3]]])
        assert result == [["ids", "in", [1, 2, 3]]]

    def test_tuple_triples_normalized_to_lists(self) -> None:
        # Input with tuple; output should be list
        result = normalize_domain([("name", "=", "Acme")])
        assert result == [["name", "=", "Acme"]]


class TestAutoWrap:
    def test_single_triple_auto_wrapped(self) -> None:
        result = normalize_domain(["name", "=", "Acme"])
        assert result == [["name", "=", "Acme"]]

    def test_single_triple_int_value(self) -> None:
        result = normalize_domain(["id", "=", 42])
        assert result == [["id", "=", 42]]


class TestUnwrapDoubleNesting:
    def test_double_wrapped(self) -> None:
        result = normalize_domain([[["name", "=", "Acme"]]])
        assert result == [["name", "=", "Acme"]]

    def test_double_wrapped_multiple(self) -> None:
        result = normalize_domain([[["a", "=", 1], ["b", "=", 2]]])
        assert result == [["a", "=", 1], ["b", "=", 2]]


class TestObjectForm:
    def test_conditions_object(self) -> None:
        result = normalize_domain(
            {
                "conditions": [
                    {"field": "name", "operator": "=", "value": "Acme"},
                    {"field": "active", "operator": "=", "value": True},
                ]
            }
        )
        assert result == [
            ["name", "=", "Acme"],
            ["active", "=", True],
        ]

    def test_conditions_object_missing_keys_dropped(self) -> None:
        result = normalize_domain(
            {
                "conditions": [
                    {"field": "name", "operator": "=", "value": "Acme"},
                    {"field": "x"},  # missing operator + value
                ]
            }
        )
        assert result == [["name", "=", "Acme"]]

    def test_conditions_object_wrong_conditions_type(self) -> None:
        assert normalize_domain({"conditions": "not a list"}) == []

    def test_dict_without_conditions_key(self) -> None:
        assert normalize_domain({"other": "thing"}) == []


class TestStringForms:
    def test_json_list_of_triples(self) -> None:
        result = normalize_domain('[["name", "=", "Acme"]]')
        assert result == [["name", "=", "Acme"]]

    def test_json_object_form(self) -> None:
        result = normalize_domain(
            '{"conditions": [{"field": "name", "operator": "=", "value": "X"}]}'
        )
        assert result == [["name", "=", "X"]]

    def test_python_literal_fallback(self) -> None:
        # Single quotes — invalid JSON, valid Python literal
        result = normalize_domain("[['name', '=', 'Acme']]")
        assert result == [["name", "=", "Acme"]]

    def test_string_with_double_wrap_unwrapped(self) -> None:
        result = normalize_domain('[[["name", "=", "Acme"]]]')
        assert result == [["name", "=", "Acme"]]


class TestValidationDrops:
    def test_triple_with_non_string_field_dropped(self) -> None:
        result = normalize_domain([[1, "=", "value"]])
        assert result == []

    def test_triple_with_non_string_operator_dropped(self) -> None:
        result = normalize_domain([["field", 42, "value"]])
        assert result == []

    def test_too_short_triple_dropped(self) -> None:
        result = normalize_domain([["field", "="]])
        assert result == []

    def test_mixed_valid_and_invalid_keeps_valid(self) -> None:
        result = normalize_domain(
            [["good", "=", 1], "not-a-triple", ["bad", 42, 3], ["also_good", "=", 2]]
        )
        assert result == [["good", "=", 1], ["also_good", "=", 2]]

    def test_unknown_logic_operator_dropped(self) -> None:
        result = normalize_domain(["XOR", ["a", "=", 1]])
        # "XOR" is a 3-char string — not a triple, not a valid logic op
        assert result == [["a", "=", 1]]


class TestPurity:
    def test_input_list_not_mutated(self) -> None:
        original = [["name", "=", "Acme"]]
        snapshot = [list(c) for c in original]
        normalize_domain(original)
        assert original == snapshot

    def test_returns_independent_list(self) -> None:
        input_domain = [["name", "=", "Acme"]]
        result = normalize_domain(input_domain)
        result.append(["injected", "=", "bad"])
        assert input_domain == [["name", "=", "Acme"]]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
