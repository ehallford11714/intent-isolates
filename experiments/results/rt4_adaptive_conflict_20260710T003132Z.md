# RT4 Adaptive Conflict Schedule

**Stamp:** 20260710T003132Z · overall=**rejected** · best_adaptive=`adaptive_thrash_0.55`

| condition | C | R | H | anchor_R | mono | thrash | trigger |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| elite_fixed_s2_mpH | 0.694 | 0.895 | 0.779 | 0.949 | 0.795 | 0.910 | 0.00 |
| stock_v2_s3_mpH | 0.717 | 0.854 | 0.776 | 0.923 | 0.725 | 0.985 | 0.00 |
| adaptive_thrash_0.55 | 0.706 | 0.724 | 0.713 | 0.765 | 0.648 | 1.000 | 1.00 |
| adaptive_thrash_0.70 | 0.706 | 0.724 | 0.713 | 0.765 | 0.648 | 1.000 | 1.00 |
| adaptive_thrash_0.40 | 0.706 | 0.724 | 0.713 | 0.765 | 0.648 | 1.000 | 1.00 |
| hybrid_interrupt | 0.653 | 0.803 | 0.716 | 0.871 | 0.677 | 0.892 | 0.00 |
| fixed_s2_single | 0.690 | 0.872 | 0.764 | 0.965 | 0.700 | 0.895 | 0.00 |
| stock_v2_s3_single | 0.719 | 0.813 | 0.756 | 0.906 | 0.640 | 0.950 | 0.00 |

## Verdicts
- **RT4_adaptive_vs_elite_s2**: `rejected` — `{"best_adaptive": "adaptive_thrash_0.55", "fixture_ok": "0/8", "adapt": {"C": 0.7059, "R": 0.7237, "H": 0.7127}, "elite": {"C": 0.6943, "R": 0.8952, "H": 0.7788}, "stock": {"C": 0.7174, "R": 0.8539, "H": 0.7757}, "h_ok": false, "c_recover_vs_stock": true, "c_vs_elite": true, "r_keep": false}`
- **RT4_hybrid_interrupt**: `rejected` — `{"hybrid": {"C": 0.6527, "R": 0.8031, "H": 0.7163}, "elite": {"C": 0.6943, "R": 0.8952, "H": 0.7788}}`
- **RT4_elite_beats_stock_H**: `supported` — `{"elite_H": 0.7788, "stock_H": 0.7757, "elite_C": 0.6943, "stock_C": 0.7174}`

## Per-fixture adaptive vs elite
- `brand_voice`: ok=False H 0.652 vs elite 0.735; C 0.700 (stock 0.633)
- `causal_narrative`: ok=False H 0.727 vs elite 0.817; C 0.733 (stock 0.716)
- `constraint_stack`: ok=False H 0.679 vs elite 0.726; C 0.664 (stock 0.732)
- `deploy_plan`: ok=False H 0.808 vs elite 0.838; C 0.750 (stock 0.810)
- `product_metaphor`: ok=False H 0.803 vs elite 0.851; C 0.755 (stock 0.833)
- `research_creative`: ok=False H 0.625 vs elite 0.726; C 0.621 (stock 0.630)
- `story_twist`: ok=False H 0.701 vs elite 0.807; C 0.734 (stock 0.691)
- `tool_log_repetitive`: ok=False H 0.705 vs elite 0.732; C 0.690 (stock 0.693)
