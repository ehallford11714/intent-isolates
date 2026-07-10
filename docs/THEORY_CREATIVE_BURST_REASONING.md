# Theory: Creative Burst Hopping & Reasoning Traces

**Status:** formalization + testable claims  
**Package:** `intentisolates` ≥ 0.4.1  
**Companion:** [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md), [CREATIVE_BURST_IMPROVEMENTS.md](CREATIVE_BURST_IMPROVEMENTS.md), [FINDINGS_REASONING_TRACE_IMPROVEMENTS.md](FINDINGS_REASONING_TRACE_IMPROVEMENTS.md)  
**Higher cognition:** [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · **Causal / Kineteq bridge:** [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md) · **Next experiments (reasoning-trace):** [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) · **Next experiments (cognition+bridge):** [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md)

---

## 1. Definitions

| Term | Definition |
| --- | --- |
| **Isolate** | Separable intent unit with typology (goal, constraint, action, …). |
| **Span isolate** | Isolate bound to contiguous text offsets `(start, end, surface)` with `hop_weight`, `burst_affinity`, `protect`. |
| **Hop** | Directed step from span \(s_i\) to unvisited \(s_j\) under policy \(\pi\). |
| **Creative burst** | Lateral walk that trades typology novelty / flexibility against structural anchors. |
| **Reasoning trace** | Ordered content whose layer path and protect spans recover decision structure (goals → constraints → actions/outcomes). |
| **Creativity meter** | Offline scorer mapping a path to dimensions \(C\) (divergent) and \(R\) (reasoning fidelity). |

---

## 2. Formal objects

- \(\mathcal{I}\): set of isolates  
- \(\mathcal{S} \subseteq \mathcal{I}\): span isolates with layer \(\ell(s) \in \{0..4\}\), typology \(\tau(s)\), protect bit \(p(s)\)  
- \(\mathcal{M}\): motifs; neighbor relation \(N_M(s) = \{s' : \exists m\in\mathcal{M},\ s,s'\in m\}\)  
- Trajectory \(T\): layer-ordered scaffold (not identical to a burst path)  
- Hop policy \(\pi(s_j \mid s_i, V)\): distribution / argmax over unvisited candidates given visited set \(V\)  
- Path \(P = (s_0,\ldots,s_n)\)  
- Scores: \(C(P)\), \(R(P)\) from `CreativityMeter`; tradeoff \(H(P) = 2CR/(C+R)\)

### v2 scoring (sketch)

\[
\mathrm{score}(s) = \alpha\,\mathrm{nov}(s) + \beta\,\mathbf{1}[s\in N_M(s_i)] + \gamma\,\mathrm{anchor\_need}(s) + \delta\,\max(0,\Delta\ell) + \mathrm{aff}(s) + \mathrm{dist}(s)
\]

with periodic forced protect visits every `anchor_schedule` hops.

---

## 3. Propositions (testable)

| ID | Claim | Prediction | Status |
| --- | --- | --- | --- |
| **P1** | Constrained divergent hops improve \(R\) without collapsing \(C\) vs random | \(H(\pi_{v2}) > H(\pi_{rand})\); \(C\) within ~0.05 of random | **Supported** (sweep+lit; strong/moderate) |
| **P2** | Anchor-scheduled burst dominates random on \(R\) / `anchor_R` | `anchor_R(v2) > anchor_R(random)` | **Supported** (strong; Δ≈0.16) |
| **P3** | Layer-monotonic bias improves trajectory quality | `layer_mono(layer_cot) ≥ layer_mono(divergent)` | **Supported** (strong; 8/8 fixtures) |
| **P4** | Divergent (high novelty) raises entropy / \(C\) vs convergent | \(C(\mathrm{div}) > C(\mathrm{conv})\); entropy likewise | **Supported** (strong) |
| **P5** | Multi-path select-by-\(H\) (ToT-style) weakly dominates single-seed v2 on \(H\) | \(H(\mathrm{multipath}) \ge H(v2)\) | **Supported** (moderate; k5/k7; lit H=0.768) |
| **P6–P12** | WM / conflict / insight / causal | See higher-cognition + [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) | P6 **rejected** (WM sim); P7 supported; P8 mixed; causal weak |
| **P13** | Multipath **value-function family**: select-by-\(H\) is H-optimal; select-by-\(R\) is R-optimal; select-by-\(C\) harms \(R\); IV-diag may dominate \(R\) for causal-prep | Replicate G1; Pareto map H/R/IV fronts | **Supported** (P0 E1 2026-07-10: H/R/C Pareto; G1 strong). iv_diag **mixed** (fail k=5 / pass k=7) |
| **P14** | Soft mono-gating raises `layer_mono` toward motif levels without motif’s \(C\) collapse | mono ≥ layer_cot+δ; \(C\) ≫ motif | **Open** → RT5 |
| **P15** | Protect-compact → burst preserves mid-constraints iff protect filter used (true PromptDict hot-set, not truncate sim) | mid_R≈1 pre-burst; post-burst `anchor_R` ≫ drop-protect | **Supported** mid_R=1.0 + protect→mpH R=0.897 (P0 E2); trunc H inflated (pool artifact) |
| **P16** | Motif–burst hybrid schedule recovers mono/R between motif specialist and v2 | Some schedule with \(H\ge v2\), mono↑, \(C\) within 0.05 of v2 | **Open** → RT8 |
| **P17** | Longer-horizon structured diverge↔converge beats hop=5 incubations | H ≥ v2 at hops≥8 | **Rejected** (P0 E3: H 0.686/0.695 ≪ v2; 0/8) — **archive** |

Falsifiers: if truncate-like random matches v2 on \(R\) at equal path length; if multipath never beats single path across seeds; if layer bias lowers mono. Cognition-grounded P6–P12 and causal bridge B1–B5: [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) §11, [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md) §7.

---

## 4. Empirical status (2026-07-09 compile)

Offline only (CreativityMeter + PromptDict compaction). Stance: **computational analogs**, not human cognition identity.

| Claim cluster | Evidence | Integrate into defaults? |
| --- | --- | --- |
| P1 / P2 / L2 (v2 vs random / v1) | v2 R lit 0.820>0.721; sweep 0.796>0.754; anchor_R Δ≈+0.16 vs random | **Yes** — keep `for_v2` |
| P5 / G2–G3 (multipath H) | lit H=0.768; sweep k7 H=0.774 > k5 0.769 > k3 0.768 > v2 0.754 | **Yes** — select-by-`tradeoff_harmonic` when k≥3 |
| G1 (do not select-by-C) | mp_H R 0.836 vs mp_C 0.734 (8/8) | **Yes** — never default select-by-C for fidelity |
| Motif L1 (fidelity specialist) | motif R/mono elite; C≪v2 (−0.16) | **Specialist only**, not ideation default |
| P4 / PP1–PP2 dual-process & precision | div↑C; conv / precision_high ↑R | **Yes** — knob families |
| P7 conflict schedule=2 | H 0.763 ≥ v2; C drops ~0.04 | **Optional** compliance; refine via RT4 |
| P6 / I1 / I2 / **P17** | Rejected (WM truncate artifact; incubation/two-phase; **structured alt-2 at hops 5–8**) | **No** incubation defaults |
| P13 value-fn | P0 E1: H-select H-max; R-select R-max; G1 strong; iv_diag only at k≥7 | **Yes** — keep H; optional iv_diag@k7 |
| P15 protect→burst | P0 E2: mid_R=1.0; protect→mpH R=0.897; trunc H artifact | **Yes** — protect before burst; ignore trunc H |
| Protect-compact mid_R | mid_R=1.0 vs truncate 0.2 | **Yes** for compaction + burst coupling |
| Causal B1/B2 | Weak mock tie / zero overlap | **Do not** claim IV quality from meter alone |

Full rows: [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) · [P0_FOLLOWUP_EXPERIMENT_RESULTS.md](P0_FOLLOWUP_EXPERIMENT_RESULTS.md) · report: [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md).

---

## 5. Open questions → next experiments

| Open question | Led by result | Experiment |
| --- | --- | --- |
| ~~Better multipath objective than \(H\)?~~ | P0 E1 closed Pareto; iv_diag only @k7 | **RT1 DONE** |
| ~~protect_compact→burst vs truncate?~~ | P0 E2 mid_R+R; trunc H artifact | **RT2 DONE** |
| Can burst-proposed \(Z\) beat random on real first-stage F? | B1 mock F tied | **RT3** |
| Adaptive conflict control recover C lost by schedule=2? | P7 H↑ but C↓ | **RT4** |
| Soft mono gates without motif C death? | motif mono 0.98 / C 0.57 vs layer_cot | **RT5** |
| Incubation succeed at longer horizons? | I1/I2 rejected at hop=5 | **RT6** |
| Motif priors transfer across fixtures? | P9 untested | **RT7** |
| Motif schedule hybrid Pareto? | L1 tradeoff | **RT8** |

Queue: [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md).

---

## 6. Compaction & causation (brief)

- **Compaction:** protect \(p(s)=1\) spans during PromptDict compact; burst on the hot set (`filter_spans_for_burst`). Empirically, `protect_compact` keeps mid_constraint_R=1.0 vs lossy_truncate 0.2; **P0 E2** closed coupling — protect→mpH R=0.897 with mid_R=1.0 (trunc H is a pool artifact). See [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md) · [P0_FOLLOWUP_EXPERIMENT_RESULTS.md](P0_FOLLOWUP_EXPERIMENT_RESULTS.md).
- **IV / layers:** abstract layers are scaffolds for trajectories, not residual-stream indices; layer-IV suite separates **indication** vs **causation** — do not claim hop policies *cause* better LLM answers without an outcome experiment (RT11). Full crosswalk: [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md), [LAYER_CAUSAL_IV.md](LAYER_CAUSAL_IV.md).

---

## 7. Experimental predictions (lit-mapped)

See `experiments/lit_review_burst_experiments.py`: divergent → high \(C\); convergent → high \(R\); v2 / multipath → high \(H\); motif → max \(R\)/mono / min \(C\).
