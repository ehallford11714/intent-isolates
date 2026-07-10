# RT4 Adaptive Conflict Schedule

**Stamp:** 20260710T003308Z · overall=**supported** · best_adaptive=`adaptive_loosen_0.55`

| condition | C | R | H | anchor_R | mono | thrash | trigger |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| elite_fixed_s2_mpH | 0.692 | 0.897 | 0.778 | 0.954 | 0.790 | 0.895 | 0.00 |
| stock_v2_s3_mpH | 0.721 | 0.850 | 0.776 | 0.923 | 0.715 | 0.980 | 0.00 |
| adaptive_thrash_0.55 | 0.726 | 0.841 | 0.775 | 0.893 | 0.745 | 0.950 | 1.00 |
| adaptive_thrash_0.70 | 0.726 | 0.841 | 0.775 | 0.893 | 0.745 | 0.950 | 1.00 |
| adaptive_thrash_0.40 | 0.726 | 0.841 | 0.775 | 0.893 | 0.745 | 0.950 | 1.00 |
| adaptive_loosen_0.55 | 0.704 | 0.874 | 0.775 | 0.933 | 0.765 | 0.945 | 0.07 |
| adaptive_loosen_0.70 | 0.704 | 0.874 | 0.775 | 0.933 | 0.765 | 0.945 | 0.07 |
| hybrid_interrupt | 0.726 | 0.829 | 0.769 | 0.903 | 0.690 | 1.000 | 0.00 |
| fixed_s2_single | 0.697 | 0.861 | 0.763 | 0.954 | 0.690 | 0.905 | 0.00 |
| stock_v2_s3_single | 0.739 | 0.778 | 0.752 | 0.866 | 0.615 | 0.960 | 0.00 |

## Verdicts
- **RT4_adaptive_vs_elite_s2**: `supported` — `{"best_adaptive": "adaptive_loosen_0.55", "fixture_ok": "7/8", "adapt": {"C": 0.7039, "R": 0.8744, "H": 0.7754}, "elite": {"C": 0.6924, "R": 0.8967, "H": 0.7781}, "stock": {"C": 0.7214, "R": 0.8504, "H": 0.7765}, "h_ok": true, "c_recover_vs_stock": true, "c_vs_elite": true, "r_keep": true}`
- **RT4_hybrid_interrupt**: `supported` — `{"hybrid": {"C": 0.7261, "R": 0.8287, "H": 0.7689}, "elite": {"C": 0.6924, "R": 0.8967, "H": 0.7781}}`
- **RT4_elite_beats_stock_H**: `supported` — `{"elite_H": 0.7781, "stock_H": 0.7765, "elite_C": 0.6924, "stock_C": 0.7214}`

## Per-fixture adaptive vs elite
- `brand_voice`: ok=True H 0.736 vs elite 0.736; C 0.609 (stock 0.657)
- `causal_narrative`: ok=True H 0.816 vs elite 0.816; C 0.727 (stock 0.711)
- `constraint_stack`: ok=True H 0.718 vs elite 0.726; C 0.723 (stock 0.728)
- `deploy_plan`: ok=True H 0.838 vs elite 0.838; C 0.784 (stock 0.815)
- `product_metaphor`: ok=True H 0.846 vs elite 0.846; C 0.833 (stock 0.838)
- `research_creative`: ok=False H 0.713 vs elite 0.726; C 0.643 (stock 0.630)
- `story_twist`: ok=True H 0.804 vs elite 0.804; C 0.709 (stock 0.718)
- `tool_log_repetitive`: ok=True H 0.732 vs elite 0.732; C 0.603 (stock 0.676)
