# RT2b–RT10 Experiment Batch Report

**Stamp:** 20260710T0047Z · Package: IntentIsolates · Offline, seeded (seed=17)  
**Elite baseline:** multipath k=7 `select_by=H`, protect on, schedule=2, pull≈0.80  
**PromptDict:** available (protect_compact) · **causaliv:** available

---

## Verdict table

| Exp | Verdict | Headline numbers | Notes |
| --- | --- | --- | --- |
| **RT2b** pool-matched protect vs truncate | **Rejected** (joint H gate) | mid_R protect **0.938** ≫ trunc **0.500**; H protect **0.758** < trunc **0.787**; pool/path **matched** (5.1 / 4.88) | Truncate H win is **not** a pool artifact. Protect still wins mid_R; R also favors trunc under match (0.913 > 0.884). |
| **RT3b** path-only IV (no Z boost) | **Rejected** | fixture wins **0/4**; burst F **ties** random on all fixtures (e.g. 4.076=4.076, 20.68=20.68); causaliv real F | Without column boost/damp, Z policies collapse. **RT3 boost was identification-necessary.** |
| **RT4b** adaptive_loosen in trainer | **Mixed** | adapt H **0.777** ≥ elite−0.005 (**0.781**); C **0.709** vs elite **0.704** (not +0.01); fixture_ok **3/4**; trainer neighborhood **baked** (accepted `keep`) | Keep fixed s2 as default; adaptive_loosen remains optional C-recovery. |
| **RT5** mono-gate hops≥8 | **Mixed** | soft mono **0.698** / hard **0.712** > layer_cot **0.656**; H ≈ elite **0.793**; C soft **0.717** > motif **0.677**; strict success **false** | Mono lift vs layer_cot but not vs elite; h8≈h10 (pool exhaustion). |
| **RT8** motif–burst hybrid | **Mixed** | 4 soft winners; best `hybrid_every4_mw0.7` H **0.781** ≥ elite **0.779**, mono **0.825** (elite+0.035), C **0.688** ≥ elite−0.05 | every_4 schedule lifts mono without motif_jump C death (0.57). |
| **RT10** bridge routing stub | **Supported** | gated rubric **0.980** vs random **0.627** (Δ**+0.353**); illegal-route **0.0**; kineteq=`absent` | Ship meter-gated route enum; no live Kineteq required. |

Artifacts: `experiments/results/rt2b_pool_matched_latest.*`, `rt3b_path_only_iv_latest.*`, `rt4b_adaptive_trainer_latest.*`, `rt5_mono_gating_latest.*`, `rt8_motif_burst_hybrid_latest.*`, `rt10_bridge_routing_latest.*`, charts under `experiments/results/charts/`.

---

## Default recommendations (moderate+ only)

| Change | Recommend? | Why |
| --- | --- | --- |
| Keep multipath k=7, `select_by=H`, protect on, schedule=2 | **Yes** | Unchanged elite; RT4b trainer still prefers fixed s2 on objective |
| Prefer `protect_compact` for **mid-constraint** retention | **Yes** | RT2b mid_R 0.938≫0.50 under matched pool — do **not** claim H/R superiority vs truncate |
| Ship meter-gated bridge routes (`validate_iv` / `compact_protect` / `burst_again`) | **Yes** | RT10 supported; illegal IV rate 0 |
| Optional `adaptive_loosen_on_calm` when C matters | **Yes (optional)** | RT4 supported; RT4b mixed but H within 0.005 and C↑ — not default over fixed s2 |
| Optional motif schedule `every_4` for mono lift | **Yes (optional, soft)** | RT8 mixed/soft: mono↑ with H≥elite and C near elite |
| Path-only IV without Z boost as production claim | **No** | RT3b rejected — boost needed for policy differentiation |
| Soft/hard mono-gate as default at hops≥8 | **No** | RT5 mixed — does not beat elite mono/H jointly |
| Truncate as fair WM control for H ranking | **No** | Even pool-matched, truncate wins H; use mid_R + coverage gates |

---

## What’s still open

1. **RT9** — Meter dimensions (`mid_constraint_retention`, `iv_structure`) so H sees protect mid_R (RT2b showed H and mid_R disagree under match).
2. **RT3 identification** — Path-only Z insufficient; need structural Z proposal that doesn’t rely on column boost, or accept boost as transparent proxy and document.
3. **RT5 depth** — h8≈h10 suggests span-pool exhaustion; need larger fixtures or revisit budgets before claiming planning-depth gains.
4. **RT8 strict** — Soft winners only; re-sweep with hops≥8 and weight grid for strict mono≥elite+0.05.
5. **RT11** — Outcome/checklist link still deferred.
6. **Live Kineteq** — RT10 stub only; MCP/module backend untested.

---

## Scripts

```text
python experiments/p0_rt2b_pool_matched.py
python experiments/p0_rt3b_path_only_iv.py
python experiments/p0_rt4b_adaptive_trainer.py
python experiments/p0_rt5_mono_gating.py
python experiments/p0_rt8_motif_burst_hybrid.py
python experiments/p0_rt10_bridge_routing_stub.py
```

Trainer bake-in: `Policy.adaptive_policy` / `thrash_threshold` + epoch-6 neighborhood in `iterative_reasoning_training.py`.
