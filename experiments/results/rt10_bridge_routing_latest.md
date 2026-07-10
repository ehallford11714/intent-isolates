# RT10 Bridge / Kineteq Routing Stub

**Stamp:** 20260710T004713Z · overall=**supported** · kineteq_backend=`absent`

| policy | rubric | illegal_rate | routes |
| --- | ---: | ---: | --- |
| gated | 0.980 | 0.000 | `{"validate_iv": 40}` |
| random | 0.627 | 0.000 | `{"burst_again": 18, "compact_protect": 11, "validate_iv": 11}` |
| select_by_C | 0.727 | 0.000 | `{"validate_iv": 20, "burst_again": 20}` |

## Verdicts
- **RT10_gated_vs_random**: `supported` — `{"gated_rubric": 0.9803, "random_rubric": 0.627, "delta": 0.3533, "gated_illegal_rate": 0.0, "select_by_C_illegal_rate": 0.0, "select_by_C_rubric": 0.7272}`
- **RT10_illegal_route_zero**: `supported` — `{"illegal_rate": 0.0}`

## Route semantics
- `validate_iv` — only when R≥τ (illegal otherwise)
- `compact_protect` — when mid-constraint retention soft
- `burst_again` — when H low or C still exploratory
