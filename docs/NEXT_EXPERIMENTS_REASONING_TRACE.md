# Next Experiments: Reasoning-Trace Quality

**Status:** P0 E1–E3 **ran** · RT2b/RT3b/RT4b/RT5/RT8/RT10 batch **ran** (`20260710T0047Z`) — see **[RT2B_RT10_EXPERIMENT_BATCH_REPORT.md](RT2B_RT10_EXPERIMENT_BATCH_REPORT.md)**  
**Package:** `intentisolates` ≥ 0.4.1  
**Evidence:** **[RT2B_RT10_EXPERIMENT_BATCH_REPORT.md](RT2B_RT10_EXPERIMENT_BATCH_REPORT.md)** · **[P0_FOLLOWUP_EXPERIMENT_RESULTS.md](P0_FOLLOWUP_EXPERIMENT_RESULTS.md)** · [p0_followup_latest.md](../experiments/results/p0_followup_latest.md) · [COMPILED_EXPERIMENTATION_20260709.md](../experiments/results/COMPILED_EXPERIMENTATION_20260709.md) · [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) · [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md) · [ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md](ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md) · [EPOCH_TRAJECTORY.md](../experiments/results/iterative_epochs/EPOCH_TRAJECTORY.md)  
**Theory:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md)  
**Related queue:** [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md) (cognition + bridge E1–E10; this doc focuses on **reasoning-trace R / layer_mono / mid_constraint / IV quality**)

**Stance:** Offline computational analogs. Prefer automatable meters first; LLM-as-judge only where noted.

### RT2b–RT10 batch (2026-07-10) — post-RT234 redesign

| Exp | Verdict | Headline |
| --- | --- | --- |
| **RT2b** | **Rejected** (H gate) | mid_R 0.938≫0.500; H 0.758<0.787 under **matched** pool — trunc H not pool artifact |
| **RT3b** | **Rejected** | path-only IV 0/4 wins; boost was identification-necessary |
| **RT4b** | **Mixed** | adapt H 0.777≈elite 0.781; C↑ small; trainer bake-in ok; keep fixed s2 default |
| **RT5** | **Mixed** | soft/hard mono > layer_cot; H≈elite; strict success false; h8≈h10 |
| **RT8** | **Mixed** | `every_4` soft winners: H≥elite, mono 0.825, C near elite |
| **RT10** | **Supported** | gated rubric 0.980 vs random 0.627; illegal=0; kineteq absent |

### P0 slate E1–E3 (2026-07-10) — authoritative offline bakeoff

| Exp | Maps to | Verdict | Headline numbers |
| --- | --- | --- | --- |
| **E1** | RT1 / P13 | **Supported** (Pareto); iv_diag mixed | k7 H-select **H=0.776**; k5 R-select **R=0.850**; G1 ΔR k5 **+0.085** (8/8); iv_diag k5 reject / k7 support |
| **E2** | RT2 / P15 | **Supported** mid_R+R; trunc H **artifact** | mid_R 1.0 vs 0.188; protect→mpH **R=0.897**; trunc pool 2.9 vs protect 5.5 |
| **E3** | RT6 / P17 | **Rejected / archive** | incub H 0.686/0.695 ≪ v2 0.754/0.790 (0/8) at hops 5 & 8 |

Script: `python experiments/p0_followup_experiments.py` · charts: `p0_e1_*.png`, `p0_e2_*.png`, `p0_e3_*.png`.

### Iterative-cycle progress (epochs 0–9)

