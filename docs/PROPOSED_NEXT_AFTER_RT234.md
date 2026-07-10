# Proposed Next Experiments (after RT2/RT3/RT4 redesign runs)

**Stamp:** 20260710T003308Z (RT4) · batch follow-up **20260710T0047Z** — see [RT2B_RT10_EXPERIMENT_BATCH_REPORT.md](RT2B_RT10_EXPERIMENT_BATCH_REPORT.md)  
**Stance:** Offline, seeded, reproducible. Ranked from **these** satellite numbers, not prior loop alone.

### Batch follow-up verdicts (RT2b / RT3b / RT4b / RT5 / RT8 / RT10)

| ID | Verdict | Evidence |
| --- | --- | --- |
| **RT2b** | **Rejected** (H) | mid_R 0.938≫0.500; H 0.758<0.787; pool matched — trunc H not artifact |
| **RT3b** | **Rejected** | path-only 0/4; boost necessary for Z differentiation |
| **RT4b** | **Mixed** | H 0.777≈0.781; C 0.709 vs 0.704; trainer bake-in; keep fixed s2 |
| **RT5** | **Mixed** | mono > layer_cot; H≈elite; strict fail; h8≈h10 |
| **RT8** | **Mixed** | every_4 soft win: H≥elite, mono 0.825, C near elite |
| **RT10** | **Supported** | gated 0.980 vs random 0.627; illegal=0 |

---

## RT2 / RT3 / RT4 verdicts (evidence)

| ID | Verdict | Evidence |
| --- | --- | --- |
| **RT2** coverage-gated protect→burst | **Mixed** (strong mid_R; H not won) | Protect mid_R **0.938** ≫ truncate **0.500**; protect R **0.900** > truncate **0.877** and > raw **0.849**; coverage alive (1.0). Truncate still wins H (**0.792** vs **0.765**) with larger pool/path_len — not a pure mid-drop fake-win (`truncate_not_fake_win=ok`), but path_len not matched (±10% fail). |
| **RT3** burst-Z vs random-Z (causaliv) | **Supported** | Fixture wins **3/4**; `causaliv` real F. Burst-H mean F **10.34** > random **10.19**; high-R F **10.31**. Wins: causal_narrative (+15% F), tool_log (+25% F), deploy_plan (weak-rate). Tie/loss: constraint_stack. |
| **RT4** adaptive schedule | **Supported** | Best=`adaptive_loosen_0.55`: H **0.775** ≥ elite−0.005 (**0.778**), C **0.704** > elite **0.692** and ≥ stock−0.03; R kept within 0.03 of elite; **7/8** fixtures. Tighten-on-thrash recovers C but drops R vs elite. Hybrid interrupt: C↑ but H/R below elite (secondary). |

Artifacts: `experiments/results/rt2_coverage_gated_latest.*`, `rt3_iv_upgrade_latest.*`, `rt4_adaptive_conflict_latest.*`, charts under `experiments/results/charts/`.

---

## Default changes (moderate+ support only)

| Change | Recommend? | Why |
| --- | --- | --- |
| Keep multipath k=7, `select_by=H`, protect on | **Yes** (unchanged) | Elite + RT2 R/mid_R; RT4 elite still H-best fixed policy |
| Prefer `protect_compact` before burst when mid-constraints matter | **Yes** | RT2/RT2b mid_R; do **not** claim H/R superiority vs truncate (RT2b rejected H) |
| Fixed `schedule=2` / pull≈0.80 as fidelity default | **Yes** | RT4b trainer still prefers fixed s2 on objective |
| Ship `adaptive_loosen_on_calm` as optional default | **Yes (optional)** | RT4 supported; RT4b mixed but H within 0.005 |
| Prefer burst/high-R paths for IV Z proposal | **Yes (prep)** with boost proxy | RT3 supported; **RT3b** shows path-only insufficient |
| Ship meter-gated bridge routes | **Yes** | RT10 supported |
| Optional motif `every_4` schedule | **Yes (optional, soft)** | RT8 mixed |
| Replace truncate as WM control for H | **Yes (docs)** | Even pool-matched, trunc can win H — gate on mid_R |

