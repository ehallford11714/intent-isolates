# Iterative Reasoning-Trace Training Report

**Package:** `intentisolates` ≥ 0.4.1  
**Run stamp:** `20260710T001218Z`  
**Stance:** Offline computational analogs. Transparent RT-guided hill-climb / evolutionary updates — **not** neural training.  
**Theory queue:** [NEXT_EXPERIMENTS_REASONING_TRACE.md](NEXT_EXPERIMENTS_REASONING_TRACE.md) (RT1–RT11)  
**Artifacts:** [EPOCH_TRAJECTORY.md](../experiments/results/iterative_epochs/EPOCH_TRAJECTORY.md) · [charts](../experiments/results/charts/) · [trajectory_latest.json](../experiments/results/iterative_epochs/trajectory_latest.json)

---

## 1. Executive summary

Over **10 epochs**, an RT-phased policy search raised mean **H from 0.753 → 0.779** (+0.026) and **R from 0.828 → 0.897** (+0.070) on a fixed 4-fixture × 3-seed grid, with only a small **C drop (0.702 → 0.696)**. **`layer_mono` rose 0.600 → 0.800**.

Elite policy at epoch 9: **multipath k=7, select_by=H, protect_compact=on, anchor_schedule=2, anchor_pull≈0.80, layer_bias≈0.47**. Best epoch = **9** (tied H with epochs 6–8; slight C polish).

| Hypothesis | Verdict from this cycle |
| --- | --- |
| **RT1** (H vs R vs C vs iv_diag) | **Supported** — G1 replicate; `iv_diag` competitive with H; select-by-C collapses R |
| **RT2** (protect→burst) | **Mixed / partial** — protect wins inside the epoch loop on H+R; standalone A-vs-B anchor gap not ≥0.10 (B shrinks mid pool → inflated path metrics) |
| **RT3** (burst Z / IV) | **Inconclusive for F** — causal suite present; mock IV only; structural Z counts logged; hybrid polish kept H-elite |
| **RT4** (conflict schedule) | **Supported in-loop** — accepting schedule=2 + higher anchor_pull lifted H/R/mono; schedule grid kept that elite |
| **RT5** (layer_mono) | **Partially supported** — mono already high after RT2/RT4; further layer_cot-like variants did not beat elite on objective |

---

## 2. Methods

### 2.1 Baseline experiment inventory (fresh runs)

| Experiment | Config | Stamp / notes |
| --- | --- | --- |
| `span_burst_creative.py` | default fixtures/hops | `20260710T000721Z` — creative_burst entropy + anchors supported |
| `lit_review_burst_experiments.py` | 4×3, hops=5 | `20260710T000756Z` — multipath_tot **H=0.769**; v2 R>v1 |
| `theory_corpus_sweep.py` | **seeds=3**, hops=5 (bounded) | `20260710T000841Z` — multipath_k7_H **0.774**; G1 intact |
| PromptDict `reasoning_trace_compaction.py` | budget 1200 | `20260710T000802Z` — protect mid_R=**1.0** vs truncate **0.2** |
| `p0_multipath_selector_bakeoff.py` (RT1) | 4×3, k∈{3,5} | `20260710T001154Z` |
| `p0_protect_compact_burst.py` (RT2) | 4×3 | `20260710T001155Z` |
| `p0_rt3_burst_iv_probe.py` (RT3) | causal fixtures | `rt3_iv_probe_latest` — structural Z; mock_iv soft |

### 2.2 Iterative trainer

Script: `experiments/iterative_reasoning_training.py`

**Eval set (frozen):** first 4 `theory_corpus_sweep.FIXTURES` × **3** seeds × hops=**5**.  
**Objective:** maximize mean **H**, with soft **R floor = 0.78** (linear penalty if below).  
**Update method:** each epoch evaluates a **finite variant neighborhood** dictated by the active RT phase; keep elite if objective improves. No torch / gradient steps.

### 2.3 Epoch → RT guidance map

| Epoch | `guided_by` | Phase | What the update searches |
| ---: | --- | --- | --- |
| 0 | baseline | floor_v2_single | Default v2 knobs, single-path; schedules multipath for t=1 |
| 1 | baseline | floor_multipath_H | k ∈ {3,5,7} with select_by=H |
| 2 | **RT1** | value_fn_bakeoff | select_by ∈ {H,R,C,iv_diag} × k ∈ {3,5} (+ k7_H) |
| 3 | **RT1** | value_fn_refine | Refine around elite select_by / k |
| 4 | **RT2** | protect_on | protect_compact on vs off |
| 5 | **RT2** | protect_toggle | protect + mild anchor_pull / schedule nudge |
| 6 | **RT4** | conflict_schedule | `anchor_schedule` × `anchor_pull` grid |
| 7 | **RT5** | layer_mono | layer_bias / soft_mono / layer_cot-like |
| 8 | **RT3** | iv_diag_or_hybrid | iv_diag select + hybrid H+protect; coordinate knob deltas |
| 9 | **RT3** | hybrid_polish | Final coordinate ascent (no further update after eval) |

