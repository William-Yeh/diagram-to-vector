# Vision Prompts for Diagram Analysis

Two-pass analysis for accurate diagram recognition.

## Pass 1: Classification

Use for initial analysis to determine type and complexity.

```
Analyze this diagram and classify it. Return JSON only:

{
  "diagramType": "<flowchart|sequence|architecture|mindmap|erd|freeform>",
  "layoutDirection": "<top-down|left-right|radial|hierarchical|freeform>",
  "complexity": "<simple|medium|complex>",
  "estimatedNodeCount": <number>,
  "patterns": [<list>],
  "description": "<one sentence>"
}

Complexity: simple ≤5 nodes, medium 6-15, complex >15
Patterns: swimlanes, nested_groups, annotations, color_coding, decision_branches
```

## Pass 2: Detailed Extraction

Use for medium/complex diagrams after Pass 1.

### Flowchart

```
Extract this flowchart as JSON:

{
  "nodes": [
    {
      "id": "<label_as_snake_case>",
      "type": "<rectangle|diamond|circle|ellipse|parallelogram|cylinder>",
      "label": "<exact text>",
      "x": <approx_x>, "y": <approx_y>,
      "width": <approx_width>, "height": <approx_height>,
      "style": {"fillColor": "<hex>", "strokeColor": "<hex>"},
      "confidence": <0.0-1.0>
    }
  ],
  "edges": [
    {
      "id": "<from>_to_<to>",
      "from": "<source_id>", "to": "<target_id>",
      "label": "<label or null>",
      "style": {"strokeStyle": "<solid|dashed>"},
      "confidence": <0.0-1.0>
    }
  ],
  "groups": [
    {"id": "<snake_case>", "label": "<label>", "nodeIds": ["..."]}
  ]
}

ID rules:
- Convert labels to snake_case: "Process Data" → "process_data"
- For duplicates in groups: "Artifact" in DEV → "artifact_dev"
- Fallback: append number: "artifact", "artifact_2"

Shape mapping:
- Rectangle → process/action
- Diamond → decision
- Circle/oval → start/end
- Parallelogram → input/output
- Cylinder → database

Mark confidence < 1.0 when text unclear or shape ambiguous.
```

### Architecture Diagram

```
Extract this architecture diagram as JSON:

{
  "nodes": [
    {
      "id": "<name_snake_case>",
      "type": "<rectangle|ellipse|cylinder>",
      "label": "<display name>",
      "x": <x>, "y": <y>, "width": <w>, "height": <h>,
      "style": {"fillColor": "<hex>", "strokeColor": "<hex>"},
      "confidence": <0.0-1.0>
    }
  ],
  "edges": [
    {
      "id": "<from>_to_<to>",
      "from": "<id>", "to": "<id>",
      "label": "<protocol or description>",
      "style": {"strokeStyle": "<solid|dashed>"},
      "confidence": <0.0-1.0>
    }
  ],
  "groups": [
    {"id": "<layer_name>", "label": "<layer>", "nodeIds": ["..."]}
  ]
}

Component hints:
- Cylinder → database
- Cloud shape → external service
- Person icon → user
- Box with lines → server/container
```

### Sequence Diagram

```
Extract this sequence diagram as JSON:

{
  "actors": [
    {"id": "<snake_case>", "label": "<name>", "order": <left-to-right>}
  ],
  "messages": [
    {
      "id": "msg_<n>",
      "from": "<actor_id>", "to": "<actor_id>",
      "label": "<message>",
      "type": "<sync|async|return>",
      "order": <top-to-bottom>,
      "style": {"strokeStyle": "<solid|dashed>"}
    }
  ]
}

Message types:
- sync: solid line, filled arrow
- async: solid line, open arrow
- return: dashed line
```

## Confidence Guidelines

| Score | Meaning |
|-------|---------|
| 0.9-1.0 | Certain - clear text, unambiguous shape |
| 0.7-0.9 | Likely - minor uncertainty |
| 0.5-0.7 | Uncertain - multiple interpretations |
| < 0.5 | Guessing - illegible/unclear |

Add `"note"` field for confidence < 0.7 explaining uncertainty.