**Do not** change production select_by away from H; **do not** make tighten-on-thrash the default (always triggers, R tax).

---

## Ranked next experiments (5–8)

### 1. RT2b — Pool-matched protect vs truncate (P0)

- **Why now:** RT2 mixed solely because truncate H > protect H with unmatched path_len/pool; mid_R/R already favor protect.
- **Design:** Force identical `pool_n` / hop budget after compact (pad truncate pool with cold refs or subsample protect filler); re-score mid_R, R, H, coverage.
- **Success:** Protect mid_R ≥ truncate+0.15 **and** H ≥ truncate−0.01 under matched coverage ±10%.
- **Effort:** S

### 2. RT9 — Meter: add mid_constraint_retention / iv_structure (P0)

- **Why now:** RT2 mid_R invisible to H (truncate can win H); RT3 F correlates with path policy — meter should see both.
- **Design:** Offline re-score saved paths; ablate R weights; check P4 dual-process order stable.
- **Success:** New composite picks protect_mpH over truncate_mpH ≥ as often as H; Spearman with RT3 F > current R.
- **Effort:** M

### 3. RT4b — Adaptive loosen bake into iterative trainer (P0)

- **Why now:** RT4 supported; loop still locks fixed schedule=2.
- **Design:** Add `adaptive_loosen` neighborhood in epochs; compare to elite fixed s2 on same 4×3 grid.
- **Success:** Objective H≥elite−0.005 with C≥elite+0.01 on ≥2/3 seeds mean.
- **Effort:** S

### 4. RT3b — LayerCausalSuite Z from path spans only (no column boost) (P1)

- **Why now:** RT3 used transparent Z-column restriction/boost so policies differ; need stricter identification.
- **Design:** Build feature frame from **only** path-visited isolates as Z candidates; no damp/boost; report F + weak rate.
- **Success:** Burst still beats random on ≥ majority fixtures **or** document that boost was necessary (method note).
- **Effort:** M

### 5. RT5 — Soft mono-gating at hops≥8 (P1)

- **Why now:** Loop mono already 0.80 at hops=5; RT4/RT2 didn’t reopen depth.
- **Design:** hops∈{8,10}; mono_gated / hard_plan vs elite multipath-H.
- **Success:** mono ≥ layer_cot+0.05 and H ≥ elite_same_hops−0.02; C ≥ motif+0.08.
- **Effort:** M

### 6. RT8 — Motif–burst hybrid schedule (P1)

- **Why now:** Elite keeps motif_weight=0.45; RT4 showed schedule adaptation helps C — motif schedule may help mono without motif_jump C death.
- **Design:** `motif_schedule ∈ {off, every_2, every_3}` × weight {0.45,0.7} vs motif_jump / elite.
- **Success:** Some hybrid H≥elite and mono≥elite+0.05 and C≥elite−0.05.
- **Effort:** S

### 7. RT6 — Long-horizon incubation redo (P1, after RT2b)

- **Why now:** Prior I1/I2 rejected at hops=5; RT4 adaptive is a related schedule idea that worked — incubation may need hops≥10.
- **Design:** hops∈{10,12}; alt blocks; compute-normalize vs multipath k=3@5.
- **Success:** Best intermittent H≥v2_same_hops on ≥5/8; else archive.
- **Effort:** M

### 8. RT11 checklist / outcome link (P2, deferred)

- **Why now:** Still meter-internal; RT3 F is first external-ish signal.
- **Design:** Freeze elite / adaptive_loosen / protect / truncate paths; automatable checklist first.
- **Success:** Spearman(H, checklist) > Spearman(C, checklist).
- **Effort:** L

---

## Mapping

| New ID | Parent queue |
| --- | --- |
| RT2b | RT2 redesign follow-up |
| RT4b | RT4 → trainer |
| RT3b | RT3 / B1 rigor |
| RT9 | Meter (NEXT RT9) |
| RT5 / RT8 / RT6 / RT11 | Existing NEXT doc |

Run order suggested: **RT2b → RT4b → RT9 → RT3b → RT5 → RT8 → RT6 → RT11**.
