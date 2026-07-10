# Theory: Higher-Cognition Grounding for Reasoning Traces

**Status:** computational analogs (not claims that span hops *are* human cognition)  
**Package:** `intentisolates` ≥ 0.4.1  
**Companions:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md) · [LIT_REVIEW_CREATIVITY_REASONING.md](LIT_REVIEW_CREATIVITY_REASONING.md) · [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) · [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md) · [FINDINGS_REASONING_TRACE_IMPROVEMENTS.md](FINDINGS_REASONING_TRACE_IMPROVEMENTS.md)

**Epistemic stance:** Formal objects \((\mathcal{I},\mathcal{S},\mathcal{M},T,\pi,C,R,H)\) are **engineering constructs** with *selective* structural resemblance to constructs in theories of higher cognition. Mappings are for hypothesis generation and experiment design, not identity claims.

---

## 0. Formal objects (recap)

| Symbol | IntentIsolates meaning |
| --- | --- |
| \(\mathcal{I}\) | Isolates (intent units) |
| \(\mathcal{S}\) | Span isolates with layer \(\ell\), typology \(\tau\), protect \(p\) |
| \(\mathcal{M}\) | Motifs; \(N_M(s)\) = motif co-members |
| \(T\) | Layer-ordered trajectory scaffold |
| \(\pi\) | Hop policy over unvisited spans |
| \(P\) | Path \((s_0,\ldots,s_n)\) |
| \(C(P), R(P)\) | CreativityMeter divergent vs reasoning-fidelity composites |
| \(H(P)\) | Harmonic tradeoff \(2CR/(C+R)\) |

Offline evidence (2026-07-09 lit + theory_corpus_sweep): `multipath_tot` / `multipath_k*_H` best \(H\) (lit **0.768**, sweep k7 **0.774**); `creative_burst_v2` lifts \(R\) vs v1 without collapsing \(C\) vs random; divergent raises entropy; convergent / precision_high raise `anchor_R`; motif_jump max R/mono min C; incubation/two-phase **rejected** at hop=5; PromptDict `protect_compact` mid_R=1.0 vs truncate 0.2. See `experiments/results/lit_burst_latest.md`, `theory_corpus_sweep_latest.md`, CLAIM_EVIDENCE_TABLE.

---

## 1. Dual-process / System 1–2

