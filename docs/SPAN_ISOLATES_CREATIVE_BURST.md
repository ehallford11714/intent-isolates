# Span Isolates & Creative-Burst Hopping

**Package:** `intentisolates` ≥ 0.4.1  
**Module:** `intentisolates.span_burst`, `intentisolates.creativity`  
**Soft export:** `llmintent.isolates` (prefers installed IntentIsolates; else vendored `_core`)

**Also see:** [CREATIVE_BURST_IMPROVEMENTS.md](CREATIVE_BURST_IMPROVEMENTS.md) · [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md) · [FINDINGS_REASONING_TRACE_IMPROVEMENTS.md](FINDINGS_REASONING_TRACE_IMPROVEMENTS.md)

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
    CreativityMeter,
    multi_path_burst,
    typology_path_entropy,
)

spans = identify_span_isolates(text)
hopper = CreativeBurstHopper.for_v2(spans, seed=17)
path = hopper.burst_path(n_hops=5, mode="creative_burst_v2")
report = CreativityMeter().score_burst(path, spans)
print(report.creativity_score, report.reasoning_trace_score, report.tradeoff_harmonic)

best, cands = multi_path_burst(spans, n_hops=5, k=5, select_by="tradeoff_harmonic")
```

### Modes

| Mode | Behavior |
| --- | --- |
| `linear` | Next unused span in document order |
| `motif_jump` | Prefer co-members of shared motifs |
| `creative_burst` | v1: novelty + layer jump + affinity + soft anchor pull |
| `creative_burst_v2` | Hybrid: α·novelty + β·motif + γ·anchor_need + δ·layer_progress + scheduled anchors |
| `random` | Uniform among unvisited (experiment baseline) |

### CreativityMeter dimensions

Diversity, novelty, flexibility, elaboration, fluency → composite **C**; constraint fidelity + layer monotonicity → composite **R**; tradeoff **H** = harmonic mean.

### CLI

```bash
python -m intentisolates span-burst --text "..." --hops 5 --mode creative_burst_v2 --markdown
python -m intentisolates creativity --text "..." --hops 5 --mode creative_burst_v2 --markdown
```

---

## Tie-in: motifs, trajectories, compaction

- **Motifs** supply neighbor edges for `motif_jump` and a soft bonus inside creative burst.
- **Trajectories** order isolates by layer (L0→L4). Burst paths are a *lateral* walk; `layer_bias` nudges them toward forward progress.
- **Compaction** (PromptDict): protect `protect=True` spans, then `filter_spans_for_burst` on the hot set. See [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md).

**Recommended pipeline:** identify span isolates → compact while protecting anchors → `creative_burst_v2` or `multi_path_burst` on the hot set → gate on CreativityMeter `R` / `H`.

---

## Experiments

```bash
python experiments/span_burst_creative.py
python experiments/lit_review_burst_experiments.py
```

Hypothesis (supported offline): `creative_burst_v2` and ToT multi-path improve reasoning-trace score / harmonic tradeoff vs random while keeping competitive creativity vs pure divergent.