Each `epoch_XX.json` records `guided_by`, `action`, `accepted`, full policy, mean meters, and path-level reasoning-trace summaries (span ids, typology path, multipath candidate meter scores).

---

## 3. Baseline results (anchors for the loop)

### Lit burst (fresh)

| condition | C | R | H |
| --- | ---: | ---: | ---: |
| creative_burst_v2 | 0.709 | 0.828 | 0.759 |
| **multipath_tot** | 0.692 | 0.874 | **0.769** |

### Sweep (seeds=3)

| condition | C | R | H |
| --- | ---: | ---: | ---: |
| creative_burst_v2 | 0.728 | 0.792 | 0.752 |
| multipath_k5_H | 0.721 | 0.838 | 0.770 |
| **multipath_k7_H** | 0.724 | 0.841 | **0.774** |
| multipath_k5_C | 0.771 | 0.737 | 0.749 |

### RT1 satellite

- Best: `mp_k5_H` H=**0.770**, R=0.874  
- `iv_diag` mean H≈0.765 / R≈0.866 — **competitive with H** (success criterion a)  
- Select-by-C R≈0.716 ≪ H R≈0.866 — **G1 replicated**

### RT2 satellite

- Protect filter mid_R=0.938; R ≥ D−0.05 holds  
- A−B `anchor_R` not ≥ +0.10 (**partial**): B drops mid anchors (neglect=1.0) but can still score high path R on a shrunken pool — same class of caution as rejected P6 truncate sim

### Compaction

- `protect_compact` mid_R=**1.000** vs `lossy_truncate` **0.200** (replicates prior PromptDict finding)

---

## 4. Epoch-by-epoch trajectory

| epoch | RT | C | R | H | layer_mono | accepted action |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 0 | baseline | 0.702 | 0.828 | 0.753 | 0.600 | schedule multipath |
| 1 | baseline | 0.712 | 0.840 | 0.766 | 0.667 | **k7_H** |
| 2 | RT1 | 0.710 | 0.846 | 0.768 | 0.683 | keep (H elite) |
| 3 | RT1 | 0.710 | 0.846 | 0.768 | 0.683 | keep |
| 4 | RT2 | 0.710 | 0.846 | 0.768 | 0.683 | **protect_on** |
| 5 | RT2 | 0.709 | 0.858 | 0.772 | 0.717 | **protect_on_anchor+** |
| 6 | RT4 | 0.695 | 0.897 | **0.779** | **0.800** | keep (schedule/pull elite) |
| 7 | RT5 | 0.695 | 0.897 | 0.779 | 0.800 | keep (layer variants no gain) |
| 8 | RT3 | 0.695 | 0.897 | 0.779 | 0.800 | **layer−** (small polish) |
| 9 | RT3 | **0.696** | **0.897** | **0.779** | **0.800** | final |

Charts:

- `experiments/results/charts/epoch_crh_trajectory.png`
- `experiments/results/charts/epoch_h_mono_mid.png`

### What changed when (training narrative)

1. **Baseline→multipath (e0–e1):** Moving from single-path v2 to multipath **k=7 / H** is the largest early H lift (+0.013), matching lit/sweep ToT findings.  
2. **RT1 (e2–e3):** Full value-fn bakeoff kept **select_by=H**; R/C/iv_diag did not beat H on the H-primary objective (iv_diag was close in the satellite).  
3. **RT2 (e4–e5):** Enabling **protect_compact** then **anchor_pull↑ + schedule→2** improved R and H; mid_constraint_R stayed 1.0 under the loop’s filter.  
4. **RT4 (e6):** Conflict/schedule grid locked schedule=2 / pull≈0.80 — mono jumps to 0.80; C dips slightly (known P7 tradeoff).  
5. **RT5 (e7):** Soft mono / layer_cot-like explores **did not** beat the RT2+RT4 elite (mono already high).  
6. **RT3 hybrid (e8–e9):** iv_diag select not preferred over H; slight **layer_bias↓** polish retained H while nudging C up 0.001.

---

## 5. Final policy vs epoch_0

