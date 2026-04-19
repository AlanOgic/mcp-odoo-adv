"""Odoo search-domain normalization.

Accepts the various shapes callers (especially LLMs) emit and returns a
canonical Odoo domain list of ``[field, operator, value]`` triples plus
the logic operators ``"&"``, ``"|"``, ``"!"``.

Supported input shapes:
    * Already-canonical list of triples — passes through, validated
    * Single triple ``["field", "op", value]`` — auto-wrapped in a list
    * Doubly-wrapped ``[[triple]]`` — unwrapped
    * Object form ``{"conditions": [{"field": ..., "operator": ..., "value": ...}]}``
    * JSON string of any of the above
    * Python-literal string (fallback via ``ast.literal_eval``)
    * ``None`` or empty — returns ``[]`` (match-all)

Invalid conditions are dropped silently. Callers that care about strictness
can compare input length to output length after normalization.
"""
from __future__ import annotations

import ast
import json
from typing import Any

_LOGIC_OPS = frozenset({"&", "|", "!"})


def normalize_domain(value: Any) -> list:
    """Return a canonical Odoo domain list from any supported input shape."""
    if value is None:
        return []

    # Unwrap [[domain]] → [domain] one level deep
    if (
        isinstance(value, list)
        and len(value) == 1
        and isinstance(value[0], list)
    ):
        value = value[0]

    # Parse string forms first
    if isinstance(value, str):
        value = _parse_string(value)
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]

    # Object form → list of triples
    if isinstance(value, dict):
        value = _conditions_to_triples(value)

    if not isinstance(value, list):
        return []

    if not value:
        return []

    # Single triple auto-wrap: ["field", "op", val] → [["field", "op", val]]
    if (
        len(value) == 3
        and isinstance(value[0], str)
        and value[0] not in _LOGIC_OPS
        and isinstance(value[1], str)
    ):
        value = [list(value)]

    return _validate_triples(value)


def _parse_string(s: str) -> Any:
    """JSON first, Python-literal as fallback, ``[]`` on total failure."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(s)
        except (ValueError, SyntaxError):
            return []


def _conditions_to_triples(obj: dict) -> list:
    """Translate ``{"conditions": [{field, operator, value}, ...]}`` to triples."""
    conditions = obj.get("conditions", [])
    if not isinstance(conditions, list):
        return []
    triples: list = []
    for cond in conditions:
        if isinstance(cond, dict) and all(
            k in cond for k in ("field", "operator", "value")
        ):
            triples.append([cond["field"], cond["operator"], cond["value"]])
    return triples


def _validate_triples(domain: list) -> list:
    """Keep only valid triples and logic operators; drop anything else."""
    valid: list = []
    for cond in domain:
        if isinstance(cond, str) and cond in _LOGIC_OPS:
            valid.append(cond)
        elif (
            isinstance(cond, (list, tuple))
            and len(cond) == 3
            and isinstance(cond[0], str)
            and isinstance(cond[1], str)
        ):
            valid.append(list(cond))
    return valid
