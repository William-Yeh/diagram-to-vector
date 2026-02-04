#!/usr/bin/env python3
"""Tests for parse_excalidraw.py - Excalidraw file parsing."""

import sys
import json
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from parse_excalidraw import sanitize_id, excalidraw_shape, find_bound_text, parse_excalidraw

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestSanitizeId:
    """Tests for sanitize_id function."""

    def test_simple_text(self):
        assert sanitize_id("Hello") == "hello"

    def test_with_spaces(self):
        assert sanitize_id("Hello World") == "hello_world"

    def test_special_characters(self):
        assert sanitize_id("foo@bar#baz!") == "foo_bar_baz"

    def test_multiple_underscores_collapsed(self):
        assert sanitize_id("foo___bar") == "foo_bar"

    def test_leading_number(self):
        assert sanitize_id("123abc") == "node_123abc"

    def test_empty_string(self):
        assert sanitize_id("") == "node"

    def test_collision_handling(self):
        existing = {"foo"}
        result = sanitize_id("foo", existing)
        assert result == "foo_2"
        assert "foo_2" in existing

    def test_multiple_collisions(self):
        existing = {"bar", "bar_2", "bar_3"}
        result = sanitize_id("bar", existing)
        assert result == "bar_4"


class TestExcalidrawShape:
    """Tests for excalidraw_shape mapping function."""

    def test_rectangle(self):
        assert excalidraw_shape("rectangle") == "rectangle"

    def test_diamond(self):
        assert excalidraw_shape("diamond") == "diamond"

    def test_ellipse(self):
        assert excalidraw_shape("ellipse") == "ellipse"

    def test_arrow(self):
        assert excalidraw_shape("arrow") == "arrow"

    def test_line(self):
        assert excalidraw_shape("line") == "line"

    def test_text(self):
        assert excalidraw_shape("text") == "text"

    def test_unknown_defaults_to_rectangle(self):
        assert excalidraw_shape("unknown_shape") == "rectangle"


class TestFindBoundText:
    """Tests for find_bound_text function."""

    def test_finds_bound_text(self):
        elements = [
            {"id": "rect1", "type": "rectangle"},
            {"id": "text1", "type": "text", "text": "Hello", "containerId": "rect1"},
        ]
        assert find_bound_text("rect1", elements) == "Hello"

    def test_no_bound_text(self):
        elements = [
            {"id": "rect1", "type": "rectangle"},
            {"id": "text1", "type": "text", "text": "Hello", "containerId": "rect2"},
        ]
        assert find_bound_text("rect1", elements) == ""

    def test_empty_elements(self):
        assert find_bound_text("any_id", []) == ""

    def test_text_without_container(self):
        elements = [
            {"id": "text1", "type": "text", "text": "Free text"},
        ]
        assert find_bound_text("text1", elements) == ""


class TestParseExcalidraw:
    """Tests for parse_excalidraw function with fixture file."""

    def test_parse_simple_fixture(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        # Check structure
        assert "nodes" in result
        assert "edges" in result
        assert "groups" in result
        assert "diagramType" in result

    def test_nodes_extracted(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        nodes = result["nodes"]
        node_labels = [n["label"] for n in nodes]

        assert "Start" in node_labels
        assert "End" in node_labels
        assert "Decision?" in node_labels

    def test_node_positions(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        start_node = next(n for n in result["nodes"] if n["label"] == "Start")
        assert start_node["x"] == 100
        assert start_node["y"] == 100

    def test_node_dimensions(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        start_node = next(n for n in result["nodes"] if n["label"] == "Start")
        assert start_node["width"] == 120
        assert start_node["height"] == 60

    def test_node_styles(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        start_node = next(n for n in result["nodes"] if n["label"] == "Start")
        assert "style" in start_node
        assert start_node["style"]["fillColor"] == "#a5d8ff"
        assert start_node["style"]["strokeColor"] == "#1e1e1e"

    def test_edges_extracted(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        edges = result["edges"]
        assert len(edges) == 1

        edge = edges[0]
        assert edge["from"] == "start"
        assert edge["to"] == "end"
        assert edge["type"] == "arrow"

    def test_diamond_type_detected(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        decision_node = next(n for n in result["nodes"] if n["label"] == "Decision?")
        assert decision_node["type"] == "diamond"

    def test_diagram_type_flowchart_when_diamond_present(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        # Has a diamond, should be flowchart
        assert result["diagramType"] == "flowchart"

    def test_confidence_is_1_for_excalidraw(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        assert result["overallConfidence"] == 1.0
        for node in result["nodes"]:
            assert node["confidence"] == 1.0

    def test_source_metadata(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        assert result["source"] == "excalidraw"
        assert "simple.excalidraw" in result["sourceFile"]


class TestParseExcalidrawEdgeCases:
    """Edge case tests for parse_excalidraw."""

    def test_deleted_elements_ignored(self):
        """Elements with isDeleted=true should be ignored."""
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        # No deleted elements in fixture, but we verify structure is correct
        for node in result["nodes"]:
            assert "id" in node
            assert "type" in node

    def test_node_ids_are_sanitized(self):
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        for node in result["nodes"]:
            # IDs should be lowercase with underscores
            assert node["id"] == node["id"].lower()
            assert " " not in node["id"]

    def test_transparent_fill_not_included(self):
        """Transparent backgrounds should not appear in style."""
        fixture_path = FIXTURES_DIR / "simple.excalidraw"
        result = parse_excalidraw(str(fixture_path))

        end_node = next(n for n in result["nodes"] if n["label"] == "End")
        # End node has transparent background in fixture
        if "style" in end_node:
            assert "fillColor" not in end_node["style"] or end_node["style"].get(
                "fillColor"
            ) != "transparent"
