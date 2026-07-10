# Next Experiments: Reasoning-Trace Quality

**Status:** P0 E1–E3 **ran** (`p0_followup_20260710T002719Z`) · RT1–RT5 also progressed via 10-epoch loop (`20260710T001218Z`)  
**Package:** `intentisolates` ≥ 0.4.1  
**Evidence:** **[P0_FOLLOWUP_EXPERIMENT_RESULTS.md](P0_FOLLOWUP_EXPERIMENT_RESULTS.md)** · [p0_followup_latest.md](../experiments/results/p0_followup_latest.md) · [COMPILED_EXPERIMENTATION_20260709.md](../experiments/results/COMPILED_EXPERIMENTATION_20260709.md) · [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) · [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md) · [ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md](ITERATIVE_REASONING_TRACE_TRAINING_REPORT.md) · [EPOCH_TRAJECTORY.md](../experiments/results/iterative_epochs/EPOCH_TRAJECTORY.md)  
**Theory:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md)  
**Related queue:** [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md) (cognition + bridge E1–E10; this doc focuses on **reasoning-trace R / layer_mono / mid_constraint / IV quality**)

**Stance:** Offline computational analogs. Prefer automatable meters first; LLM-as-judge only where noted.

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
| Causal IV weak | B1/B2 mock F tied — inconclusive | claim table |

**Production do-not-touch from falsifiers:** do not ship naive `incubation_alt` / hop=5 `two_phase` / **structured alt-2 incubation**; do not treat head/tail truncate as a fair WM control; keep `side_hop_prob≈0.18`.

---

## Priority summary

| Priority | IDs | Goal | Status |
| --- | --- | --- | --- |
| **P0** | RT1 / E1 | Multipath value-fn | **DONE** |
| **P0** | RT2 / E2 | Protect→burst | **DONE** (trunc H artifact) |
| **P0** | RT6 / E3 | Structured incubation | **ARCHIVED** |
| **P0** | RT3–RT4 | IV F + conflict adaptive | **NEXT** (RT4 in-loop partial) |
| **P1** | RT5, RT7–RT8 | Planning / transfer / motif hybrid | queued |
| **P2** | RT9–RT11 | Meter / Bridge / outcome | queued |

Run order remaining: **RT3 → RT4 (confirm out-of-loop) → RT5 → RT7 → RT8 → RT9 → RT10 → RT11**.

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

### RT3 — Burst-proposed instruments → weak-IV F (replace mock tie)

- **Hypothesis:** Paths from multipath select-by-H (or RT1 `iv_diag`) propose early-layer Z candidates with higher first-stage F and lower weak-IV rate than random Z or select-by-C winners.
- **Grounding:** B1 currently F(burst)=F(random)=4.2025 (weak tie); multipath R ≥ random (B4 strong, ΔR=+0.096). Structural prior is ready; statistical IV is not.
- **Design:** Causal narrative fixtures (+ LayerCausalSuite). Z = early-layer / tool/instrument typologies on path; X mid; Y outcome. Compare: multipath-H Z, multipath-C Z, random Z, convergent Z. Soft `causaliv` when present; mock_iv only as CI smoke with **non-identical** assignment.
- **Metrics:** first-stage F, weak-IV rate, |\(\beta_{IV}\)| SE; path C/R/H for correlation.
- **Success:** Burst-H mean F > random by ≥10% relative **or** weak-IV rate ≤ random − 5 pp across ≥3 fixtures; reject if still tied under non-degenerate assignment.
- **Effort:** M · **Offline:** mostly · **LLM judge:** no
- **Tests:** B1, P11, P10

### RT4 — Conflict-adaptive + schedule fine grid (without killing C)

- **Hypothesis:** Adaptive protect recruitment (high typology thrash / low recent anchor_need) matches or beats fixed `conflict_schedule_2` on H while recovering C lost by always-on schedule=2 (C=0.688 vs v2 0.728).
- **Grounding:** P7 supported (H 0.763 ≥ v2 0.754) but C drop ~0.04; precision_high also raises R with C cost.
- **Design:** Conditions: v2 schedule=3; fixed=2; adaptive threshold grid; hybrid schedule=3 with one conflict interrupt. Same 8 fixtures × 5 seeds.
- **Metrics:** H, C, R, `anchor_R`, forced-visit count.
- **Success:** Adaptive H ≥ schedule_2 − 0.005 and C ≥ v2 − 0.03 on ≥6/8 fixtures.
- **Effort:** S–M · **Offline:** yes · **LLM judge:** no
- **Tests:** P7 refinement; Botvinick analog

---

## P1 — depth & schedules

### RT5 — Planning-depth / layer_monotonicity intervention

- **Hypothesis:** Soft layer-order constraints (goal/constraint before action/outcome) raise `layer_mono` toward motif specialist levels without motif’s C collapse (motif mono≈0.98 / C≈0.57; layer_cot mono lit 0.700 / C 0.667).
- **Grounding:** P3 strong (layer_cot mono ≥ divergent 8/8); PL1 H≥divergent; motif wins mono but L1b C≪v2.
- **Design:** Hop budgets {5,8,10}. Conditions: divergent, layer_cot, v2, multipath-H, **mono_gated** (reject hops that violate Δℓ≥−1 more than once), **hard_plan** (must visit ℓ≤1 before ℓ≥3).
- **Metrics:** `layer_mono`, plan-success (layer order check), H, C.
- **Success:** mono_gated or hard_plan mono ≥ layer_cot + 0.05 and H ≥ v2 − 0.02; C ≥ motif_jump + 0.08.
- **Effort:** M · **Offline:** yes · **LLM judge:** optional checklist later
- **Tests:** P3 / Soar ToL analog; new **P14**

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

### RT8 — Motif–burst hybrid schedule (fidelity without C death)

- **Hypothesis:** Periodic motif pulls (every k hops) lift R/`layer_mono` vs v2 while keeping C within 0.05 of v2 — between motif specialist and burst.
- **Grounding:** Motif R=0.900 C=0.566 vs v2 R=0.796 C=0.728; v2 already has motif_weight=0.45 — vary **schedule** not just weight.
- **Design:** `motif_schedule ∈ {off, every_2, every_3, every_4}` × weight ∈ {0.45, 0.7}; vs pure motif_jump / v2 / convergent.
- **Metrics:** C, R, H, `layer_mono`, `anchor_R`.
- **Success:** Some hybrid with H ≥ v2 and `layer_mono` ≥ v2 + 0.05 and C ≥ v2 − 0.05.
- **Effort:** S · **Offline:** yes · **LLM judge:** no
- **Tests:** L1 hybrid; P1 refinement

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

### RT10 — Bridge / Kineteq orchestration routing stub

- **Hypothesis:** Meter-gated route from high-H / high-R paths chooses more coherent next tools (`iv_validate` only if R≥τ; else remine/search) than random or select-by-C.
- **Grounding:** B5 untested; B4 structural prior strong; kineteq live MCP absent — dry-run / rubric only.
- **Design:** Offline enum rubric over winner paths from lit/sweep; optional CausalBridge dry_run if present; record `kineteq_backend=absent|pivot_fallback`.
- **Metrics:** rubric score, illegal-route rate (IV when R low).
- **Success:** Gated rubric ≥ random + 0.2; illegal-route rate = 0.
- **Effort:** M (stub) · **Offline:** yes · **LLM judge:** no
- **Tests:** B5 / P12

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
