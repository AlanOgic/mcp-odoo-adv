"""Cross-operation result references for ``batch_execute``.

Each operation in a batch is an independent Odoo call, so a later operation
needs a way to consume an earlier one's result (the classic case: create a
partner, then use its id as ``partner_id`` on a sale order).

Any string of the exact form ``"@N"`` (1-indexed) appearing anywhere inside an
operation's args or kwargs is replaced with the result of operation N::

    [{"model": "res.partner", "method": "create", "args": [{"name": "Acme"}]},
     {"model": "sale.order",  "method": "create", "args": [{"partner_id": "@1"}]}]

Only exact matches are substituted, so ordinary strings that merely contain an
``@`` (email addresses, ``"@mentions"``) pass through untouched.

Pure functions — no I/O, no logging side effects.
"""

from __future__ import annotations

import re
from typing import Any

_REFERENCE = re.compile(r"^@(\d+)$")


class BatchReferenceError(ValueError):
    """Raised when an ``"@N"`` reference cannot be resolved."""


class _Failed:
    """Placeholder recorded for an operation that produced no result."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<failed operation>"


#: Recorded in place of a result so that ``"@N"`` indices stay aligned with
#: operation numbers even when an earlier operation failed.
FAILED: Any = _Failed()


def substitute_references(value: Any, results: list[Any]) -> Any:
    """Recursively replace ``"@N"`` strings in ``value`` with ``results[N-1]``.

    ``results`` holds the results of the operations already executed, in order.
    Containers are rebuilt rather than mutated, so ``value`` is left untouched.

    Raises:
        BatchReferenceError: for ``"@0"`` (references are 1-indexed) or for a
            reference to an operation that has not executed yet.
    """
    if isinstance(value, str):
        match = _REFERENCE.match(value)
        if match is None:
            return value
        return _resolve(int(match.group(1)), results)

    if isinstance(value, dict):
        return {k: substitute_references(v, results) for k, v in value.items()}

    if isinstance(value, list):
        return [substitute_references(item, results) for item in value]

    if isinstance(value, tuple):
        return tuple(substitute_references(item, results) for item in value)

    return value


def _resolve(index: int, results: list[Any]) -> Any:
    """Return ``results[index - 1]`` or raise with an actionable message."""
    if index < 1:
        raise BatchReferenceError(
            "Invalid reference '@0': operation references are 1-indexed; "
            "the first operation is '@1'."
        )
    if index > len(results):
        raise BatchReferenceError(
            f"Cannot resolve '@{index}': only {len(results)} operation(s) have "
            "run. References may only point at earlier operations."
        )
    value = results[index - 1]
    if isinstance(value, _Failed):
        raise BatchReferenceError(
            f"Cannot resolve '@{index}': operation {index} failed, so it has "
            "no result to reference."
        )
    return value


def has_references(value: Any) -> bool:
    """Return True when ``value`` contains at least one ``"@N"`` reference."""
    if isinstance(value, str):
        return _REFERENCE.match(value) is not None
    if isinstance(value, dict):
        return any(has_references(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_references(item) for item in value)
    return False
