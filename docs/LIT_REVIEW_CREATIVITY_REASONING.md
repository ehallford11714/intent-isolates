# Lit Review: Creativity, Reasoning Traces, and Hop Policies

**Status:** working review for IntentIsolates creative-burst + CreativityMeter  
**Theory:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md)  
**Experiments:** `experiments/lit_review_burst_experiments.py`

---

## 1. Divergent thinking (Guilford)

J. P. Guilford contrasted **divergent** production (many answers) with **convergent** (one answer), scoring fluency, flexibility, originality, and elaboration ([overview](https://www.cogn-iq.org/learn/theory/divergent-thinking/); [Alternate Uses](https://en.wikipedia.org/wiki/Guilford's_Alternate_Uses)).

| Dimension | Meter / hop mapping |
| --- | --- |
| Fluency | `fluency` (unique spans / pool); longer paths |
| Flexibility | `flexibility` (cross-layer / non-motif jumps); `side_hop_prob` |
| Originality | `novelty` (+ `novelty_weight`) |
| Elaboration | `elaboration` (surface length proxy) |

**Experiment condition:** `divergent_guilford` — high novelty, low anchor schedule.

---

## 2. Associative creativity (Mednick)

Mednick’s associative hierarchy / Remote Associates Test: creative thought as combining remote associates ([review](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.573432/full); [PMC revisit](https://pmc.ncbi.nlm.nih.gov/articles/PMC3924568/)).

**Mapping:** `motif_jump` and `motif_weight` — prefer co-members of shared motifs (structural “associates”).

---

## 3. Boden: exploratory vs transformational

Margaret Boden: combinational, **exploratory** (search within a conceptual space), **transformational** (change the rules) ([AI Mag. survey](https://doi.org/10.1609/aimag.v30i3.2254)).

**Mapping:** exploratory ≈ high `novelty_weight` within fixed typology/layer space (`novelty_boden`); transformational ≈ future P2 (alter protect set / layer grammar) — not default offline.

---

## 4. CoT / ToT / GoT

- **Chain-of-Thought** (Wei et al.): linear intermediate steps — maps to `layer_bias` forward scaffolding (`layer_cot`).
- **Tree of Thoughts** ([Yao et al., 2023](https://arxiv.org/abs/2305.10601)): explore multiple thought paths, evaluate, backtrack — maps to `multi_path_burst` + CreativityMeter select-by-\(H\).
- **Graph of Thoughts** ([Besta et al.](https://htor.inf.ethz.ch/publications/img/besta-topologies.pdf)): arbitrary merges — P2 merge-to-goal hops.

---

## 5. Constrained creativity & CST

Creativity support tools and constrained generation keep value/constraints while exploring. **Mapping:** `anchor_pull`, `anchor_schedule`, `protect` spans; condition `convergent_constrained`.

---

## 6. Prompt compression / context engineering

Lossless dict compression preserves motifs; lossy truncate drops mid-constraints ([ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md)). **Mapping:** isolate-then-compact → `filter_spans_for_burst` on hot set; meter `constraint_fidelity` must stay high after compact.

---

## 7. Latent reasoning / scratchpads (brief)

Scratchpads and latent-thought inspection motivate treating intermediate text as a structured artifact. Burst hops operate on **explicit** span isolates (offline); soft bridge to `llmintent.latent` is optional and not required for meter scores.

---

## 8. Lit → knob / meter cheat sheet

| Lit thread | Knob / API | Meter dim |
| --- | --- | --- |
| Guilford fluency/flex/orig/elab | `novelty_weight`, `side_hop_prob`, path length | fluency, flexibility, novelty, elaboration |
| Mednick associates | `motif_jump`, `motif_weight` | (structure in flexibility inverse) |
| Boden exploratory | high novelty within space | novelty, C |
| Constrained creativity | `anchor_pull`, `anchor_schedule` | constraint_fidelity, R |
| CoT scaffolding | `layer_bias` | layer_monotonicity |
| ToT/GoT | `multi_path_burst` | select by H / C·R |
| Compaction | `protect`, `filter_spans_for_burst` | constraint_fidelity |

---

## 9. References (selected)

1. Guilford divergent thinking — [Cogn-IQ](https://www.cogn-iq.org/learn/theory/divergent-thinking/)  
2. Mednick RAT review — [Frontiers 2020](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.573432/full)  
3. Boden computer models of creativity — [AI Magazine](https://doi.org/10.1609/aimag.v30i3.2254)  
4. Yao et al. Tree of Thoughts — [arXiv:2305.10601](https://arxiv.org/abs/2305.10601)  
5. Besta et al. topologies of thought — [ETH PDF](https://htor.inf.ethz.ch/publications/img/besta-topologies.pdf)  
6. Workspace: PromptDict + isolates compaction — `research/docs/ISOLATES_COMPACTION_REASONING.md`
