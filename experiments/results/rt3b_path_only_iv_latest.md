# RT3b Path-Only IV (No Z Boost)

**Stamp:** 20260710T004800Z · causaliv=True · autocausal=True
**Overall:** **rejected** · fixture wins `0/4` · boost_used=False

**Method note:** path-only hard mask (no Z boost). Burst does not clearly win without boost; RT3 boost may have been necessary.

| condition | F | max_F | weak_rate | edge_q | H | R | n_Z | method |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| burst_high_R | 11.812 | 20.242 | 0.469 | 0.412 | 0.818 | 0.885 | 0.5 | causaliv |
| burst_multipath_H | 11.187 | 18.421 | 0.500 | 0.456 | 0.837 | 0.897 | 0.8 | causaliv |
| convergent | 11.812 | 20.242 | 0.469 | 0.412 | 0.794 | 0.823 | 0.2 | causaliv |
| random_path | 12.009 | 20.242 | 0.469 | 0.494 | 0.725 | 0.725 | 1.2 | causaliv |

## Per-fixture wins (burst vs random)
- `causal_narrative`: win=False (none) F 3.288 vs 4.076 (rel=0.8066)
- `deploy_plan`: win=False (none) F 20.683 vs 20.683 (rel=1.0)
- `tool_log_repetitive`: win=False (none) F 21.977 vs 21.977 (rel=1.0)
- `constraint_stack`: win=False (none) F 1.298 vs 1.298 (rel=1.0)
