# Findings: Improving Reasoning Traces via Creative Burst + Meter

**Run:** `experiments/results/lit_burst_latest.md` (fresh `20260709T234812Z`)  
**Compiled:** [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md) · [COMPILED_EXPERIMENTATION_20260709.md](../experiments/results/COMPILED_EXPERIMENTATION_20260709.md) · [CHARTS.md](../experiments/results/CHARTS.md)  
**Theory / lit:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md), [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md)  
**Higher cognition + causal/Kineteq:** [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md), [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md), [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md), [INSIGHTS_THEORY_CORPUS_SWEEP.md](INSIGHTS_THEORY_CORPUS_SWEEP.md)

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
| random | 0.702 | 0.705 | 0.687 | 2.119 | 0.743 | 0.633 |
| motif_jump | 0.590 | 0.956 | 0.725 | 1.855 | 0.950 | 0.967 |
| creative_burst_v1 | 0.778 | 0.721 | 0.745 | 2.363 | 0.812 | 0.550 |
| divergent_guilford | 0.786 | 0.654 | 0.705 | **2.474** | 0.738 | 0.500 |
| convergent_constrained | 0.644 | **0.907** | 0.747 | 1.939 | **1.000** | 0.733 |
| novelty_boden | 0.745 | 0.751 | 0.743 | 2.335 | 0.850 | 0.567 |
| layer_cot | 0.667 | 0.895 | 0.755 | 2.022 | 1.000 | 0.700 |
| creative_burst_v2 | 0.706 | 0.820 | 0.751 | 2.165 | 0.929 | 0.617 |
| **multipath_tot** | 0.713 | 0.841 | **0.768** | 2.213 | 0.917 | 0.700 |

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

**Primary queue (evidence-tied):** [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) — RT1–RT11.  
Companion cognition+bridge: [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md) (E1–E10).  
**Iterative training report:** [ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md](ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md) (10 epochs, RT-guided).

### What’s next (top of queue)

1. **RT2 refinement** — Token-budget PromptDict protect→burst + coverage gates (loop mixed).  
2. **RT3** — Non-mock first-stage F for burst-proposed Z.  
3. **RT4 adaptive** — Thrash-triggered schedule vs fixed schedule=2 elite from epoch 6.  
4. **RT5** — Soft mono-gating at hops≥8 (epoch 7 saturated at mono=0.80).  
5. **RT6** — Long-horizon incubation redo only after RT2/RT3 land.

---

## 6. Doc / code index

- Meter: `src/intentisolates/creativity.py`  
- Hopper v2 + multipath: `src/intentisolates/span_burst.py`  
- Lit experiment: `experiments/lit_review_burst_experiments.py`  
- Results: `experiments/results/lit_burst_latest.md`