| RT | Status | Epoch evidence | Satellite |
| --- | --- | --- | --- |
| **RT1** | **Supported (closed by E1)** | e2–e3 kept `select_by=H`, k=7; G1 replicate | `rt1_multipath_bakeoff_latest` + **p0 E1** |
| **RT2** | **Mixed** (mid_R/R win; H not) | e4–e5 `protect_on`; **p0 E2** + coverage-gated redesign | `rt2_coverage_gated_latest` mid_R 0.938≫0.50; R win; trunc H |
| **RT3** | **Supported** (causaliv upgrade) | e8–e9 hybrid polish; kept H-elite | `rt3_iv_upgrade_latest` — burst Z wins **3/4** on F/weak |
| **RT4** | **Supported** (adaptive) | e6 locked schedule=2, pull≈0.80; H=0.779, mono=0.800 | `rt4_adaptive_conflict_latest` — `adaptive_loosen_0.55` **7/8** |
| **RT5** | **Partial** | e7 layer variants did not beat post-RT4 elite | mono already 0.80 after RT2/RT4 |
| **RT6** | **Archived (E3)** | structured alt-2 fails hops 5 & 8 | **p0 E3** |

Loop headline: epoch_0 H=**0.753** → epoch_9 H=**0.779**, R **0.828→0.897**, mono **0.600→0.800**.

**Post-loop redesign:** [PROPOSED_NEXT_AFTER_RT234.md](PROPOSED_NEXT_AFTER_RT234.md) (RT2b / RT4b / RT9 / RT3b …).

---

## Result anchors (cite these)

| Finding | Numbers | Source |
| --- | --- | --- |
| Multipath H-optimal | lit `multipath_tot` **H=0.768**; sweep `multipath_k7_H` **0.774**; **P0 E1** k7_H **0.776** | lit / sweep / p0 |
| **P0 E1** select-by-H wins H | k3/5/7 all **supported** (8/8 vs R/C on H) | p0_followup |
| **P0 E1** select-by-R wins R | k5 R=**0.850** / H=0.760 vs H-select R=0.829 / H=0.771 | p0_followup |
| Select-by-H ≫ select-by-C on R | sweep Δ=+0.102; **P0** k5 Δ=**+0.085**, k7 **+0.111** (8/8) | CLAIM + p0 |
| **P0 E1** iv_diag | k5 **rejected**; k7 **supported** (H=0.772, R=0.862) | p0_followup |
| v2 R-lift vs v1 | lit R **0.820>0.721**; sweep **0.796>0.754** (L2, 5/8) | lit + claim L2 |
| Motif fidelity / creativity tax | lit motif `anchor_R=0.950`, `layer_mono=0.967`, C=**0.590** | lit + L1 |
| Dual-process + precision | div C=0.761 > conv 0.657; `precision_high` R=0.891 vs low 0.740 | P4 / PP* |
| Conflict schedule helps H | `conflict_schedule_2` H=**0.763** ≥ v2 0.754 (P7) | sweep |
| Incubation fail (I1/I2 + **E3**) | alt H≈0.69; structured h5/h8 **0.686/0.695** ≪ v2 — **archive** | rejected |
| Protect mid_R + **E2** burst | mid_R **1.0** vs trunc **0.188**; protect→mpH R=**0.897** | compaction + p0 |
| **RT2b** pool-matched | mid_R **0.938**≫**0.500**; H **0.758**<**0.787** (matched) — trunc H not artifact | rt2b_pool_matched |
| **RT3b** path-only IV | 0/4 wins; F ties without boost | rt3b_path_only_iv |
| **RT10** gated routing | rubric **0.980** vs random **0.627**; illegal=0 | rt10_bridge_routing |
| Causal IV weak | B1/B2 mock F tied — inconclusive | claim table |

**Production do-not-touch from falsifiers:** do not ship naive `incubation_alt` / hop=5 `two_phase` / **structured alt-2 incubation**; do not treat head/tail truncate as a fair WM control; keep `side_hop_prob≈0.18`.

---

## Priority summary

| Priority | IDs | Goal | Status |
| --- | --- | --- | --- |
| **P0** | RT1 / E1 | Multipath value-fn | **DONE** |
| **P0** | RT2 / E2 | Protect→burst | **DONE** (trunc H artifact) |
| **P0** | RT2b | Pool-matched protect H | **DONE / Rejected** (mid_R still wins) |
| **P0** | RT6 / E3 | Structured incubation | **ARCHIVED** |
| **P0** | RT3 / RT3b | IV F + path-only rigor | **DONE** (RT3 supported; RT3b rejected) |
| **P0** | RT4 / RT4b | Conflict adaptive + trainer | **DONE** (RT4 supported; RT4b mixed) |
| **P1** | RT5, RT8 | Planning / motif hybrid | **DONE / Mixed** |
| **P1** | RT7 | Analogical transfer | queued |
| **P2** | RT10 | Bridge routing stub | **DONE / Supported** |
| **P2** | RT9, RT11 | Meter / outcome | queued |

