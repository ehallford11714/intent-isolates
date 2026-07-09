# Motifs and reasoning trajectories

## Motifs

A **motif** is a recurring pattern or composition of isolates within or across layers.

| Motif typology | Detection |
|----------------|-----------|
| `co_occurrence` | Pair sharing a layer |
| `sequence` | Adjacent in span / order |
| `typed_path` | Template match on typology sequence |
| `chain` | Length-3 path in soft adjacency graph |
| `triangle` | 3-clique in soft graph |
| `layer_bridge` | Members spanning ≥2 layer distance |

Each motif carries:

- `member_ids`, `layers`, `pattern`
- `support` / `confidence` (heuristic)
- `trajectory_role`: `early_lexical` | `mid_latent` | `late_goal` | `bridge` | …

### Typed templates

```
goal → constraint → action
affective → instrumental → outcome
lexical → latent_feature → goal
constraint → instrumental → outcome
goal → instrumental → outcome
affective → constraint → action
```

## Reasoning trajectories

`trajectory_from_motifs(motifs, isolates)` orders content by layer:

```
L0 surface lexical  →  L1 binding  →  L2 latent  →  L3 goal/constraint  →  L4 action/outcome
```

Outputs:

- `steps[]` with isolate/motif ids and role
- `layer_path`, `motif_path`
- `summary_markdown` explaining layer roles
- `ascii_diagram` and `mermaid` flowchart

### Why trajectories help understand layers

Early steps concentrate lexical/affective isolates (what was said / felt). Mid layers host latent or confounder-like structure (what is bound or entangled). Late layers concentrate goals, constraints, and actions (what is decided / done). Motifs that **bridge** layers show how local isolates compose into a longer path — a lens on **layer roles**, not a claim that the model “thinks” in these steps.

## Caveats

- Motifs are **structural hypotheses**.
- Abstract L0–L4 ≠ transformer residual indices unless explicitly bound.
- Template matches are not causal identification.