**Sources:** Kahneman (2003/2011) System 1–2; Evans (2008) dual-process review ([doi:10.1146/annurev.psych.59.103006.093629](https://doi.org/10.1146/annurev.psych.59.103006.093629)); Kahneman (2003) overview ([PDF](https://pages.ucsd.edu/~mckenzie/Kahneman2003AmPsych.pdf)).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| System 1 / Type-1 (fast, associative) | High-novelty / `side_hop_prob` / `divergent_guilford` | **tight** (behavioral dual, not neural) |
| System 2 / Type-2 (slow, rule-governed) | `anchor_schedule`, `convergent_constrained`, protect visits | **tight** |
| Default → override | Burst then forced anchor | **moderate** |

**(b) Predictions for \(C\) vs \(R\):** Divergent (S1-like) ↑\(C\), ↓`anchor_R`; convergent (S2-like) ↑\(R\); hybrid v2 / multipath maximize \(H\).  
**(c) Analog closeness:** **tight** for the diverge/converge schedule; **loose** for claiming two architectural systems.

**Supported:** lit conditions `divergent_guilford` vs `convergent_constrained` (entropy / anchors).

---

## 2. Working memory & executive control

**Sources:** Baddeley multi-component WM ([overview](https://en.wikipedia.org/wiki/Baddeley%27s_model_of_working_memory)); Miyake et al. (2000) unity/diversity of EFs ([PDF](https://columbia.edu/cu/psychology/tor/Papers/Unity_Diversity_Exec_Functions.pdf)); Diamond (2013) EF review ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4084861/)).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Goal maintenance (central executive) | Protect spans \(p(s)=1\); `anchor_pull` | **tight** |
| WM load management | PromptDict compact + `filter_spans_for_burst` | **moderate–tight** |
| Updating | Visited set \(V\); novelty of unused typologies | **moderate** |
| Shifting | Mode switch mid-path (diverge→converge) | **moderate** |
| Inhibition | Suppress revisit / backward layer jumps | **loose–moderate** |

**(b) Predictions:** Under compaction (load), unprotected goals → goal neglect → ↓\(R\); protect-hot-set should preserve `constraint_fidelity` / `anchor_R`. Dual-task analog: compact then burst → \(R\) drop unless protect.  
**(c) Closeness:** **tight** for protect≈goal maintenance; **loose** for phonological loop / sketchpad.

**Partially supported:** compaction bridge — PromptDict `protect_compact` mid_constraint_R=**1.000** vs `lossy_truncate` **0.200** (settled for load). End-to-end protect→burst still open: offline WM truncate sim **rejected** P6 (pool-shrink artifact). Next: [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) **RT2**.

---

## 3. Global Workspace Theory (GWT / GNW)

**Sources:** Baars (1988/1997) GWT ([PDF](http://bernardbaars.pbworks.com/f/BaarsJCS1997.pdf)); Dehaene & Changeux GNW ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/)); [Wikipedia GWT](https://en.wikipedia.org/wiki/Global_workspace_theory).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Competing coalitions | `multi_path_burst` candidate paths | **tight** (computational) |
| Broadcast winner | Select-by-\(H\) (or future causal validate) | **tight** |
| Receiving specialists | Downstream IV / Bridge / Kineteq tools | **moderate** (orchestration analog) |
| Ignition threshold | Meter gate / weak-IV reject | **loose–moderate** |

**(b) Predictions:** Multipath + evaluate ≥ single-seed on \(H\); broadcasting a low-\(R\) path should fail causal/validation gates more often.  
**(c) Closeness:** **tight** for ToT-as-coalitions; **loose** for consciousness claims.

**Supported:** `multipath_tot` / k-sweep select-by-\(H\) ≥ v2 on \(H\) (lit+sweep); select-by-\(C\) harms \(R\) (G1 ΔR≈+0.10 for H vs C). Orchestration broadcast → CausalBridge/Kineteq: see bridge doc (mostly untested; **RT10**).

---

## 4. Predictive processing / active inference

**Sources:** Friston free-energy / predictive coding ([doi:10.1098/rstb.2008.0300](https://doi.org/10.1098/rstb.2008.0300); [NRN PDF](https://www.fil.ion.ucl.ac.uk/~karl/NRN.pdf)); Clark *Surfing Uncertainty* (2016); active inference reviews ([doi:10.1111/tops.12704](https://doi.org/10.1111/tops.12704)).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Hypothesis sampling | Lateral hops / novelty term | **moderate** |
| Precision-weighted priors | Protect anchors + `anchor_pull` (high precision) | **moderate** |
| Expected free energy explore/exploit | \(C\) vs \(R\) / select-by-\(H\) | **loose–moderate** |
| Policy selection | \(\pi\); multipath | **moderate** |

**(b) Predictions:** High-precision anchors stabilize \(R\); exploratory hops raise \(C\) and prediction-error-like entropy; value from meter ≈ soft EFE proxy (not formal FEP).  
**(c) Closeness:** **loose–moderate** — useful metaphor; no free-energy math in meter.

**Behavioral PP supported:** `precision_high` R=0.891 ≥ `precision_low` 0.740 (PP1); low precision ↑C (PP2). Formal FEP math still absent.

---

## 5. Cognitive control / conflict monitoring

**Sources:** Botvinick et al. (2001) conflict monitoring ([doi:10.1037/0033-295X.108.3.624](https://doi.org/10.1037/0033-295x.108.3.624)).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Conflict signal | Low recent `anchor_R` / typology thrash / layer backjump | **moderate** |
| Control recruitment | `anchor_schedule` forced protect visit | **tight** |
| Post-conflict slowing | Temporary ↑`anchor_pull` / ↓`side_hop_prob` | **moderate** (knob schedule) |

**(b) Predictions:** Adaptive schedule (conflict-triggered anchors) > fixed schedule on \(H\) under noisy fixtures; over-forcing anchors ↓\(C\).  
**(c) Closeness:** **tight** for schedule-as-control; **loose** for ACC identity.

**Supported (fixed):** `conflict_schedule_2` H=0.763 ≥ v2 0.754 (P7, 5/8) with C cost (~0.04). Adaptive conflict schedule **open** → **RT4**.

---

## 6. Analogical / relational reasoning

**Sources:** Gentner (1983) structure-mapping ([doi:10.1207/s15516709cog0702_3](https://doi.org/10.1207/s15516709cog0702_3)); Holyoak pragmatic analogy; SME lineage.

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Relational structure | Motifs \(\mathcal{M}\); typed paths | **tight** |
| Structure-mapping | `motif_jump` / `motif_weight` | **tight** |
| Systematicity bias | Prefer connected motif systems over isolated spans | **moderate** |
| Analogical transfer | Cross-fixture motif reuse | **moderate** (experimentable) |

**(b) Predictions:** Motif-guided paths ↑\(R\), ↓\(C\) (lit: motif_jump); hybrid motif+novelty recovers \(H\).  
**(c) Closeness:** **tight** for motif≈relational skeleton.

**Supported (within-fixture):** `motif_jump` highest \(R\) / mono, lowest \(C\) (L1). Cross-fixture transfer **open** → **RT7** (P9).

---

## 7. Insight / representational change

**Sources:** Knoblich, Ohlsson et al. (1999) constraint relaxation / chunk decomposition ([JEP:LMC](https://doi.org/10.1037/0278-7393.25.6.1534)); Ohlsson representational change.

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Impasse | Local motif cluster / low novelty plateau | **moderate** |
| Constraint relaxation | `side_hop_prob` ignoring layer bias | **moderate–tight** |
| Chunk decomposition | Split motif / visit atypical typology | **loose–moderate** |
| Restructuring | Layer jump that unlocks goal/outcome | **moderate** |

**(b) Predictions:** Occasional side-hops raise \(C\) and can unlock better \(H\) vs pure convergent; too many → ↓\(R\).  
**(c) Closeness:** **moderate**.

**Partially supported:** v2 `side_hop_prob=0.18` in hybrid; dedicated insight-impasse protocol **untested**.

---

## 8. Soar / ACT-R problem-space search

**Sources:** Newell Soar / problem spaces; Anderson ACT-R ([doi:10.1037/0033-295X.111.4.1036](https://doi.org/10.1037/0033-295x.111.4.1036)).

| Cognitive construct | Our construct | Closeness |
| --- | --- | --- |
| Problem space | Span graph over \(\mathcal{S}\) | **tight** |
| Operator | Hop under \(\pi\) | **tight** |
| Goal stack | Protect / trajectory \(T\) | **moderate–tight** |
| Production conflict resolution | Score terms in v2; multipath select | **moderate** |
| Declarative chunks | Motifs / PromptDict entries | **loose–moderate** |

**(b) Predictions:** Layer-monotonic operators improve planning-like `layer_mono`; deeper planning (ToL analog) favors `layer_cot` / multipath.  
**(c) Closeness:** **tight** for search formalism; **loose** for full ACT-R timing/activation.

**Supported:** layer_cot / multipath competitive on \(H\); ToL-style depth sweep **untested**.

---

## 9. Optional briefs

### Conceptual spaces (Gärdenfors)

Typology × layer as quality dimensions; hops = trajectories in a conceptual space. **Closeness:** loose–moderate. Predicts smooth exploratory paths (Boden exploratory) vs transformational rule changes (alter protect grammar — P2).

### Metacognition / monitoring

CreativityMeter as metacognitive evaluator; select-by-\(H\) = confidence/control. Causal weak-IV / placebo as **epistemic** metacontrol (bridge doc). **Closeness:** moderate for meter-as-monitor; loose for feeling-of-knowing.

---

## 10. Tightest analogs (ranked)

| Rank | Analog | Why |
| --- | ---: | --- |
| 1 | Dual-process diverge/converge | Directly matches C vs R conditions already measured |
| 2 | GWT coalitions → broadcast | Multipath_tot + select-by-H; extends to Bridge/Kineteq routing |
| 3 | WM goal maintenance / protect | Compaction + anchors; goal-neglect experiments |
| 4 | Structure-mapping / motifs | motif_jump empirical signature |
| 5 | Conflict-triggered control | Natural refinement of `anchor_schedule` |

---

## 11. Refined propositions (cognition-grounded)

| ID | Claim | Theory root | Status |
| --- | --- | --- | --- |
| **P1** | Constrained divergent \(\pi_{v2}\) improves \(H\) vs random without collapsing \(C\) | Dual-process + CST | **Supported** (sweep 2026-07-09; strong/moderate) |
| **P2** | Anchor schedule raises `anchor_R` vs unconstrained burst | Conflict control / WM goals | **Supported** (strong) |
| **P3** | Forward layer bias improves trajectory quality vs pure divergent | Soar/ACT-R + CoT | **Supported** (mono 8/8; H still < motif specialist) |
| **P4** | Divergent ↑\(C\)/entropy vs convergent | Dual-process / Guilford | **Supported** (strong) |
| **P5** | Multipath select-by-\(H\) ≽ single v2 on \(H\) | GWT / ToT | **Supported** (moderate; k↑ helps; lit H=0.768) |
| **P6** | Protect-hot-set after compact preserves \(R\) under load | WM load / goal neglect | **Rejected** offline truncate-sim (artifact); redesign w/ PromptDict → **RT2** |
| **P7** | Tighter `anchor_schedule` (conflict-like) ≽ default v2 on \(H\) | Botvinick | **Supported** (moderate; schedule=2); adaptive → **RT4** |
| **P8** | Side-hops raise \(C\) without large \(R\) loss | Insight / Ohlsson | **Mixed** (C↑ supported; R drop >0.08 rejected) |
| **P9** | Motif structure-mapping transfers across fixtures | Gentner / Holyoak | **Untested** → **RT7** (within-fixture L1 supported) |
| **P10** | High-\(R\) paths align better with IV causation | LayerCausal | **Weak / inconclusive** (mock overlap) → **RT3** |
| **P11** | Burst-proposed instruments beat random Z | Explore Z | **Weak** (mock_iv F tied) → **RT3** |
| **P12** | Orchestration broadcast of high-\(H\) path | GWT + Fabric | **Untested** → **RT10** |
| **P13** | Multipath value-fn: H-optimal vs R-optimal vs C-harmful; IV-diag for causal-prep | GWT / metacontrol | **Partial** (G1+H/R columns); IV-diag → **RT1** |
| **P14** | Soft mono-gating → motif-like mono without motif \(C\) death | Soar / CoT | **Open** → **RT5** |
| **P15** | Protect-compact → burst preserves mid-constraints iff protect filter | WM + compaction | Compact mid_R **supported**; coupling → **RT2** |
| **P16** | Motif–burst hybrid schedule Pareto between motif & v2 | Structure-mapping + dual-process | **Open** → **RT8** |
| **P17** | Longer-horizon intermittent diverge/converge can beat hop=5 incubations | Dual-process / incubation | hop=5 **rejected** (I1/I2); longer → **RT6** |

Empirical inventory: [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) · [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md).

Falsifiers unchanged for P1–P5; for P10–P17 see [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) and [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md).

---

## 11b. Empirical status (2026-07-09)

| Supported (integrate) | Rejected / do-not-ship | Weak / open |
| --- | --- | --- |
| P1–P5, P7, PP1/PP2, G1–G3, L1/L2, PL1, S1–S3, B4 (structural) | P6 (artifact), I1, I2, P8b (R tax) | B1/B2 mock IV; P9–P12, P13–P17 |

**Production stance:** keep `for_v2` + multipath select-by-\(H\); treat motif_jump as fidelity specialist; do not ship hop=5 incubation/two-phase or truncate-as-WM-control.

---

## 11c. Open questions → next experiments

| Question | Evidence gap | Doc |
| --- | --- | --- |
| Value function beyond \(H\) for IV-prep | mp_k5_R vs H; G1 | RT1 |
| Real protect→burst goal neglect | P6 artifact vs PromptDict mid_R=1.0 | RT2 |
| Non-mock burst Z first-stage F | B1 tie | RT3 |
| Adaptive conflict recovers C | P7 C cost | RT4 |
| Mono gates without motif C death | motif mono vs C | RT5 |
| Incubation at hops≥10 | I1/I2 | RT6 |
| Cross-fixture motif transfer | P9 | RT7 |
| Motif schedule hybrid | L1 tradeoff | RT8 |
| Meter + mid_constraint / IV dims | mid_R invisible to hop meter | RT9 |
| Bridge route stub | B5 | RT10 |

Full protocols: [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md).

---

## 12. Closely related experimental analogs (ranked)

Closer than generic “creativity tests”; offline-automatable preferred.

| # | Analog | Protocol sketch | Metrics | Predicted winner vs v2/multipath | Effort |
| --- | --- | --- | --- | --- | --- |
| 1 | Task-switching / set-shifting | Mid-path flip knobs (novelty→anchor) at hop \(n/2\) | \(H\), switch cost (Δentropy) | Two-phase ≥ single-mode v2 on \(H\) | **S** |
| 2 | Goal neglect under compact | `protect_compact` → burst with/without protect filter | `anchor_R`, `constraint_fidelity`, \(R\) | Protect filter ≫ drop-protect | **S** |
| 3 | RAT-style remote associates | Link spans that co-resolve a held-out “associate” typology | Hit rate, \(C\), \(R\) | motif+novelty > random; multipath best \(H\) | **M** |
| 4 | Tower of London / planning depth | Require layer-monotonic goal before outcome; vary hop budget | `layer_mono`, plan success, \(H\) | `layer_cot` / multipath > divergent | **M** |
| 5 | Dual-task interference | Compact (load) then burst; compare schedule | \(R\) drop, recovery with anchors | Convergent recovers \(R\) | **S** |
| 6 | Incubation schedule | Alternate diverge/converge blocks | \(H\) vs fixed | Intermittent ≥ fixed on hard fixtures | **M** |
| 7 | Beam / MCTS + meter value | Deepen multipath with meter as value / UCB | \(H\), compute | Meter-guided beam ≥ flat k-seed | **M** |
| 8 | Analogical transfer | Train motifs on fixture A; hop on B | Transfer \(R\), motif reuse | Motif prior > cold start | **M** |
| 9 | Indication vs causation diagnosticity | Score hops by LayerCausal indication vs IV edge | Alignment, weak-IV rate | High-\(R\) paths → better causation match | **M** |
| 10 | N-back-like span load | Cap candidate set size; force update of \(V\) | Goal neglect rate | Protect schedule mitigates | **S** |
| 11 | Instrument exploration | Burst proposes Z candidates → IV first-stage F | F-stat, \(\beta_{IV}\) SE | Burst-Z > random-Z | **M** |
| 12 | Orchestration broadcast stub | High-\(H\) path → Bridge dry-run next step | Route correctness, artifact OK | Meter-gated route > random tool | **L** |

---

## 13. References (selected)

1. Evans, J. St. B. T. (2008). Dual-processing accounts… *Annu. Rev. Psychol.* [doi](https://doi.org/10.1146/annurev.psych.59.103006.093629)  
2. Kahneman, D. (2003). A perspective on judgment and choice. *Am. Psychol.* [PDF](https://pages.ucsd.edu/~mckenzie/Kahneman2003AmPsych.pdf)  
3. Baddeley WM model — [overview](https://en.wikipedia.org/wiki/Baddeley%27s_model_of_working_memory)  
4. Miyake et al. (2000). Unity and diversity of executive functions. [PDF](https://columbia.edu/cu/psychology/tor/Papers/Unity_Diversity_Exec_Functions.pdf)  
5. Baars, B. J. — GWT [PDF](http://bernardbaars.pbworks.com/f/BaarsJCS1997.pdf); Dehaene GNW [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/)  
6. Friston (2009) predictive coding [doi](https://doi.org/10.1098/rstb.2008.0300); Friston (2010) FEP [NRN](https://www.fil.ion.ucl.ac.uk/~karl/NRN.pdf)  
7. Botvinick et al. (2001). Conflict monitoring… [doi](https://doi.org/10.1037/0033-295x.108.3.624)  
8. Gentner (1983). Structure-mapping. [doi](https://doi.org/10.1207/s15516709cog0702_3)  
9. Knoblich et al. (1999). Constraint relaxation… insight. [doi](https://doi.org/10.1037/0278-7393.25.6.1534)  
10. Anderson et al. (2004). ACT-R. [doi](https://doi.org/10.1037/0033-295x.111.4.1036)  

Compaction: [ISOLATES_COMPACTION_REASONING.md](../../docs/ISOLATES_COMPACTION_REASONING.md). Causal Fabric: [GLOBAL_SYSTEM.md](../../docs/GLOBAL_SYSTEM.md).
