# Next Experiments: Reasoning-Trace Quality

**Status:** prioritized queue grounded in 2026-07-09 offline results  
**Package:** `intentisolates` ≥ 0.4.1  
**Evidence:** [COMPILED_EXPERIMENTATION_20260709.md](../experiments/results/COMPILED_EXPERIMENTATION_20260709.md) · [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md) · [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md)  
**Theory:** [THEORY_CREATIVE_BURST_REASONING.md](THEORY_CREATIVE_BURST_REASONING.md) · [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md)  
**Related queue:** [NEXT_EXPERIMENTS_HIGHER_COGNITION.md](NEXT_EXPERIMENTS_HIGHER_COGNITION.md) (cognition + bridge E1–E10; this doc focuses on **reasoning-trace R / layer_mono / mid_constraint / IV quality**)

**Stance:** Offline computational analogs. Prefer automatable meters first; LLM-as-judge only where noted.

---

## Result anchors (cite these)

| Finding | Numbers | Source |
| --- | --- | --- |
| Multipath H-optimal | lit `multipath_tot` **H=0.768**; sweep `multipath_k7_H` **0.774**, `k5_H` **0.769**, `k3_H` **0.768** | lit_burst / theory_corpus_sweep |
| Select-by-H ≫ select-by-C on R | `mp_k5_H` R=**0.836** vs `mp_k5_C` R=**0.734** (Δ=+0.102, 8/8) — claim **G1** | CLAIM_EVIDENCE_TABLE |
| Select-by-R lifts R, costs H | `mp_k5_R` R=0.852 / H=0.760 vs `mp_k5_H` R=0.836 / H=0.769 | sweep |
| v2 R-lift vs v1 | lit R **0.820>0.721**; sweep **0.796>0.754** (L2, 5/8) | lit + claim L2 |
| Motif fidelity / creativity tax | lit motif `anchor_R=0.950`, `layer_mono=0.967`, C=**0.590**; sweep motif R=0.900 C=0.566 vs v2 C=0.728 (L1a/b) | lit + L1 |
| Dual-process + precision | div C=0.761 > conv 0.657; `precision_high` R=0.891 vs low 0.740 (PP1/PP2) | P4 / PP* |
| Conflict schedule helps H | `conflict_schedule_2` H=**0.763** ≥ v2 0.754 (P7, 5/8) | sweep |
| Incubation / two-phase fail at hop=5 | `incubation_alt` H=0.691 < div 0.734 (I1); `two_phase` H=0.728 < v2 0.754 (I2) | rejected |
| WM sim artifact | `wm_truncate_drop` H=0.778 / anchor_R=1.0 inflated; protect mid_R settled elsewhere | P6 rejected |
| Protect-compact mid-constraints | PromptDict `protect_compact` **mid_R=1.000** vs truncate **0.200**; gold_R=1.0 | reasoning_compaction_20260709T234933Z |
| Causal IV weak | B1/B2 mock F tied / zero overlap — inconclusive for identification | claim table |

**Production do-not-touch from falsifiers:** do not ship naive `incubation_alt` / hop=5 `two_phase`; do not treat head/tail truncate as a fair WM control; keep `side_hop_prob≈0.18` (insight high R-tax Δ≈−0.13 vs convergent).

---

## Priority summary

| Priority | IDs | Goal |
| --- | --- | --- |
| **P0** | RT1–RT4 | Raise R / mid-constraint / IV-diagnostic path selection without wrecking C |
| **P1** | RT5–RT8 | Planning depth, redesigned schedules, analogical transfer |
| **P2** | RT9–RT11 | Meter calibration, Bridge/Kineteq stub, LLM-judge outcome link |

Run order: **RT1 → RT3 → RT2 → RT4 → RT5 → RT6 → RT7 → RT8 → RT9 → RT10 → RT11**.

---

## P0 — ship next

### RT1 — Multipath value-function bakeoff (H vs R vs IV-diagnosticity)