Run order remaining: **RT9 → RT7 → RT11** (optional RT8 hops≥8 re-sweep).

---

## P0 — ship next

### RT1 — Multipath value-function bakeoff (H vs R vs IV-diagnosticity) — **DONE**

- **Status:** **RAN** `python experiments/p0_followup_experiments.py` (E1) + satellite `rt1_multipath_bakeoff` + iterative e2–e3. Authoritative table: [P0_FOLLOWUP_EXPERIMENT_RESULTS.md](P0_FOLLOWUP_EXPERIMENT_RESULTS.md).
- **Hypothesis:** Selecting by \(H\) maximizes harmonic quality; selecting by \(R\) maximizes fidelity but drops \(H\); IV-diag may beat pure \(R\) for causal-prep without C-selection disaster.
- **Design:** 8 fixtures × 5 seeds, hops=5, k∈{3,5,7}; `select_by ∈ {H, R, C, product, iv_diag}`.
- **Result:** (b) Pareto mapped — **H-select wins H** (all k, 8/8); **R-select wins R** (ΔH≈−0.01); **C-select worst on R** (G1 strong). iv_diag: **rejected at k=5**, **supported at k=7**.
- **Default:** keep `select_by=tradeoff_harmonic`; optional `iv_diag` only when k≥7 for IV-prep.

### RT2 — Protect-compact → burst coupling (goal-neglect redo) — **DONE**

- **Status:** **RAN** as P0 E2 in `p0_followup_experiments.py` (soft PromptDict `DictCompressor` + keyword protect).
- **Hypothesis:** Real PromptDict `protect_compact` hot-set + `filter_spans_for_burst` preserves mid-constraints through burst; dropping protect under identical compact budget causes goal neglect (↓R / ↓`constraint_fidelity`).
- **Grounding:** Compaction mid_R protect=**1.0** vs truncate=**0.2**; sweep P6 **rejected** because `wm_truncate_drop` shrunk pool → fake `anchor_R=1.0`. Need non-artifact control.
- **Design:** Conditions: raw→v2; truncate→v2; protect_compact→v2; protect_compact→multipath_H.
- **Result:** mid_R protect=**1.000** vs trunc **0.188** (**supported**); protect→v2 R=**0.886** ≥ raw 0.799 (**supported**); protect→mpH R=**0.897** > trunc 0.851 but H 0.767 < trunc 0.799 (**mixed** on H) — trunc pool **2.875** vs protect **5.5** → **artifact_risk** (same class as P6). Prefer protect→mpH for R; do not rank by trunc H.
- **Default:** document protect_compact before burst; do **not** change hop knobs from truncate H.

### RT2b — Pool-matched protect vs truncate — **DONE / Rejected (H)**

- **Status:** **RAN** `p0_rt2b_pool_matched.py`. Pool/path_len **matched** (5.1 / 4.88). mid_R protect **0.938** ≫ trunc **0.500**; H protect **0.758** < trunc **0.787** — truncate H win is **not** a pool artifact. Protect R near raw (supported secondary).
- **Default:** Keep protect for mid-constraints; do **not** claim H superiority vs truncate even under match. Prefer RT9 meter so H sees mid_R.

### RT3 — Burst-proposed instruments → weak-IV F (replace mock tie) — **DONE**

