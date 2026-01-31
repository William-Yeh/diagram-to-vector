#!/usr/bin/env python3
"""
convert.py
Convert diagram JSON to Mermaid, draw.io, GraphViz, or SVG.

Author: William Yeh <william.pjyeh@gmail.com>
License: MIT

Usage:
    python scripts/convert.py <input.json> -f <format> [options]
    python scripts/convert.py "*.json" -f mermaid -d output/

Formats: mermaid, drawio, graphviz, svg
"""

import json
import argparse
import sys
import os
import re
import html
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional


class DiagramConverter:
    """Converts intermediate diagram JSON to output formats."""
    
    DEFAULT_LAYOUTS = {
        'mermaid': 'structure', 'graphviz': 'structure',
        'drawio': 'position', 'svg': 'position'
    }
    
    MERMAID_SHAPES = {
        'rectangle': ('["', '"]'), 'diamond': ('{', '}'),
        'circle': ('(("', '"))'), 'ellipse': ('(["', '"])'),
        'cylinder': ('[("', '")]'), 'parallelogram': ('[/"', '"/]'),
    }
    
    DRAWIO_SHAPES = {
        'rectangle': 'rounded=0;whiteSpace=wrap;html=1;',
        'diamond': 'rhombus;whiteSpace=wrap;html=1;',
        'circle': 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;',
        'ellipse': 'ellipse;whiteSpace=wrap;html=1;',
        'cylinder': 'shape=cylinder3;whiteSpace=wrap;html=1;',
        'parallelogram': 'shape=parallelogram;whiteSpace=wrap;html=1;',
    }
    
    GRAPHVIZ_SHAPES = {
        'rectangle': 'box', 'diamond': 'diamond', 'circle': 'circle',
        'ellipse': 'ellipse', 'cylinder': 'cylinder', 'parallelogram': 'parallelogram',
    }
    
    def __init__(self, data: Dict[str, Any], layout_mode: Optional[str] = None):
        self.data = data
        self.layout_override = layout_mode
        self.nodes = {n['id']: n for n in data.get('nodes', [])}
        self.edges = data.get('edges', [])
        self.groups = data.get('groups', [])
        self.title = data.get('title', '')
    
    def get_layout(self, fmt: str) -> str:
        return self.layout_override or self.DEFAULT_LAYOUTS.get(fmt, 'structure')
    
    def _style_to_mermaid(self, node_id: str, style: Dict) -> Optional[str]:
        if not style:
            return None
        parts = []
        if style.get('fillColor'):
            parts.append(f"fill:{style['fillColor']}")
        if style.get('strokeColor'):
            parts.append(f"stroke:{style['strokeColor']}")
        if style.get('strokeWidth'):
            parts.append(f"stroke-width:{style['strokeWidth']}px")
        return f"style {node_id} {','.join(parts)}" if parts else None
    
    def to_mermaid(self) -> str:
        lines = []
        if self.title:
            lines.extend(['---', f'title: {self.title}', '---'])
        
        direction = 'TD'
        if self.get_layout('mermaid') == 'position' and self.nodes:
            xs = [n.get('x', 0) for n in self.nodes.values()]
            ys = [n.get('y', 0) for n in self.nodes.values()]
            if (max(xs) - min(xs)) > (max(ys) - min(ys)):
                direction = 'LR'
        
        lines.append(f'flowchart {direction}')
        
        grouped = set()
        for g in self.groups:
            grouped.update(g.get('nodeIds', []))
        
        for nid, node in sorted(self.nodes.items()):
            if nid in grouped:
                continue
            lines.append(self._mermaid_node(nid, node))
        
        for group in sorted(self.groups, key=lambda g: g.get('id', '')):
            gid, glabel = group.get('id', 'group'), group.get('label', '')
            lines.extend(['', f'    subgraph {gid}[{glabel}]'])
            for nid in sorted(group.get('nodeIds', [])):
                if nid in self.nodes:
                    lines.append('    ' + self._mermaid_node(nid, self.nodes[nid]))
            lines.append('    end')
        
        lines.append('')
        
        for edge in sorted(self.edges, key=lambda e: e.get('id', '')):
            fr, to = edge.get('from', ''), edge.get('to', '')
            label = edge.get('label', '')
            style = edge.get('style', {})
            arrow = '-.->' if style.get('strokeStyle') == 'dashed' else '-->'
            if edge.get('type') == 'line':
                arrow = '---'
            if label:
                lines.append(f'    {fr} {arrow}|{label}| {to}')
            else:
                lines.append(f'    {fr} {arrow} {to}')
        
        style_lines = []
        for nid, node in sorted(self.nodes.items()):
            s = self._style_to_mermaid(nid, node.get('style', {}))
            if s:
                style_lines.append(f'    {s}')
        if style_lines:
            lines.extend([''] + style_lines)
        
        return '\n'.join(lines)
    
    def _mermaid_node(self, nid: str, node: Dict) -> str:
        shape = node.get('type', 'rectangle')
        label = node.get('label', nid).replace('"', "'").replace('[', '(').replace(']', ')')
        pre, suf = self.MERMAID_SHAPES.get(shape, ('["', '"]'))
        return f'    {nid}{pre}{label}{suf}'
    
    def to_graphviz(self) -> str:
        lines = ['digraph G {', '    rankdir=TB;', '    node [fontname="Arial"];', '']
        if self.title:
            lines.insert(1, f'    label="{self.title}";')
        
        for nid, node in sorted(self.nodes.items()):
            shape = self.GRAPHVIZ_SHAPES.get(node.get('type', 'rectangle'), 'box')
            label = node.get('label', nid).replace('"', '\\"')
            attrs = [f'label="{label}"', f'shape={shape}']
            style = node.get('style', {})
            if style.get('fillColor'):
                attrs.extend([f'fillcolor="{style["fillColor"]}"', 'style=filled'])
            if style.get('strokeColor'):
                attrs.append(f'color="{style["strokeColor"]}"')
            lines.append(f'    {nid} [{", ".join(attrs)}];')
        
        lines.append('')
        
        for edge in sorted(self.edges, key=lambda e: e.get('id', '')):
            fr, to = edge.get('from', ''), edge.get('to', '')
            attrs = []
            if edge.get('label'):
                attrs.append(f'label="{edge["label"]}"')
            if edge.get('style', {}).get('strokeStyle') == 'dashed':
                attrs.append('style=dashed')
            attr_str = f' [{", ".join(attrs)}]' if attrs else ''
            lines.append(f'    {fr} -> {to}{attr_str};')
        
        for group in sorted(self.groups, key=lambda g: g.get('id', '')):
            lines.extend(['', f'    subgraph cluster_{group.get("id", "")} {{',
                         f'        label="{group.get("label", "")}";'])
            for nid in sorted(group.get('nodeIds', [])):
                lines.append(f'        {nid};')
            lines.append('    }')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def to_drawio(self) -> str:
        cells = []
        
        for nid, node in sorted(self.nodes.items()):
            shape = node.get('type', 'rectangle')
            label = html.escape(node.get('label', nid))
            base_style = self.DRAWIO_SHAPES.get(shape, self.DRAWIO_SHAPES['rectangle'])
            style_parts = [base_style]
            ns = node.get('style', {})
            if ns.get('fillColor'):
                style_parts.append(f"fillColor={ns['fillColor']};")
            if ns.get('strokeColor'):
                style_parts.append(f"strokeColor={ns['strokeColor']};")
            style = ''.join(style_parts)
            x, y = node.get('x', 0), node.get('y', 0)
            w, h = node.get('width', 120), node.get('height', 60)
            cells.append(f'''        <mxCell id="cell_{nid}" value="{label}" style="{style}" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>
        </mxCell>''')
        
        for edge in sorted(self.edges, key=lambda e: e.get('id', '')):
            eid = edge.get('id', '')
            fr, to = edge.get('from', ''), edge.get('to', '')
            label = html.escape(edge.get('label', ''))
            style = 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;'
            if edge.get('style', {}).get('strokeStyle') == 'dashed':
                style += 'dashed=1;'
            cells.append(f'''        <mxCell id="cell_{eid}" value="{label}" style="{style}" edge="1" parent="1" source="cell_{fr}" target="cell_{to}">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>''')
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="diagram-to-vector" type="device">
  <diagram name="Page-1" id="diagram_1">
    <mxGraphModel dx="1000" dy="600" grid="1" gridSize="10">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
{chr(10).join(cells)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    def to_svg(self) -> str:
        if not self.nodes:
            return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"></svg>'
        
        min_x = min(n.get('x', 0) for n in self.nodes.values())
        min_y = min(n.get('y', 0) for n in self.nodes.values())
        max_x = max(n.get('x', 0) + n.get('width', 120) for n in self.nodes.values())
        max_y = max(n.get('y', 0) + n.get('height', 60) for n in self.nodes.values())
        
        pad = 50
        width, height = max_x - min_x + pad*2, max_y - min_y + pad*2
        ox, oy = -min_x + pad, -min_y + pad
        
        elements = []
        
        for edge in sorted(self.edges, key=lambda e: e.get('id', '')):
            fn, tn = self.nodes.get(edge['from']), self.nodes.get(edge['to'])
            if not fn or not tn:
                continue
            x1 = fn['x'] + fn.get('width', 120)/2 + ox
            y1 = fn['y'] + fn.get('height', 60)/2 + oy
            x2 = tn['x'] + tn.get('width', 120)/2 + ox
            y2 = tn['y'] + tn.get('height', 60)/2 + oy
            dash = 'stroke-dasharray="8,4"' if edge.get('style', {}).get('strokeStyle') == 'dashed' else ''
            elements.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="2" {dash} marker-end="url(#arrow)"/>')
        
        for nid, node in sorted(self.nodes.items()):
            x, y = node['x'] + ox, node['y'] + oy
            w, h = node.get('width', 120), node.get('height', 60)
            label = html.escape(node.get('label', nid))
            style = node.get('style', {})
            fill = style.get('fillColor', '#fff')
            stroke = style.get('strokeColor', '#333')
            elements.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2" rx="5"/>')
            elements.append(f'  <text x="{x+w/2}" y="{y+h/2+5}" font-family="Arial" font-size="14" text-anchor="middle">{label}</text>')
        
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#333"/></marker></defs>
{chr(10).join(elements)}
</svg>'''
    
    def convert(self, fmt: str) -> str:
        return {'mermaid': self.to_mermaid, 'graphviz': self.to_graphviz,
                'drawio': self.to_drawio, 'svg': self.to_svg}[fmt.lower()]()


def get_ext(fmt: str) -> str:
    return {'mermaid': '.mmd', 'graphviz': '.dot', 'drawio': '.drawio', 'svg': '.svg'}.get(fmt, '.txt')


def main():
    parser = argparse.ArgumentParser(description='Convert diagram JSON to output formats')
    parser.add_argument('input', help='Input JSON file or glob pattern')
    parser.add_argument('--format', '-f', required=True, help='Format(s): mermaid,drawio,graphviz,svg')
    parser.add_argument('--output', '-o', help='Output file (single input)')
    parser.add_argument('--output-dir', '-d', default='.', help='Output directory')
    parser.add_argument('--layout', '-l', choices=['structure', 'position'])
    
    args = parser.parse_args()
    formats = [f.strip().lower() for f in args.format.split(',')]
    files = sorted(glob.glob(args.input))
    
    if not files:
        print(f"No files found: {args.input}")
        sys.exit(1)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    for path in files:
        with open(path) as f:
            data = json.load(f)
        conv = DiagramConverter(data, args.layout)
        base = Path(path).stem
        
        for fmt in formats:
            result = conv.convert(fmt)
            if args.output and len(files) == 1 and len(formats) == 1:
                out = args.output
            else:
                out = os.path.join(args.output_dir, f"{base}{get_ext(fmt)}")
            with open(out, 'w') as f:
                f.write(result)
            print(f"Created: {out}")
    
    print(f"\nConverted {len(files)} file(s)")


if __name__ == '__main__':
    main()