- **Hypothesis:** Selecting by \(H\) maximizes harmonic quality; selecting by \(R\) maximizes fidelity but drops \(H\); an IV-diagnosticity score (early-layer/protect coverage + layer_mono) may beat pure \(R\) on causal-prep paths without C collapse of select-by-C.
- **Grounding:** G1 ΔR=+0.102 (H vs C); `mp_k5_R` R=0.852 > `mp_k5_H` 0.836 but H 0.760 < 0.769; B1/B2 still weak — need a better selection objective before spending real IV.
- **Design:** Same fixtures/seeds as sweep (8×5, hops=5, k∈{3,5,7}). Conditions: `select_by ∈ {tradeoff_harmonic, R, C, iv_diag}` where `iv_diag = 0.5·anchor_R + 0.3·layer_mono + 0.2·early_layer_frac`. Freeze hop policy to v2.
- **Metrics:** C, R, H, `anchor_R`, `layer_mono`; optional post-hoc mock/real first-stage F on winner only.
- **Success:** (a) `iv_diag` H ≥ `mp_k5_H` − 0.01 and R ≥ `mp_k5_H` R; OR (b) clearly maps Pareto: H-max / R-max / IV-prep fronts. Select-by-C must remain worst on R (replicate G1).
- **Effort:** S · **Offline:** yes · **LLM judge:** no
- **Tests:** P5 refinement; G1; Bridge B4 prior; new **P13** (value-fn family)

### RT2 — Protect-compact → burst coupling (goal-neglect redo)

- **Hypothesis:** Real PromptDict `protect_compact` hot-set + `filter_spans_for_burst` preserves mid-constraints through burst; dropping protect under identical compact budget causes goal neglect (↓R / ↓`constraint_fidelity`).
- **Grounding:** Compaction mid_R protect=**1.0** vs truncate=**0.2**; sweep P6 **rejected** because `wm_truncate_drop` shrunk pool → fake `anchor_R=1.0`. Need non-artifact control.
- **Design:** Per fixture: (A) protect_compact → filter protect → v2; (B) protect_compact → filter **without** protect preference; (C) lossy_truncate matched `tok_after` → v2; (D) no-compact v2 baseline. Flag `goal_neglect_under_compact` if protect goals absent from path.
- **Metrics:** mid_constraint_R (pre-burst), post-burst R / `anchor_R` / H, neglect flag rate.
- **Success:** A `anchor_R` ≥ B by ≥0.10; A mid_R ≥ 0.95; A R ≥ D − 0.05; C must not fake-win via pool shrinkage (require path length / coverage matched ±10%).
- **Effort:** S–M · **Offline:** yes · **LLM judge:** no
- **Tests:** P6 redesign; WM §2; compaction bridge

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

### RT6 — Incubation / intermittent diverge–converge (longer horizon)

- **Hypothesis:** Rejected I1/I2 were **horizon artifacts** at hops=5; at hops≥10 with block sizes (2d/2c) or (3d/1c), intermittent schedules can recover H ≥ v2 without C collapse of pure convergent.
- **Grounding:** `incubation_alt` H=0.691 (1/8 wins); `two_phase` H=0.728 (1/8); dual-process still strong when modes run alone (P4).
- **Design:** hops ∈ {10,12}; blocks ∈ {alt-2, alt-3/1, mid-flip, v2-fixed, divergent-fixed}. Match compute: intermittent single-seed vs multipath k=3 at hop=5 (compute-normalized appendix).
- **Metrics:** H, C, R, entropy trajectory, switch cost.
- **Success:** Best intermittent H ≥ v2_same_hops; ≥5/8 fixture wins; if still fails → **archive** incubation as knobs (document falsifier).
- **Effort:** M · **Offline:** yes · **LLM judge:** no
- **Tests:** I1/I2 redesign; dual-process schedule

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
| head/tail truncate as WM protect control | P6 artifact |
| select-by-C for fidelity traces | G1 R disaster |
| raising `side_hop_prob` to ~0.40 | P8b R tax |

When RT* land, append verdicts to CLAIM_EVIDENCE_TABLE and refresh empirical status in THEORY_* docs.
