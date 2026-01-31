---
name: diagram-to-vector
description: Convert hand-drawn diagrams and whiteboard sketches into structured vector formats. Use when the user wants to convert a tldraw, Excalidraw, Miro, or other whiteboard URL to Mermaid, draw.io, GraphViz, or SVG. Also use when transforming an uploaded screenshot or image of a diagram into editable vector format. Supports batch processing of multiple files.
---

# Diagram to Vector Converter

Converts hand-drawn diagrams and whiteboard sketches into structured vector formats (Mermaid, draw.io, GraphViz, SVG).

## Quick Start

```bash
# Install dependencies
pip install playwright --break-system-packages
python -m playwright install chromium

# Capture screenshot from whiteboard URL
python scripts/capture.py "https://www.tldraw.com/r/example" -o diagram.png

# For Excalidraw files, parse directly (no screenshot needed)
python scripts/parse_excalidraw.py input.excalidraw -o diagram.json

# Convert to Mermaid (default)
python scripts/convert.py diagram.json

# Convert to multiple formats
python scripts/convert.py diagram.json -f mermaid,drawio,svg
```

## Workflow

1. **Capture** - Screenshot from URL or use uploaded image
2. **Analyze** - Use Claude vision to extract structure into JSON
3. **Convert** - Transform JSON to output format(s)

For Excalidraw files, skip steps 1-2 and parse directly with `parse_excalidraw.py`.

## Supported Inputs

| Source | Command |
|--------|---------|
| tldraw URL | `python scripts/capture.py "https://tldraw.com/..."` |
| Excalidraw URL | `python scripts/capture.py "https://excalidraw.com/..."` |
| Excalidraw file | `python scripts/parse_excalidraw.py input.excalidraw` |
| Miro, Figma, etc. | `python scripts/capture.py "<URL>"` |
| Uploaded image | Use directly with vision analysis |

## Output Formats

| Format | Extension | Best For |
|--------|-----------|----------|
| Mermaid | `.mmd` | Documentation, markdown, GitHub |
| draw.io | `.drawio` | Visual editing, detailed diagrams |
| GraphViz | `.dot` | Technical docs, auto-layout |
| SVG | `.svg` | Web embedding, further editing |

## capture.py Options

```bash
python scripts/capture.py <URL> [options]

  -o, --output <file>     Output filename (default: screenshot.png)
  -z, --zoom <float>      Zoom level (default: 1.0)
  -w, --wait <seconds>    Wait for render (default: 3)
  -r, --region <x,y,w,h>  Capture specific region
  --full-page             Capture full scrollable area
  --no-hide-ui            Keep toolbar/UI visible
```

Auto-detects whiteboard type and hides UI elements.

## convert.py Options

```bash
python scripts/convert.py <input> [options]

  -f, --format <fmt>      Format(s), comma-separated (default: mermaid)
  -o, --output <file>     Output filename (single file)
  -d, --output-dir <dir>  Output directory (batch mode)
  -l, --layout <mode>     structure (auto) or position (preserved)
```

**Layout defaults:** Mermaid/GraphViz → structure, draw.io/SVG → position

## Intermediate JSON Format

```json
{
  "diagramType": "flowchart",
  "title": "My Diagram",
  "nodes": [
    {
      "id": "process_data",
      "type": "rectangle",
      "label": "Process Data",
      "x": 100, "y": 200,
      "style": { "fillColor": "#fff3cd", "strokeColor": "#856404" },
      "confidence": 0.95
    }
  ],
  "edges": [
    {
      "id": "start_to_process",
      "from": "start",
      "to": "process_data",
      "label": "Begin",
      "style": { "strokeStyle": "dashed" }
    }
  ],
  "groups": [
    { "id": "main_flow", "label": "Main Flow", "nodeIds": ["start", "process_data"] }
  ]
}
```

See `assets/example.json` for a complete example.

## Vision Analysis

When analyzing diagram images with Claude, use the prompts in `assets/vision_prompts.md`:

1. **Pass 1 (Classification)** - Determines type, complexity, layout
2. **Pass 2 (Extraction)** - Type-specific detailed extraction

**Supported diagram types:** flowchart, sequence, architecture, ERD, mind map

## Style Preservation

| Style | Mermaid | GraphViz | draw.io | SVG |
|-------|---------|----------|---------|-----|
| Fill color | ✅ | ✅ | ✅ | ✅ |
| Stroke color | ✅ | ✅ | ✅ | ✅ |
| Dashed lines | ✅ | ✅ | ✅ | ✅ |

## VCS-Friendly Output

All outputs are deterministic for clean git diffs:
- Label-based IDs (`cell_process_data` not random UUIDs)
- No timestamps
- Sorted keys in JSON/XML
- Context-aware collision handling (`artifact_dev`, `artifact_prod`)

## Examples

**Convert tldraw to Mermaid:**
```bash
python scripts/capture.py "https://tldraw.com/r/xyz" -o sketch.png
# Use Claude vision to analyze → sketch.json
python scripts/convert.py sketch.json -f mermaid
```

**Batch convert:**
```bash
python scripts/convert.py "diagrams/*.json" -f mermaid,svg -d output/
```
