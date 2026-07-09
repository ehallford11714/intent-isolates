# Theory: Creative Burst Hopping & Reasoning Traces

**Status:** formalization + testable claims  
**Package:** `intentisolates` ≥ 0.4.1  
**Companion:** [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md), [CREATIVE_BURST_IMPROVEMENTS.md](CREATIVE_BURST_IMPROVEMENTS.md), [FINDINGS_REASONING_TRACE_IMPROVEMENTS.md](FINDINGS_REASONING_TRACE_IMPROVEMENTS.md)  
**Higher cognition:** [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · **Causal / Kineteq bridge:** [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md) · **Next experiments:** [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md)

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
| **P5** | Multi-path select-by-\(H\) (ToT-style) weakly dominates single-seed v2 on \(H\) | \(H(\mathrm{multipath}) \ge H(v2)\) | **Supported** (moderate; k5/k7) |
| **P6–P12** | WM / conflict / insight / causal | See higher-cognition + [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) | P6 **rejected** (WM sim); P7 supported; P8 mixed; causal weak |

Falsifiers: if truncate-like random matches v2 on \(R\) at equal path length; if multipath never beats single path across seeds; if layer bias lowers mono. Cognition-grounded P6–P12 and causal bridge B1–B5: [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) §11, [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md) §7.

---

## 4. Compaction & causation (brief)

- **Compaction:** protect \(p(s)=1\) spans during PromptDict compact; burst on the hot set (`filter_spans_for_burst`). Burst must not erase anchors that compaction preserved. See [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md).
- **IV / layers:** abstract layers are scaffolds for trajectories, not residual-stream indices; layer-IV suite separates **indication** vs **causation** — do not claim hop policies *cause* better LLM answers without an outcome experiment. Full crosswalk (meter \(R\) ↔ weak-IV epistemic control; burst ↔ instrument explore; Bridge/Kineteq broadcast): [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md), [LAYER_CAUSAL_IV.md](LAYER_CAUSAL_IV.md).

---

## 5. Experimental predictions (lit-mapped)

See `experiments/lit_review_burst_experiments.py`: divergent → high \(C\); convergent → high \(R\); v2 / multipath → high \(H\).
