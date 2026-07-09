# Findings: Improving Reasoning Traces via Creative Burst + Meter

**Run:** see `experiments/results/lit_burst_latest.md`  
**Theory / lit:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md), [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md)

---

## 1. What lit predicted

| Lit idea | Prediction |
| --- | --- |
| Guilford divergent | Higher entropy / C; lower anchors if unconstrained |
| Constrained / convergent creativity | Higher `anchor_R` / R; lower entropy |
| Mednick / motifs | High R, low C (clustered associates) |
| CoT layer scaffolding | Higher layer monotonicity |
| ToT multi-path + evaluate | Best harmonic tradeoff H = 2CR/(C+R) |
| v2 hybrid (P0) | Better R than v1 without collapsing C vs random |

---

## 2. What experiments showed (offline, 4 fixtures × 3 seeds, 5 hops)

Latest summary (CreativityMeter composites):

| condition | C | R | H | entropy | anchor_R | layer_mono |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| linear | 0.688 | 0.645 | 0.657 | 2.147 | 0.625 | 0.683 |
| random | 0.744 | 0.701 | 0.713 | 2.279 | 0.764 | 0.583 |
| motif_jump | 0.590 | 0.956 | 0.725 | 1.855 | 0.950 | 0.967 |
| creative_burst_v1 | 0.778 | 0.721 | 0.745 | 2.363 | 0.812 | 0.550 |
| divergent_guilford | 0.787 | 0.666 | 0.711 | **2.474** | 0.738 | 0.533 |
| convergent_constrained | 0.655 | **0.896** | 0.750 | 1.977 | **0.983** | 0.733 |
| novelty_boden | 0.756 | 0.732 | 0.739 | 2.363 | 0.829 | 0.550 |
| layer_cot | 0.716 | 0.812 | 0.752 | 2.203 | 0.917 | 0.617 |
| creative_burst_v2 | 0.726 | 0.795 | 0.754 | 2.241 | 0.900 | 0.600 |
| **multipath_tot** | 0.720 | 0.823 | **0.766** | 2.213 | 0.917 | 0.650 |

**Confirmed:** divergent entropy > convergent; convergent anchors > divergent; v2 R > v1 R; multipath H ≥ v2 H; v2 H ≥ random.

**Nuance:** `motif_jump` still wins raw R / layer_mono but loses C (lowest creativity). Pure divergent wins C/entropy but loses H to hybrids. `layer_cot` is competitive on H with strong anchors.

---

## 3. Which proposals won (implemented P0)

1. **Anchor-scheduled burst** — raised `anchor_R` (v2 ~0.90 vs v1 0.81 vs random ~0.76).  
2. **Layer-aware bias** — `layer_cot` / v2 improve mono vs pure divergent; motif_jump still best mono.  
3. **Novelty + motif hybrid** — v2 keeps C near random while lifting R.  
4. **Multi-path select-by-meter (ToT)** — **best H** (0.766); recommended when compute allows k≈5 seeds.

---

## 4. Recommended defaults (production)

### CreativeBurstHopper

```python
CreativeBurstHopper.for_v2(spans)  # or mode="creative_burst_v2"
# knobs: anchor_pull=0.70, layer_bias=0.55, novelty_weight=1.10,
#        motif_weight=0.45, anchor_schedule=3, side_hop_prob=0.18
```

For max reasoning fidelity under a budget: `multi_path_burst(..., k=5, select_by="tradeoff_harmonic")`.  
For ideation-only: `divergent_guilford` knobs.  
For compliance-heavy traces: `convergent_constrained` knobs.

### CreativityMeter

Default weights (C: diversity/novelty/flex/elab/fluency; R: 0.65 constraint + 0.35 layer_mono).  
Select paths by **`tradeoff_harmonic`** (H), not C alone.

### Compaction bridge

`filter_spans_for_burst` after protect_compact; meter `constraint_fidelity` as gate before accepting a burst path.

---

## 5. Next P1 experiments

1. Two-phase diverge→converge within one path (first half novelty, second half anchors).  
2. Protect-hot-set burst after PromptDict `protect_compact` (end-to-end with compaction metrics).  
3. Outcome-linked eval: does higher H improve downstream task checklists / LLM judge scores?  
4. GoT merge hops into shared goal spans (P2).

---

## 6. Doc / code index

- Meter: `src/intentisolates/creativity.py`  
- Hopper v2 + multipath: `src/intentisolates/span_burst.py`  
- Lit experiment: `experiments/lit_review_burst_experiments.py`  
- Results: `experiments/results/lit_burst_latest.md`
