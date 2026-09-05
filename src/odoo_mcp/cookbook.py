"""Read/write the Learned Patterns section of COOKBOOK.md.

The cookbook is a living document of patterns that took ≥4 failed attempts
to discover. Surfacing it as an MCP resource lets clients consult it after
their first failure; surfacing the writer as an MCP tool lets clients add
new patterns once they finally succeed.

Pure functions — no logging side effects. The MCP wrappers in
``odoo_mcp.server`` translate the dict results into JSON envelopes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

# Threshold below which trial-and-error isn't worth documenting.
MIN_FAILED_APPROACHES: int = 4

_SECTION_HEADING: str = "## 🧠 Learned Patterns"
_HOW_TO_USE_HEADING: str = "### How to Use This Section"


def find_cookbook(candidates: Iterable[Path]) -> Optional[Path]:
    """Return the first existing path from ``candidates`` (or ``None``)."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def default_cookbook_paths() -> list[Path]:
    """Locations to check when no explicit path is provided.

    Order: source checkout, parent of source checkout (editable installs),
    Docker container layout.
    """
    here = Path(__file__).resolve()
    return [
        here.parent.parent.parent / "COOKBOOK.md",
        here.parent.parent.parent.parent / "COOKBOOK.md",
        Path("/app/COOKBOOK.md"),
    ]


def read_patterns(cookbook_path: Path) -> dict[str, Any]:
    """Extract the Learned Patterns section from ``cookbook_path``.

    Returns a dict with ``found`` (bool) plus either ``content`` (the
    section as markdown) or an ``error``/``message`` describing why nothing
    was returned. Never raises for the common cases.
    """
    if not cookbook_path.exists():
        return {
            "found": False,
            "error": f"COOKBOOK.md not found at {cookbook_path}",
        }

    try:
        content = cookbook_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "found": False,
            "error": f"Failed to read {cookbook_path}: {exc}",
        }

    start = content.find(_SECTION_HEADING)
    if start == -1:
        return {
            "found": False,
            "message": (
                "No Learned Patterns section yet — patterns are added after "
                f"≥{MIN_FAILED_APPROACHES} failed attempts on a problem."
            ),
        }

    # Stop at the next top-level heading (## ...) or end of file.
    next_section = content.find("\n## ", start + 1)
    section = content[start:next_section] if next_section != -1 else content[start:]

    return {
        "found": True,
        "source": str(cookbook_path),
        "section": "Learned Patterns (Experience-Based)",
        "content": section.strip(),
    }


def add_pattern(
    cookbook_path: Path,
    *,
    problem: str,
    failed_approaches: list[str],
    working_solution: str,
    why_it_works: str,
    key_lesson: str,
    related_links: str = "",
) -> dict[str, Any]:
    """Insert a new pattern entry just before the "How to Use" footer.

    Validates the ≥4-failed-approaches threshold before touching the file.
    Returns ``{"success": bool, ...}``; never raises for the common cases.
    """
    if len(failed_approaches) < MIN_FAILED_APPROACHES:
        return {
            "success": False,
            "error": (
                f"Need at least {MIN_FAILED_APPROACHES} failed approaches "
                f"(got {len(failed_approaches)}). Only document significant "
                "trial-and-error."
            ),
        }

    if not cookbook_path.exists():
        return {
            "success": False,
            "error": f"COOKBOOK.md not found at {cookbook_path}",
        }

    try:
        content = cookbook_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "success": False,
            "error": f"Failed to read {cookbook_path}: {exc}",
        }

    marker_pos = content.find(_HOW_TO_USE_HEADING)
    if marker_pos == -1:
        return {
            "success": False,
            "error": (
                f"Could not find insertion point ({_HOW_TO_USE_HEADING!r}) "
                f"in {cookbook_path}"
            ),
        }

    new_pattern = _format_pattern(
        problem=problem,
        failed_approaches=failed_approaches,
        working_solution=working_solution,
        why_it_works=why_it_works,
        key_lesson=key_lesson,
        related_links=related_links,
    )

    new_content = content[:marker_pos] + new_pattern + "\n\n" + content[marker_pos:]

    try:
        cookbook_path.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return {
            "success": False,
            "error": f"Failed to write {cookbook_path}: {exc}",
        }

    return {
        "success": True,
        "message": f"✅ New pattern documented: {problem}",
        "pattern_summary": {
            "problem": problem,
            "failed_attempts": len(failed_approaches),
            "location": str(cookbook_path),
        },
        "announcement": f"✅ New pattern documented: {key_lesson}",
    }


def _format_pattern(
    *,
    problem: str,
    failed_approaches: list[str],
    working_solution: str,
    why_it_works: str,
    key_lesson: str,
    related_links: str,
) -> str:
    """Render a pattern entry as markdown ready to splice into COOKBOOK.md."""
    failed_lines = "\n".join(
        f"{i + 1}. ❌ {approach}" for i, approach in enumerate(failed_approaches)
    )
    pattern = (
        "\n\n---\n\n"
        f"### Pattern: {problem}\n\n"
        f"**Problem**: {problem}\n\n"
        "**Failed Approaches**:\n"
        f"{failed_lines}\n\n"
        "**Working Solution**:\n"
        "```python\n"
        f"{working_solution}\n"
        "```\n\n"
        f"**Why It Works**: {why_it_works}\n\n"
        f"**Key Lesson**: {key_lesson}\n"
    )
    if related_links:
        pattern += f"\n**Related**: {related_links}\n"
    return pattern
