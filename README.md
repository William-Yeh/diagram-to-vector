# Diagram to Vector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

Convert hand-drawn diagrams and whiteboard sketches into structured vector formats (Mermaid, draw.io, GraphViz, SVG).

## Overview

This tool captures screenshots from whiteboard URLs (tldraw, Excalidraw, Miro, Figma) or parses Excalidraw files directly, then converts them to editable vector formats.

**Supported outputs:** Mermaid, draw.io, GraphViz, SVG

## Installation

```bash
# Using uv (recommended)
uv pip install -r requirements.txt
uv run python -m playwright install chromium

# Or using pip with venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Quick Start

```bash
# Capture screenshot from whiteboard URL
python scripts/capture.py "https://www.tldraw.com/r/example" -o diagram.png

# For Excalidraw files, parse directly (no screenshot needed)
python scripts/parse_excalidraw.py input.excalidraw -o diagram.json

# Convert to Mermaid (default)
python scripts/convert.py diagram.json -f mermaid

# Convert to multiple formats
python scripts/convert.py diagram.json -f mermaid,drawio,svg
```

## Documentation

See [SKILL.md](SKILL.md) for complete documentation including:
- Detailed CLI options
- Intermediate JSON format specification
- Vision analysis prompts for Claude
- Style preservation details

## Claude Code Skill

Install as a Claude Code skill to enable diagram conversion directly in conversations:

```bash
npx @anthropic-ai/claude-code-skills add github:William-Yeh/diagram-to-vector
```

Then use `/diagram-to-vector` in Claude Code to convert diagrams.

## Author

William Yeh <william.pjyeh@gmail.com>

## License

MIT License - see [LICENSE](LICENSE) for details.
