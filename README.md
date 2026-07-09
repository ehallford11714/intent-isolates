# IntentIsolates

**Identify isolates**, classify their **typology**, form **layer motifs**, and map **reasoning trajectories**.

Package: `intentisolates` · Version: **0.3.0**

> Epistemic caveat: motifs and trajectories are **structural hypotheses**, not proven cognitive mechanisms. Abstract layers L0–L4 are a reasoning scaffold unless bound to a real model residual stream. **Indication ≠ causation** — see [LAYER_CAUSAL_IV.md](docs/LAYER_CAUSAL_IV.md).

## Install

```bash
pip install intentisolates
# or from source
pip install -e ".[dev]"
```

Optional soft backends:

```bash
pip install intentisolates[hf]
pip install intentisolates[llmintent]
```

## Quick API

```python
from intentisolates import (
    identify_isolates,
    classify_typology,
    form_motifs,
    trajectory_from_motifs,
    build_report,
)

text = (
    "I want to finish the report. I cannot miss the deadline. "
    "I feel anxious. I will submit it using the portal so that it is on time."
)

isos = identify_isolates(text=text)
motifs = form_motifs(isos)
traj = trajectory_from_motifs(motifs, isos)

print(traj.ascii_diagram)
print(traj.summary_markdown)
```

### Layer causal / IV

```python
from intentisolates.causal import LayerCausalSuite

suite = LayerCausalSuite.from_text(text)
result = suite.run(outcome_hint="on time")
print(result.to_markdown())  # indication matrix + IV causation edges
```

Also works on **features** (KPI / activation vectors) and small **graphs** (orphan / leaf nodes):

```python
identify_isolates(features={"a": 0.1, "spike": 4.2})
identify_isolates(graph={"nodes": ["A", "B", "x"], "edges": [["A", "B"]]})
```

## CLI

```bash
python -m intentisolates identify --text "I want X but cannot Y"
python -m intentisolates typology --text "I feel stuck; I need a plan"
python -m intentisolates motifs --text "..."
python -m intentisolates trajectory --text "..." -o out.json
python -m intentisolates report --text "..." --motifs --trajectory -o out.json
python -m intentisolates causal --text "..." --outcome-hint decision
python -m intentisolates backends
```

## Concepts

| Concept | Meaning |
|---------|---------|
| **Isolate** | Separable unit of intent/meaning/activation |
| **Typology** | `lexical`, `affective`, `instrumental`, `goal`, `constraint`, `action`, `outcome`, `confounder`, `noise`, `latent_feature`, `orphan_node` |
| **Layer** | Abstract L0–L4 (or model residual index when hooked) |
| **Motif** | Recurring composition of isolates (co-occurrence, sequence, typed path, chain, triangle, layer bridge) |
| **Trajectory** | Ordered path of motifs/isolates across layers |
| **Indication** | Layer/motif association with outcome Y (not causal) |
| **Causation (IV)** | Lower-layer Z instruments mid/late X → Y via 2SLS / Wald |

## Docs

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [TYPOLOGY.md](docs/TYPOLOGY.md)
- [MOTIFS_TRAJECTORIES.md](docs/MOTIFS_TRAJECTORIES.md)
- [LAYER_CAUSAL_IV.md](docs/LAYER_CAUSAL_IV.md)
- [SOTA_ISOLATES.md](docs/SOTA_ISOLATES.md)

## Soft integrations

- `llmintent.isolates` — optional re-export when both packages are installed
- LatentIntentInspect / HF — soft imports only; rule backend never requires torch
- AutoCausalLib — `python -m autocausal isolates-causal` soft-imports this package
- CausalIVSuite — preferred IV backend when `causaliv` is installed

## License

MIT
