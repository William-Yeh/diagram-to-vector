#!/usr/bin/env python3
"""Tests for convert.py - DiagramConverter and output formats."""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from convert import DiagramConverter, get_ext


class TestGetExt:
    """Tests for get_ext helper function."""

    def test_mermaid_extension(self):
        assert get_ext("mermaid") == ".mmd"

    def test_graphviz_extension(self):
        assert get_ext("graphviz") == ".dot"

    def test_drawio_extension(self):
        assert get_ext("drawio") == ".drawio"

    def test_svg_extension(self):
        assert get_ext("svg") == ".svg"

    def test_unknown_format_returns_txt(self):
        assert get_ext("unknown") == ".txt"


class TestDiagramConverterBasic:
    """Tests for DiagramConverter initialization and helpers."""

    def test_empty_diagram(self):
        conv = DiagramConverter({})
        assert conv.nodes == {}
        assert conv.edges == []
        assert conv.groups == []
        assert conv.title == ""

    def test_layout_defaults(self):
        conv = DiagramConverter({})
        assert conv.get_layout("mermaid") == "structure"
        assert conv.get_layout("graphviz") == "structure"
        assert conv.get_layout("drawio") == "position"
        assert conv.get_layout("svg") == "position"

    def test_layout_override(self):
        conv = DiagramConverter({}, layout_mode="position")
        assert conv.get_layout("mermaid") == "position"
        assert conv.get_layout("graphviz") == "position"


