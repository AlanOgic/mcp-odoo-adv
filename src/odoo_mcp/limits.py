"""Smart-limit policy for Odoo search/read operations.

Prevents accidentally returning massive datasets (e.g. all ``mail.message``
rows) when callers forget to pass a ``limit``. Pure functions — no logging
side effects. Callers receive a list of warning strings and emit them
however they like.
"""

from __future__ import annotations

from typing import Any, Tuple

DEFAULT_LIMIT: int = 100
MAX_LIMIT: int = 1000

SEARCH_METHODS: frozenset[str] = frozenset({"search", "search_count", "search_read"})

_MISSING: Any = object()


def apply_limits(
    method: str, kwargs: dict[str, Any]
) -> Tuple[dict[str, Any], list[str]]:
    """Apply smart-limit policy to ``kwargs`` for ``method``.

    Returns ``(new_kwargs, warnings)``. Does not mutate the input dict.

    Rules (only applied when ``method`` is a search method):
        * ``limit`` missing or ``None`` → set to ``DEFAULT_LIMIT``
        * ``limit == 0`` or ``limit is False`` → kept (unlimited) with a warning
        * ``limit > MAX_LIMIT`` → capped to ``MAX_LIMIT`` with a warning
    """
    if method not in SEARCH_METHODS:
        return kwargs, []

    new_kwargs = dict(kwargs)
    warnings: list[str] = []
    limit = new_kwargs.get("limit", _MISSING)

    if limit is _MISSING or limit is None:
        new_kwargs["limit"] = DEFAULT_LIMIT
        label = "missing" if limit is _MISSING else "None"
        warnings.append(
            f"No limit specified for {method} ({label}); "
            f"applying default limit={DEFAULT_LIMIT}"
        )
    elif limit is False or limit == 0:
        warnings.append(
            "Unlimited query requested (limit=0); " "this may return massive datasets"
        )
    elif isinstance(limit, int) and limit > MAX_LIMIT:
        warnings.append(
            f"Requested limit={limit} exceeds MAX_LIMIT={MAX_LIMIT}; "
            f"capping to limit={MAX_LIMIT}"
        )
        new_kwargs["limit"] = MAX_LIMIT

    return new_kwargs, warnings


def warn_large_read(args: list) -> list[str]:
    """Return a warning when a ``read(ids, fields)`` call has a huge id list."""
    if args and isinstance(args[0], list) and len(args[0]) > MAX_LIMIT:
        return [f"Reading {len(args[0])} records at once; consider batching."]
    return []


def warn_large_result(result: Any) -> list[str]:
    """Return a warning when a result list is at or above ``MAX_LIMIT``."""
    if isinstance(result, list) and len(result) >= MAX_LIMIT:
        return [f"Large result set: {len(result)} records. Consider adding filters."]
    return []
