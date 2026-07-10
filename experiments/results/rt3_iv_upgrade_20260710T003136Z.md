# RT3 Burst-Z vs Random-Z IV Upgrade

**Stamp:** 20260710T003136Z · causaliv=True · autocausal=True
**Overall:** **supported** · fixture wins `3/4`

| condition | F | max_F | weak_rate | edge_q | H | R | n_Z | method |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| burst_high_R | 10.311 | 18.506 | 0.438 | 0.485 | 0.807 | 0.841 | 0.8 | causaliv |
| burst_multipath_H | 10.339 | 18.168 | 0.531 | 0.441 | 0.826 | 0.829 | 1.0 | causaliv |
| convergent | 9.305 | 15.601 | 0.500 | 0.527 | 0.794 | 0.823 | 0.8 | causaliv |
| random_path | 10.189 | 18.163 | 0.562 | 0.495 | 0.738 | 0.754 | 1.0 | causaliv |

## Per-fixture wins (burst vs random)
- `causal_narrative`: win=True (F+10%) F 4.319 vs 3.755 (rel=1.1504)
- `deploy_plan`: win=True (weak) F 17.948 vs 18.577 (rel=0.9661)
- `tool_log_repetitive`: win=True (F+10%) F 21.467 vs 17.124 (rel=1.2536)
- `constraint_stack`: win=False (none) F 1.298 vs 1.298 (rel=1.0)
