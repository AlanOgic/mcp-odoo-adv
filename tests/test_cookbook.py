"""Tests for ``odoo_mcp.cookbook`` (read/write Learned Patterns)."""
from __future__ import annotations

from pathlib import Path

import pytest

from odoo_mcp.cookbook import (
    MIN_FAILED_APPROACHES,
    add_pattern,
    find_cookbook,
    read_patterns,
)


# ---- read_patterns ---------------------------------------------------------


class TestReadPatterns:
    def test_missing_file(self, tmp_path: Path) -> None:
        result = read_patterns(tmp_path / "nope.md")
        assert result["found"] is False
        assert "not found" in result["error"].lower()

    def test_no_section(self, tmp_path: Path) -> None:
        cookbook = tmp_path / "COOKBOOK.md"
        cookbook.write_text("# Title\n\nSome content but no Learned Patterns.\n")
        result = read_patterns(cookbook)
        assert result["found"] is False
        assert "no learned patterns" in result["message"].lower()

    def test_section_alone(self, tmp_path: Path) -> None:
        cookbook = tmp_path / "COOKBOOK.md"
        cookbook.write_text(
            "# Title\n\n## 🧠 Learned Patterns\n\nFirst recipe content.\n"
        )
        result = read_patterns(cookbook)
        assert result["found"] is True
        assert "First recipe content." in result["content"]
        assert result["content"].startswith("## 🧠 Learned Patterns")

    def test_section_followed_by_others(self, tmp_path: Path) -> None:
        cookbook = tmp_path / "COOKBOOK.md"
        cookbook.write_text(
            "# Title\n\n"
            "## 🧠 Learned Patterns\n\nKept content.\n\n"
            "## Another Section\n\nDropped content.\n"
        )
        result = read_patterns(cookbook)
        assert result["found"] is True
        assert "Kept content." in result["content"]
        assert "Dropped content." not in result["content"]


# ---- find_cookbook ---------------------------------------------------------


class TestFindCookbook:
    def test_returns_first_existing(self, tmp_path: Path) -> None:
        wanted = tmp_path / "COOKBOOK.md"
        wanted.write_text("hello")
        decoy = tmp_path / "missing.md"
        result = find_cookbook([decoy, wanted])
        assert result == wanted

    def test_returns_none_when_all_missing(self, tmp_path: Path) -> None:
        result = find_cookbook([tmp_path / "a.md", tmp_path / "b.md"])
        assert result is None


# ---- add_pattern -----------------------------------------------------------


@pytest.fixture
def cookbook_with_marker(tmp_path: Path) -> Path:
    """A COOKBOOK.md containing the 'How to Use This Section' marker."""
    cookbook = tmp_path / "COOKBOOK.md"
    cookbook.write_text(
        "# Cookbook\n\n"
        "## 🧠 Learned Patterns\n\n"
        "Some intro text.\n\n"
        "### How to Use This Section\n\n"
        "Workflow description.\n\n"
        "---\n\n"
        "## Final Section\n\nTrailer.\n"
    )
    return cookbook


def _four_approaches() -> list[str]:
    return [
        "Tried using = on m2m field",
        "Tried dotted notation",
        "Tried wrong model",
        "Tried single int instead of list",
    ]


class TestAddPatternValidation:
    def test_rejects_under_threshold(self, cookbook_with_marker: Path) -> None:
        result = add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=["one", "two", "three"],
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        assert result["success"] is False
        assert str(MIN_FAILED_APPROACHES) in result["error"]

    def test_accepts_exactly_threshold(self, cookbook_with_marker: Path) -> None:
        result = add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        assert result["success"] is True

    def test_rejects_when_marker_missing(self, tmp_path: Path) -> None:
        cookbook = tmp_path / "COOKBOOK.md"
        cookbook.write_text("# No marker here\n")
        result = add_pattern(
            cookbook,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        assert result["success"] is False
        assert "How to Use This Section" in result["error"]

    def test_rejects_missing_file(self, tmp_path: Path) -> None:
        result = add_pattern(
            tmp_path / "missing.md",
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestAddPatternContent:
    def test_inserts_before_how_to_use_marker(
        self, cookbook_with_marker: Path
    ) -> None:
        add_pattern(
            cookbook_with_marker,
            problem="Search m2m fields",
            failed_approaches=_four_approaches(),
            working_solution='execute_method(...)',
            why_it_works="m2m needs in operator",
            key_lesson="Use in for many2many",
        )
        new_content = cookbook_with_marker.read_text()
        pattern_pos = new_content.find("### Pattern: Search m2m fields")
        marker_pos = new_content.find("### How to Use This Section")
        assert pattern_pos != -1
        assert marker_pos != -1
        assert pattern_pos < marker_pos

    def test_includes_all_failed_approaches_numbered(
        self, cookbook_with_marker: Path
    ) -> None:
        add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        new_content = cookbook_with_marker.read_text()
        assert "1. ❌ Tried using = on m2m field" in new_content
        assert "2. ❌ Tried dotted notation" in new_content
        assert "3. ❌ Tried wrong model" in new_content
        assert "4. ❌ Tried single int instead of list" in new_content

    def test_omits_related_when_empty(self, cookbook_with_marker: Path) -> None:
        add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        assert "**Related**:" not in cookbook_with_marker.read_text()

    def test_includes_related_when_provided(
        self, cookbook_with_marker: Path
    ) -> None:
        add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
            related_links="https://example.com/docs",
        )
        text = cookbook_with_marker.read_text()
        assert "**Related**: https://example.com/docs" in text

    def test_preserves_content_after_marker(
        self, cookbook_with_marker: Path
    ) -> None:
        add_pattern(
            cookbook_with_marker,
            problem="X",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="lesson",
        )
        text = cookbook_with_marker.read_text()
        assert "## Final Section" in text
        assert "Trailer." in text

    def test_returns_summary(self, cookbook_with_marker: Path) -> None:
        result = add_pattern(
            cookbook_with_marker,
            problem="m2m search",
            failed_approaches=_four_approaches(),
            working_solution="code",
            why_it_works="reason",
            key_lesson="Use in for many2many",
        )
        assert result["pattern_summary"]["problem"] == "m2m search"
        assert result["pattern_summary"]["failed_attempts"] == 4
        assert "m2m search" in result["message"]
        assert "Use in for many2many" in result["announcement"]