- **Status:** **RAN** `p0_rt3_burst_iv_upgrade.py` → **Supported** (3/4 fixtures; causaliv). Follow-up **RT3b** path-only (no boost) → **Rejected** (0/4; F ties) — boost was identification-necessary. See batch report.
- **Hypothesis:** Paths from multipath select-by-H propose early-layer Z with higher first-stage F / lower weak-IV than random.
- **Result:** With transparent Z boost: supported. Path-only hard mask: rejected / method note.
- **Default:** Prefer burst/high-R paths for IV **prep** with documented boost proxy; do not claim path-only F superiority.

### RT3b — Path-only IV (no Z boost) — **DONE / Rejected**

- **Status:** **RAN** `p0_rt3b_path_only_iv.py` (`rt3b_path_only_iv_latest`).
- **Result:** 0/4 fixture wins; burst F ≈ random under hard mask. Documents that RT3 column boost was necessary for policy differentiation.

### RT4 — Conflict-adaptive + schedule fine grid (without killing C) — **DONE**

- **Status:** **RAN** `p0_rt4_adaptive_conflict.py` → **Supported** (`adaptive_loosen_0.55`, 7/8). **RT4b** trainer bake-in → **Mixed** (H within 0.005; C lift < +0.01; trainer keeps fixed s2).
- **Default:** Fixed schedule=2 / pull≈0.80 fidelity default; optional `adaptive_loosen_on_calm` when C matters.

### RT4b — Adaptive loosen in trainer — **DONE / Mixed**

- **Status:** **RAN** `p0_rt4b_adaptive_trainer.py` + `Policy.adaptive_policy` in `iterative_reasoning_training.py`.
- **Result:** fixture_ok 3/4; H 0.777 vs elite 0.781; C 0.709 vs 0.704; epoch-6 neighborhood includes adaptive_loosen (accepted `keep`).

---

## P1 — depth & schedules

### RT5 — Planning-depth / layer_monotonicity intervention — **DONE / Mixed**

- **Status:** **RAN** `p0_rt5_mono_gating.py` at hops {8,10}. Soft/hard mono > layer_cot (+0.04–0.06) and C > motif; H ≈ elite (−0.001 to −0.003); **strict success false**. h8≈h10 (pool exhaustion).
- **Default:** Do **not** ship mono-gate as default; elite multipath-H remains best H at depth.

### RT6 — Incubation / intermittent diverge–converge (longer horizon) — **DONE / ARCHIVED**

- **Status:** **RAN** as P0 E3 (strict alt-2 convergent↔divergent at hops **5 and 8**). Longer {10,12} not needed — already fails hard.
- **Hypothesis:** Rejected I1/I2 were **horizon artifacts** at hops=5; at hops≥8 with block size 2, intermittent schedules can recover H ≥ v2.
- **Result:** structured_incubation H=**0.686** (h5) / **0.695** (h8) vs v2 **0.754** / **0.790** and multipath_H **0.771** / **0.803**; fixture wins **0/8** both horizons — **rejected / archive**. Dual-process still works as **fixed** modes (div/conv), not as alternating schedule.
- **Default:** **no** incubation schedule knobs; prefer multipath-H or fixed dual-process presets.

### RT7 — Analogical transfer across fixtures

- **Hypothesis:** Motif priors fit on fixture A raise R / motif-reuse on related fixture B vs cold start, without forcing full `motif_jump` C tax.
- **Grounding:** Within-fixture motif_jump R/mono elite (L1/S3); P9 **untested** for transfer.
- **Design:** Pair fixtures (planning↔constraint-heavy; creative↔tool-log). Fit motif co-visit stats on A; hop on B with `motif_weight` prior vs cold v2 vs motif_jump.
- **Metrics:** transfer R, motif reuse rate, H, C.
- **Success:** Prior R > cold on ≥3/4 pairs; C ≥ motif_jump + 0.05.
- **Effort:** M · **Offline:** yes · **LLM judge:** no
- **Tests:** P9 Gentner

### RT8 — Motif–burst hybrid schedule (fidelity without C death) — **DONE / Mixed**

