#!/usr/bin/env python3
"""
parse_excalidraw.py
Parse Excalidraw JSON files directly into intermediate format (no vision needed).

Author: William Yeh <william.pjyeh@gmail.com>
License: MIT

Usage:
    python scripts/parse_excalidraw.py input.excalidraw -o diagram.json
"""

import argparse
import json
import sys
import re
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional


def sanitize_id(text: str, existing: set = None) -> str:
    """Convert text to valid snake_case identifier."""
    if not text:
        text = "node"
    sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', text.lower())
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    if not sanitized or sanitized[0].isdigit():
        sanitized = 'node_' + sanitized
    if existing:
        orig, i = sanitized, 2
        while sanitized in existing:
            sanitized = f"{orig}_{i}"
            i += 1
        existing.add(sanitized)
    return sanitized


def excalidraw_shape(shape: str) -> str:
    """Map Excalidraw shapes to standard types."""
    return {'rectangle': 'rectangle', 'diamond': 'diamond', 'ellipse': 'ellipse',
            'arrow': 'arrow', 'line': 'line', 'text': 'text'}.get(shape, 'rectangle')


def find_bound_text(eid: str, elements: List[Dict]) -> str:
    """Find text bound to an element."""
    for el in elements:
        if el.get('type') == 'text' and el.get('containerId') == eid:
            return el.get('text', '')
    return ''


def parse_excalidraw(path: str) -> Dict[str, Any]:
    """Parse Excalidraw file into intermediate format."""
    with open(path, 'r') as f:
        data = json.load(f)
    
    elements = data.get('elements', [])
    id_map, existing = {}, set()
    nodes, edges, groups = [], [], []
    
    # First pass: shapes
    for el in elements:
        if el.get('type') in ('arrow', 'line', 'text') or el.get('isDeleted'):
            continue
        
        label = find_bound_text(el.get('id'), elements) or el.get('text', '') or f"Shape {len(nodes)+1}"
        nid = sanitize_id(label, existing)
        id_map[el.get('id')] = nid
        
        style = {}
        if el.get('backgroundColor') and el.get('backgroundColor') != 'transparent':
            style['fillColor'] = el.get('backgroundColor')
        if el.get('strokeColor'):
            style['strokeColor'] = el.get('strokeColor')
        
        node = {
            'id': nid, 'type': excalidraw_shape(el.get('type', '')),
            'label': label.strip(),
            'x': round(el.get('x', 0)), 'y': round(el.get('y', 0)),
            'width': round(el.get('width', 100)), 'height': round(el.get('height', 50)),
            'confidence': 1.0
        }
        if style:
            node['style'] = style
        nodes.append(node)
    
    # Second pass: arrows/lines
    for el in elements:
        if el.get('type') not in ('arrow', 'line') or el.get('isDeleted'):
            continue
        
        start = el.get('startBinding', {}).get('elementId')
        end = el.get('endBinding', {}).get('elementId')
        if not start or not end:
            continue
        
        fr, to = id_map.get(start), id_map.get(end)
        if not fr or not to:
            continue
        
        edge = {
            'id': f"{fr}_to_{to}", 'from': fr, 'to': to,
            'type': 'arrow' if el.get('type') == 'arrow' else 'line',
            'confidence': 1.0
        }
        label = find_bound_text(el.get('id'), elements)
        if label:
            edge['label'] = label.strip()
        
        style = {}
        if el.get('strokeStyle') == 'dashed':
            style['strokeStyle'] = 'dashed'
        if style:
            edge['style'] = style
        edges.append(edge)
    
    # Third pass: frames as groups
    for el in elements:
        if el.get('type') == 'frame' and not el.get('isDeleted'):
            gid = sanitize_id(el.get('name', 'Group'), existing)
            contained = [id_map[e['id']] for e in elements 
                        if e.get('frameId') == el.get('id') and e.get('id') in id_map]
            if contained:
                groups.append({'id': gid, 'label': el.get('name', 'Group'), 'nodeIds': contained})
    
    return {
        'diagramType': 'flowchart' if any(n['type'] == 'diamond' for n in nodes) else 'architecture',
        'source': 'excalidraw', 'sourceFile': path,
        'overallConfidence': 1.0,
        'nodes': nodes, 'edges': edges, 'groups': groups
    }


def main():
    parser = argparse.ArgumentParser(description='Parse Excalidraw files')
    parser.add_argument('input', help='Input .excalidraw file or glob')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--output-dir', '-d', default='.', help='Output directory')
    
    args = parser.parse_args()
    files = glob.glob(args.input)
    
    if not files:
        print(f"No files found: {args.input}")
        sys.exit(1)
    
    for path in files:
        out = args.output if args.output and len(files) == 1 else \
              str(Path(args.output_dir) / f"{Path(path).stem}.json")
        result = parse_excalidraw(path)
        with open(out, 'w') as f:
            json.dump(result, f, indent=2, sort_keys=True)
        print(f"Created: {out} ({len(result['nodes'])} nodes, {len(result['edges'])} edges)")


if __name__ == '__main__':
    main()
