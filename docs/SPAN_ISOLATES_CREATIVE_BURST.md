# Span Isolates & Creative-Burst Hopping

**Package:** `intentisolates` ≥ 0.4  
**Module:** `intentisolates.span_burst`  
**Soft export:** `llmintent.isolates` (prefers installed IntentIsolates; else vendored `_core`)

---

## Concept

A **span isolate** is an isolate typed/bound to a contiguous **text span** (`start`, `end`, `surface`). Unlike a free-floating phrase label, it is a **hoppable stepping-stone**: you can jump span→span along a trajectory to spark **creative burst** exploration while keeping structural anchors (goal / constraint / outcome) visitable.

| Field | Role |
| --- | --- |
| `text_span` | Contiguous offsets + surface string |
| `typology` | goal / constraint / affective / … |
| `hop_weight` | How strongly the span should stay reachable (anchors high) |
| `burst_affinity` | How useful as a creative stepping-stone (affective/novel high) |
| `protect` | True for goal/constraint/outcome anchors |

---

## API

```python
from intentisolates import (
    identify_span_isolates,
    CreativeBurstHopper,
    typology_path_entropy,
)

spans = identify_span_isolates(text)
hopper = CreativeBurstHopper(spans, seed=17)
hop = hopper.hop(spans[0].id, mode="creative_burst")
path = hopper.burst_path(seed=None, n_hops=5, mode="creative_burst")
print(path.typology_path, typology_path_entropy(path.typology_path))
```

### Modes

| Mode | Behavior |
| --- | --- |
| `linear` | Next unused span in document order |
| `motif_jump` | Prefer co-members of shared motifs |
| `creative_burst` | Novelty + layer jump + burst affinity + soft **anchor pull** |
| `random` | Uniform among unvisited (experiment baseline) |

### CLI

```bash
python -m intentisolates span-burst --text "..." --hops 5 --mode creative_burst --markdown
```

---

## Tie-in: motifs, trajectories, compaction

- **Motifs** supply neighbor edges for `motif_jump` and a soft bonus inside `creative_burst`.
- **Trajectories** order isolates by layer (L0→L4). Burst paths are a *lateral* walk across spans; they complement (not replace) layer trajectories.
- **Compaction** (PromptDict): when shrinking a working set, **protect span isolates** with `protect=True` (goal/constraint/outcome) the same way isolate-then-compact protects mid-trace constraints. See [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md).

**Recommended pipeline:** identify span isolates → compact while protecting `protect` spans → hop `creative_burst` on the remaining / restored hot set for divergent ideation without losing anchors.

---

## Experiment

```bash
python experiments/span_burst_creative.py
```

Hypothesis: `creative_burst` increases typology-path entropy vs `linear` while preserving higher goal/constraint visit rates than pure `random`.
