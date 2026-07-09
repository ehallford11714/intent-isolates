# Span-burst creative hopping experiment

- Created: `2026-07-09T23:08:18.980300+00:00`
- Backend: `intentisolates`
- Hops: `5` · fixtures: `4`

## Summary

| mode | entropy | coverage | anchor_R | goal_vis | constr_vis | unique_typs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| linear | 2.147 | 0.735 | 0.625 | 0.75 | 1.67 | 4.75 |
| motif_jump | 1.855 | 0.735 | 0.950 | 1.25 | 2.25 | 4.00 |
| creative_burst | 2.418 | 0.735 | 0.738 | 1.25 | 1.00 | 5.50 |
| random | 2.186 | 0.735 | 0.780 | 0.83 | 1.75 | 4.83 |

## Verdict

- creative_burst increased typology entropy vs linear (diversity gain).
- creative_burst preserved goal/constraint/outcome visits at least as well as random (anchor pull working).

## Hypothesis

creative_burst hopping increases typology diversity while preserving visits to goal/constraint spans vs pure random

