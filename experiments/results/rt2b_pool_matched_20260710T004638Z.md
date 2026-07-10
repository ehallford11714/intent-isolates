# RT2b Pool-Matched Protect vs Truncate

**Stamp:** 20260710T004638Z · PromptDict=True · overall=**rejected**

Config: fixtures=8 seeds=5 hops=5 budget=120 k=7

| condition | C | R | H | mid_R | coverage | path_len | pool |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| protect_mpH_matched | 0.667 | 0.884 | 0.758 | 0.938 | 0.969 | 4.88 | 5.1 |
| truncate_mpH_matched | 0.696 | 0.913 | 0.787 | 0.500 | 0.969 | 4.88 | 5.1 |
| protect_v2_matched | 0.656 | 0.887 | 0.751 | 0.938 | 0.969 | 4.88 | 5.1 |
| truncate_v2_matched | 0.696 | 0.869 | 0.768 | 0.500 | 0.969 | 4.88 | 5.1 |
| raw_mpH | 0.700 | 0.895 | 0.783 | 1.000 | 0.724 | 6.00 | 8.4 |

## Verdicts
- **RT2b_pool_matched_protect_vs_truncate_mpH**: `rejected` — `{"mid_R": {"protect": 0.9375, "truncate": 0.5}, "R": {"protect": 0.8842, "truncate": 0.9128}, "H": {"protect": 0.7581, "truncate": 0.7873}, "pool_n": {"protect": 5.125, "truncate": 5.125}, "path_len": {"protect": 4.875, "truncate": 4.875}, "coverage": {"protect": 0.9688, "truncate": 0.9688}, "pool_matched": true, "path_len_matched": true, "coverage_matched": true, "mid_win": true, "h_ok": false}`
- **RT2b_protect_R_vs_raw**: `supported` — `{"protect_R": 0.8842, "raw_R": 0.8952}`
