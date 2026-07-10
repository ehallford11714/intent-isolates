# RT4b Adaptive Loosen in Trainer / Eval

**Stamp:** 20260710T004710Z · overall=**mixed** · fixture_ok=`3/4`

| condition | C | R | H | mono | mid_R |
| --- | ---: | ---: | ---: | ---: | ---: |
| elite_fixed_s2 | 0.704 | 0.887 | 0.781 | 0.800 | 1.000 |
| adaptive_loosen_0.55 | 0.709 | 0.869 | 0.777 | 0.750 | 1.000 |
| adaptive_loosen_0.40 | 0.704 | 0.887 | 0.781 | 0.800 | 1.000 |
| adaptive_loosen_0.70 | 0.709 | 0.869 | 0.777 | 0.750 | 1.000 |
| adaptive_tighten_0.55 | 0.725 | 0.842 | 0.777 | 0.733 | 1.000 |

## Verdicts
- **RT4b_adaptive_loosen_vs_elite_s2**: `mixed` — `{"fixture_ok": "3/4", "adapt": {"C": 0.7093, "R": 0.8692, "H": 0.7774}, "elite": {"C": 0.7041, "R": 0.8867, "H": 0.7806}, "h_ok": true, "c_lift": false, "r_keep": true}`
- **RT4b_trainer_bake_in**: `supported` — `{"probe": {"accepted": "keep", "action": "RT4/RT4b conflict schedule + adaptive_loosen: accept keep", "next_policy": {"novelty_weight": 1.1, "anchor_pull": 0.8, "layer_bias": 0.47, "motif_weight": 0.45, "anchor_schedule": 2, "side_hop_prob": 0.18, "multipath": true, "k": 7, "select_by": "H", "protect_compact": true, "soft_mono_gate": false, "adaptive_policy": null, "thrash_threshold": 0.55}, "n_candidates": 14, "adaptive_in_neighborhood": true}}`

**Trainer epoch-6 probe:** accepted=`keep` · adaptive_in_neighborhood=True
