# RT2 Protect-Compact → Burst (Coverage-Gated Redesign)

**Stamp:** 20260710T003116Z · PromptDict=True · overall=**mixed**

Config: fixtures=8 seeds=5 hops=5 budget=120 k=7

| condition | C | R | H | mid_R | coverage | path_len | pool | tok |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A_protect_v2 | 0.665 | 0.900 | 0.760 | 0.938 | 1.000 | 4.12 | 4.1 | 59 |
| A_protect_mpH | 0.672 | 0.900 | 0.764 | 0.938 | 1.000 | 4.12 | 4.1 | 59 |
| C_truncate_v2 | 0.710 | 0.878 | 0.781 | 0.500 | 0.884 | 5.75 | 6.6 | 64 |
| C_truncate_mpH | 0.724 | 0.877 | 0.792 | 0.500 | 0.884 | 5.75 | 6.6 | 64 |
| D_raw_v2 | 0.695 | 0.864 | 0.764 | 1.000 | 0.724 | 6.00 | 8.4 | 107 |
| D_raw_mpH | 0.720 | 0.849 | 0.775 | 1.000 | 0.724 | 6.00 | 8.4 | 107 |

## Verdicts
- **RT2_protect_vs_truncate_mpH**: `mixed_strong_mid` — `{"mid_R": {"protect": 0.9375, "truncate": 0.5}, "R": {"protect": 0.9001, "truncate": 0.8766}, "H": {"protect": 0.7645, "truncate": 0.7916}, "coverage": {"protect": 1.0, "truncate": 0.8839}, "path_len": {"protect": 4.125, "truncate": 5.75}, "path_len_matched": false, "coverage_alive_vs_raw": true}`
- **RT2_protect_vs_truncate_v2**: `mixed` — `{"mid_R": {"protect": 0.9375, "truncate": 0.5}, "R": {"protect": 0.9001, "truncate": 0.8779}, "H": {"protect": 0.7602, "truncate": 0.7808}}`
- **RT2_protect_R_near_raw_mpH**: `supported` — `{"protect_R": 0.9001, "raw_R": 0.8487, "delta": 0.0514}`
- **RT2_truncate_not_fake_win**: `ok` — `{"truncate_H": 0.7808, "protect_H": 0.7602, "pools": {"truncate": 6.625, "protect": 4.125}}`