| Knob | Epoch 0 | Epoch 9 (best) | Δ |
| --- | ---: | ---: | --- |
| novelty_weight | 1.10 | 1.10 | 0 |
| anchor_pull | 0.70 | **0.80** | +0.10 |
| layer_bias | 0.55 | **0.47** | −0.08 |
| motif_weight | 0.45 | 0.45 | 0 |
| anchor_schedule | 3 | **2** | −1 |
| side_hop_prob | 0.18 | 0.18 | 0 |
| multipath | false | **true** | on |
| k | 5 | **7** | +2 |
| select_by | H | **H** | — |
| protect_compact | false | **true** | on |

| Meter | Epoch 0 | Epoch 9 | Δ |
| --- | ---: | ---: | ---: |
| C | 0.702 | 0.696 | −0.006 |
| R | 0.828 | 0.897 | **+0.070** |
| H | 0.753 | 0.779 | **+0.026** |
| layer_mono | 0.600 | 0.800 | **+0.200** |
| mid_constraint_R | 1.000 | 1.000 | 0 |

---

## 6. Supported / refuted / open (RT lens)

### Supported

- **Multipath select-by-H** remains the production default for harmonic quality (RT1 / P5 / G2).  
- **G1:** select-by-C is a fidelity anti-pattern (satellite + epoch bakeoff).  
- **iv_diag** is a viable alternate objective nearly matching H (RT1 success a).  
- **Conflict schedule=2 + moderate↑ anchor_pull** with multipath+protect raises R/H/mono in-loop (RT4 / P7 refinement).  
- **Iterative transparent training works:** RT-phased neighborhoods produce a clear H/R trajectory without opaque models.

### Partial / mixed

- **RT2** protect helps the loop, but the **standalone A vs B success rule** (Δanchor_R≥0.10) did not hold — B’s mid-drop neglects constraints while path meters can still look strong. Prefer mid_R + matched coverage as gates (aligns with NEXT doc redesign).  
- **RT5** soft mono: further bias not needed once RT2/RT4 already lifted mono to 0.80; no evidence against layer_cot itself (prior P3 still stands).

### Open / weak

- **RT3** first-stage F: only structural Z counts + `LayerCausalSuite(mock_iv=True)`; no non-degenerate F uplift claimed.  
- Outcome / LLM-judge (RT11) not run.  
- Fixtures×seeds modest (4×3); sweep used seeds=3 for runtime.

---

## 7. Limitations

- Offline meters only; hop budget=5.  
- Protect filter is an **isolate analog** of PromptDict `protect_compact`, not a full token-budget eviction replay inside every epoch.  
- Epoch update evaluates many variants; still discrete search, sensitive to neighborhood design.  
- Float noise in serialized knobs (e.g. 0.7999…) is binary float artifact — treat as 0.80.  
- Incubation / two_phase still **not** recommended (prior I1/I2); not reopened here.

---

## 8. Recommendations

1. **Production default:** multipath **k=5..7**, `select_by="tradeoff_harmonic"` (H).  
2. **When fidelity matters:** turn **protect filter** on before burst; prefer `anchor_schedule=2`, `anchor_pull≈0.80` over stock schedule=3 when R/mono matter more than max C.  
3. **Do not** select multipath winners by C for reasoning traces.  
4. **Optional:** try `iv_diag` when preparing IV / early-layer paths; expect near-H performance.  
5. **Next experiments:** finish RT2 with PromptDict-matched token budgets + coverage gates; RT3 with non-mock first-stage F; RT5 mono-gating at hops≥8; RT6 long-horizon incubation only after that.

Reproduce:

```bash
# from IntentIsolates/
python experiments/span_burst_creative.py
python experiments/lit_review_burst_experiments.py
python experiments/theory_corpus_sweep.py --seeds 3 --hops 5
python experiments/p0_multipath_selector_bakeoff.py
python experiments/p0_protect_compact_burst.py
python experiments/p0_rt3_burst_iv_probe.py
python experiments/iterative_reasoning_training.py --epochs 10 --fixtures 4 --seeds 3
python experiments/plot_epochs.py
```

---

## 9. File index

| Path | Role |
| --- | --- |
| `experiments/iterative_reasoning_training.py` | RT-guided 10-epoch trainer |
| `experiments/p0_multipath_selector_bakeoff.py` | RT1 satellite |
| `experiments/p0_protect_compact_burst.py` | RT2 satellite |
| `experiments/p0_rt3_burst_iv_probe.py` | RT3 soft probe |
| `experiments/plot_epochs.py` | Epoch charts |
| `experiments/results/iterative_epochs/epoch_00.json` … `epoch_09.json` | Per-epoch traces |
| `experiments/results/iterative_epochs/EPOCH_TRAJECTORY.md` | Knob + meter table |
| `experiments/results/charts/epoch_crh_trajectory.png` | C/R/H vs epoch |
| `experiments/results/charts/epoch_h_mono_mid.png` | H / mono / mid_R |
