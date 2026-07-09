# Creative-Burst Hopping — Improvements for Reasoning Traces

**Status:** research + implemented (`creative_burst_v2`)  
**Package:** `intentisolates` ≥ 0.4.1  
**Related:** [SPAN_ISOLATES_CREATIVE_BURST.md](SPAN_ISOLATES_CREATIVE_BURST.md), [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md)

---

## 1. Why creative_burst helps reasoning traces

A reasoning trace is not only a linear document walk. Useful traces need:

| Property | Role | How burst helps |
| --- | --- | --- |
| **Diversity** | Surface alternate typologies / metaphors / instruments | Novelty + burst affinity + moderate layer jumps raise typology-path entropy |
| **Anchors** | Keep goals / constraints / outcomes visitable | Soft `anchor_pull` + periodic forced visits raise `anchor_R` vs pure random |
| **Structure** | Motifs and layer scaffolds remain recoverable | Motif co-member bonus keeps structural edges in the hop graph |

Offline baseline (≈ `span_burst_latest`):

| mode | entropy | anchor_R |
| --- | ---: | ---: |
| linear | 2.15 | 0.63 |
| motif_jump | 1.86 | **0.95** |
| creative_burst | **2.36** | 0.81 |
| random | 2.18 | 0.72 |

**Takeaway:** v1 already wins diversity; the open gap is **anchor fidelity** (vs motif_jump) and **layer-order fidelity** (vs an ideal L1→L3→L4 trajectory).

---

## 2. Gaps vs motif_jump and vs ideal trajectories

### vs `motif_jump`

- Motif jumps stay on co-members → high `anchor_R`, low entropy (clustered typologies).
- Creative burst explores laterally → high entropy, but under-visits protect spans unless forced.

### vs ideal reasoning trajectory (`L_early → L_late`)

`trajectory_from_motifs` orders content by abstract layer (surface → binding → latent → goal/constraint → action/outcome). Burst paths are *lateral* walks; v1 scores **absolute** layer distance (encourages jumps) rather than **forward** progress. That hurts `layer_path_monotonicity` — a proxy for “does the hop path still look like a reasoning scaffold?”

### Compaction bridge

Protect `SpanIsolate.protect` spans during PromptDict compact (isolate-then-compact), then burst on the hot set. Burst must not undo that protection by never revisiting anchors.

---

## 3. SOTA-inspired ideas (brief)

| Idea | Citation / lineage | Transfer to hopping |
| --- | --- | --- |
| **Divergent–convergent creativity** | Guilford; Design Thinking diverge→converge | Alternate exploration hops with scheduled anchor convergence |
| **Tree / Graph of Thoughts** | Yao et al. ToT; Besta et al. GoT | Multi-path exploration with merge back to goal/constraint nodes |
| **Curiosity / novelty bonuses** | Pathak ICM; count-based exploration | Typology novelty term already present; strengthen + decay revisited types |
| **Constrained generation** | Lexically / structurally constrained decoding | Hard/soft protect-span visits = structural constraints on the walk |
| **CoT scaffolding** | Wei et al. CoT; process supervision | Prefer forward layer steps so paths resemble early→late reasoning |
| **Motif-guided search** | Graph motifs / template paths | Keep motif_link as a soft edge prior (hybrid with novelty) |

---

## 4. Ranked improvement proposals

### P0 — ship now (implemented in `creative_burst_v2`)

1. **Anchor-scheduled burst** — every `anchor_schedule` hops (default 3), force visit to highest-weight unvisited protect span. Closes gap to motif_jump `anchor_R` without every-other-hop over-forcing (v1 used `% 2`, which can over-anchor and still miss goals).
2. **Layer-aware hop bias** — score `δ · max(0, Δlayer)` for forward progress; small penalty for large backward jumps; occasional `side_hop_prob` creative side-hops that ignore layer bias.
3. **Novelty + motif hybrid** —  
   `score = α·novelty + β·motif_link + γ·anchor_need + δ·layer_progress + affinity + dist`  
   with knobs `novelty_weight`, `motif_weight`, `anchor_pull`, `layer_bias`.

### P1 — next (partially started)

4. **Protect-span hot-set burst** — after `protect_compact`, restrict candidates via `filter_spans_for_burst` (helper shipped).
5. **Two-phase diverge→converge** — first ⌊n/2⌋ hops maximize novelty; last hops maximize anchor + layer progress.
6. **Multi-seed beam / ToT select** — **implemented** as `multi_path_burst` (pick by CreativityMeter H). Won best H in lit experiments.

### P2 — research

7. GoT-style merge nodes (explicit join hops into shared goal spans).
8. Learned hop policy (bandit / small classifier over span features).
9. Online LLM rescoring of candidate next spans (expensive; not offline-default).

---

## 5. Knobs & defaults (`creative_burst_v2`)

| Knob | Default | Role |
| --- | ---: | --- |
| `anchor_pull` | 0.70 | γ scale for protect-span need |
| `layer_bias` | 0.55 | δ scale for forward layer progress |
| `novelty_weight` | 1.10 | α scale for unused typology |
| `motif_weight` | 0.45 | β scale for motif co-member |
| `anchor_schedule` | 3 | Force protect visit every N hops (0 = off) |
| `side_hop_prob` | 0.18 | Prob. of creative side-hop (ignore layer bias) |

Mode `creative_burst` keeps **v1** scoring for A/B; `creative_burst_v2` uses the hybrid above.

**CreativityMeter:** see `intentisolates.creativity`; select paths by `tradeoff_harmonic`.

---

## 6. Experiment pointer

```bash
python experiments/lit_review_burst_experiments.py
python experiments/span_burst_creative.py
```

Results: `experiments/results/lit_burst_latest.md` · findings: [FINDINGS_REASONING_TRACE_IMPROVEMENTS.md](FINDINGS_REASONING_TRACE_IMPROVEMENTS.md).

Metrics: CreativityMeter C/R/H, entropy, `anchor_R`, `layer_path_monotonicity`, unique typologies.