- **Status:** **RAN** `p0_rt8_motif_burst_hybrid.py`. Soft winners: `hybrid_every4_mw{0.45,0.7}` H **0.781** ≥ elite **0.779**, mono **0.825**, C **0.688** ≥ elite−0.05. Strict mono≥elite+0.05 with H≥elite: soft path only.
- **Default (optional):** `every_4` motif schedule when mono lift desired without motif_jump C death.

---

## P2 — meter, orchestration, outcomes

### RT9 — CreativityMeter calibration / new dimension

- **Hypothesis:** Current R (0.65 constraint + 0.35 mono) underweights mid-constraint retention after compact and IV-prep structure; adding `mid_constraint_retention` and/or `iv_structure` dimensions improves selection of paths that win RT2/RT3 without changing rank-order of P4 dual-process.
- **Grounding:** Protect-compact mid_R=1.0 is invisible to hop meter today; B1/B2 mocks uninformative; G1 shows objective choice matters.
- **Design:** Ablate R weights; add optional dimension; re-score saved sweep JSON paths offline (no re-hop if traces stored; else re-run lit conditions). Correlation vs protect mid_R and vs IV F when RT3 lands.
- **Metrics:** Spearman with held-out proxies; stability of condition ranking for P1/P4/P5.
- **Success:** New composite selects RT2-A or RT3-H winners ≥ as often as H; does not flip divergent↔convergent order.
- **Effort:** M · **Offline:** yes · **LLM judge:** optional later for “coherence”
- **Tests:** Metacognition §9; meter-as-monitor

### RT10 — Bridge / Kineteq orchestration routing stub — **DONE / Supported**

- **Status:** **RAN** `p0_rt10_bridge_routing_stub.py`. Gated rubric **0.980** vs random **0.627** (Δ+0.353); illegal-route **0.0**; `kineteq_backend=absent`.
- **Default:** Ship meter-gated routes `validate_iv` / `compact_protect` / `burst_again` (no live Kineteq required for stub).

### RT11 — Outcome-linked eval (LLM-as-judge / checklist) — deferred gate

- **Hypothesis:** High-H multipath paths score higher on task checklists than high-C divergent paths at matched length — validating meter as outcome prior.
- **Grounding:** All current support is meter-internal; report Limitations: no outcome experiment.
- **Design:** Freeze top paths from multipath-H, divergent, convergent, motif; checklist + optional LLM judge; blind condition labels.
- **Metrics:** checklist pass, judge Likert; correlate with H/R.
- **Success:** Spearman(H, checklist) > Spearman(C, checklist); multipath-H ≥ divergent on checklist.
- **Effort:** L · **Offline:** checklist can be automatable; **LLM judge:** yes (later)
- **Tests:** Outcome falsifier for P5 production claim

---

## Mapping to higher-cognition E-queue

| This doc | Overlaps NEXT_EXPERIMENTS_HIGHER_COGNITION |
| --- | --- |
| RT2 | E1 (redesigned) |
| RT6 | E2 + incubation |
| RT4 | E3 |
| RT5 | E4 |
| RT3 | E5 + E7 |
| RT7 | E9 |
| RT10 | E10 |
| RT1 / RT8 / RT9 | New (reasoning-trace focused) |

---

## Schema flags

```json
{
  "theory_ids": ["P13", "P6", "B1"],
  "select_by": "tradeoff_harmonic|R|C|iv_diag",
  "goal_neglect_under_compact": false,
  "orchestration_stage": "burst_explore|compact_protect|iv_estimate|bridge_route",
  "kineteq_backend": "absent"
}
```

---

## Do not run as “improvements” (already rejected)

| Condition | Why |
| --- | --- |
| hop=5 `incubation_alt` / naive `two_phase` | I1/I2 rejected |
| **structured alt-2 incubation (hops 5–8)** | P0 E3 / P17 rejected (0/8); archived |
| head/tail truncate as WM protect control | P6 + E2 pool artifact |
| select-by-C for fidelity traces | G1 R disaster |
| raising `side_hop_prob` to ~0.40 | P8b R tax |

When RT* land, append verdicts to CLAIM_EVIDENCE_TABLE and refresh empirical status in THEORY_* docs.