class TestMermaidConversion:
    """Tests for Mermaid output format."""

    def get_sample_data(self):
        return {
            "title": "Test Flow",
            "nodes": [
                {"id": "start", "type": "rectangle", "label": "Start", "x": 0, "y": 0},
                {"id": "process", "type": "rectangle", "label": "Process", "x": 100, "y": 0},
                {"id": "decision", "type": "diamond", "label": "OK?", "x": 200, "y": 0},
            ],
            "edges": [
                {"id": "e1", "from": "start", "to": "process"},
                {"id": "e2", "from": "process", "to": "decision", "label": "check"},
            ],
            "groups": [],
        }

    def test_mermaid_basic_structure(self):
        conv = DiagramConverter(self.get_sample_data())
        result = conv.to_mermaid()
        assert "flowchart" in result
        assert "start" in result
        assert "process" in result

    def test_mermaid_title(self):
        conv = DiagramConverter(self.get_sample_data())
        result = conv.to_mermaid()
        assert "title: Test Flow" in result

    def test_mermaid_diamond_shape(self):
        conv = DiagramConverter(self.get_sample_data())
        result = conv.to_mermaid()
        # Diamond uses { } syntax in Mermaid
        assert "decision{OK?}" in result

    def test_mermaid_edge_with_label(self):
        conv = DiagramConverter(self.get_sample_data())
        result = conv.to_mermaid()
        assert "|check|" in result

    def test_mermaid_dashed_edge(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A"},
                {"id": "b", "type": "rectangle", "label": "B"},
            ],
            "edges": [
                {"id": "e1", "from": "a", "to": "b", "style": {"strokeStyle": "dashed"}},
            ],
        }
        conv = DiagramConverter(data)
        result = conv.to_mermaid()
        assert "-.->" in result

    def test_mermaid_with_styles(self):
        data = {
            "nodes": [
                {
                    "id": "styled",
                    "type": "rectangle",
                    "label": "Styled",
                    "style": {"fillColor": "#ff0000", "strokeColor": "#000000"},
                }
            ],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_mermaid()
        assert "fill:#ff0000" in result
        assert "stroke:#000000" in result

    def test_mermaid_subgraph(self):
        data = {
            "nodes": [{"id": "n1", "type": "rectangle", "label": "Node 1"}],
            "edges": [],
            "groups": [{"id": "grp", "label": "My Group", "nodeIds": ["n1"]}],
        }
        conv = DiagramConverter(data)
        result = conv.to_mermaid()
        assert "subgraph grp[My Group]" in result
        assert "end" in result


class TestGraphvizConversion:
    """Tests for GraphViz output format."""

    def test_graphviz_basic_structure(self):
        data = {
            "nodes": [{"id": "start", "type": "rectangle", "label": "Start"}],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_graphviz()
        assert "digraph G {" in result
        assert "}" in result

    def test_graphviz_node_shapes(self):
        data = {
            "nodes": [
                {"id": "rect", "type": "rectangle", "label": "Box"},
                {"id": "dia", "type": "diamond", "label": "Diamond"},
                {"id": "circ", "type": "circle", "label": "Circle"},
            ],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_graphviz()
        assert "shape=box" in result
        assert "shape=diamond" in result
        assert "shape=circle" in result

    def test_graphviz_edge(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A"},
                {"id": "b", "type": "rectangle", "label": "B"},
            ],
            "edges": [{"id": "e1", "from": "a", "to": "b", "label": "connects"}],
        }
        conv = DiagramConverter(data)
        result = conv.to_graphviz()
        assert "a -> b" in result
        assert 'label="connects"' in result

    def test_graphviz_dashed_edge(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A"},
                {"id": "b", "type": "rectangle", "label": "B"},
            ],
            "edges": [
                {"id": "e1", "from": "a", "to": "b", "style": {"strokeStyle": "dashed"}}
            ],
        }
        conv = DiagramConverter(data)
        result = conv.to_graphviz()
        assert "style=dashed" in result

    def test_graphviz_cluster(self):
        data = {
            "nodes": [{"id": "n1", "type": "rectangle", "label": "N1"}],
            "edges": [],
            "groups": [{"id": "grp", "label": "Cluster", "nodeIds": ["n1"]}],
        }
        conv = DiagramConverter(data)
        result = conv.to_graphviz()
        assert "subgraph cluster_grp" in result
        assert 'label="Cluster"' in result


class TestDrawioConversion:
    """Tests for draw.io output format."""

    def test_drawio_xml_structure(self):
        data = {
            "nodes": [{"id": "n1", "type": "rectangle", "label": "Node", "x": 100, "y": 50}],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_drawio()
        assert '<?xml version="1.0"' in result
        assert "<mxfile" in result
        assert "<mxGraphModel" in result
        assert "</mxfile>" in result

    def test_drawio_node_cell(self):
        data = {
            "nodes": [
                {"id": "mynode", "type": "rectangle", "label": "My Node", "x": 100, "y": 50}
            ],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_drawio()
        assert 'id="cell_mynode"' in result
        assert 'value="My Node"' in result
        assert 'x="100"' in result
        assert 'y="50"' in result

    def test_drawio_edge_cell(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A", "x": 0, "y": 0},
                {"id": "b", "type": "rectangle", "label": "B", "x": 100, "y": 0},
            ],
            "edges": [{"id": "e1", "from": "a", "to": "b"}],
        }
        conv = DiagramConverter(data)
        result = conv.to_drawio()
        assert 'id="cell_e1"' in result
        assert 'source="cell_a"' in result
        assert 'target="cell_b"' in result

    def test_drawio_escapes_html(self):
        data = {
            "nodes": [{"id": "n", "type": "rectangle", "label": "A < B & C"}],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_drawio()
        assert "&lt;" in result
        assert "&amp;" in result


class TestSvgConversion:
    """Tests for SVG output format."""

    def test_svg_empty_diagram(self):
        conv = DiagramConverter({})
        result = conv.to_svg()
        assert "<svg" in result
        assert "</svg>" in result

    def test_svg_structure(self):
        data = {
            "nodes": [{"id": "n1", "type": "rectangle", "label": "Node", "x": 50, "y": 50}],
            "edges": [],
        }
        conv = DiagramConverter(data)
        result = conv.to_svg()
        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert "<rect" in result
        assert "<text" in result

    def test_svg_arrow_marker(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A", "x": 0, "y": 0},
                {"id": "b", "type": "rectangle", "label": "B", "x": 200, "y": 0},
            ],
            "edges": [{"id": "e1", "from": "a", "to": "b"}],
        }
        conv = DiagramConverter(data)
        result = conv.to_svg()
        assert "<defs>" in result
        assert 'id="arrow"' in result
        assert "<line" in result

    def test_svg_dashed_line(self):
        data = {
            "nodes": [
                {"id": "a", "type": "rectangle", "label": "A", "x": 0, "y": 0},
                {"id": "b", "type": "rectangle", "label": "B", "x": 200, "y": 0},
            ],
            "edges": [
                {"id": "e1", "from": "a", "to": "b", "style": {"strokeStyle": "dashed"}}
            ],
        }
        conv = DiagramConverter(data)
        result = conv.to_svg()
        assert "stroke-dasharray" in result


class TestConvertMethod:
    """Tests for the unified convert() method."""

    def test_convert_mermaid(self):
        conv = DiagramConverter({"nodes": [], "edges": []})
        result = conv.convert("mermaid")
        assert "flowchart" in result

    def test_convert_graphviz(self):
        conv = DiagramConverter({"nodes": [], "edges": []})
        result = conv.convert("graphviz")
        assert "digraph" in result

    def test_convert_drawio(self):
        conv = DiagramConverter({"nodes": [], "edges": []})
        result = conv.convert("drawio")
        assert "mxfile" in result

    def test_convert_svg(self):
        conv = DiagramConverter({"nodes": [], "edges": []})
        result = conv.convert("svg")
        assert "<svg" in result

    def test_convert_case_insensitive(self):
        conv = DiagramConverter({"nodes": [], "edges": []})
        assert "flowchart" in conv.convert("MERMAID")
        assert "digraph" in conv.convert("GraphViz")
