# RT2 Protect-Compact → Burst

**Stamp:** 20260710T001003Z · PromptDict=True

| condition | C | R | H | anchor_R | mid_R | neglect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A_protect_filter | 0.721 | 0.806 | 0.754 | 0.917 | 0.938 | 0.00 |
| B_no_protect_pref | 0.778 | 0.807 | 0.785 | 1.000 | 0.000 | 1.00 |
| C_truncate_matched | 0.720 | 0.836 | 0.767 | 0.963 | 0.812 | 0.50 |
| D_no_compact | 0.718 | 0.812 | 0.756 | 0.917 | 1.000 | 0.00 |

## Verdict
- RT2 partial: A anchor_R − B = -0.083 < 0.10
- RT2 mid_R A=0.938 < 0.95
- RT2 R gate: A R=0.806 ≥ D−0.05 (0.762)
- RT2: truncate control does not clearly fake-win vs A
