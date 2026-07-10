# RT2 Protect-Compact → Burst

**Stamp:** 20260710T001155Z · PromptDict=True

| condition | C | R | H | anchor_R | mid_R | neglect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A_protect_filter | 0.726 | 0.797 | 0.753 | 0.912 | 0.938 | 0.00 |
| B_no_protect_pref | 0.778 | 0.819 | 0.792 | 1.000 | 0.000 | 1.00 |
| C_truncate_matched | 0.725 | 0.830 | 0.766 | 0.963 | 0.812 | 0.50 |
| D_no_compact | 0.721 | 0.797 | 0.751 | 0.912 | 1.000 | 0.00 |

## Verdict
- RT2 partial: A anchor_R − B = -0.088 < 0.10
- RT2 mid_R A=0.938 < 0.95
- RT2 R gate: A R=0.797 ≥ D−0.05 (0.747)
- RT2: truncate control does not clearly fake-win vs A
