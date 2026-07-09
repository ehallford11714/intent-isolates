# Lit-review grounded burst experiments

- Created: `2026-07-09T23:20:38.185873+00:00`
- Hops: `5` · fixtures: `4`

## Lit → condition mapping

| condition | lit idea | mode |
| --- | --- | --- |
| linear | document-order baseline (no divergent search) | `linear` |
| random | unconstrained exploration baseline | `random` |
| motif_jump | Mednick associative / motif-guided search | `motif_jump` |
| creative_burst_v1 | prior creative_burst (soft anchor + novelty) | `creative_burst` |
| divergent_guilford | Guilford divergent: maximize novelty/entropy/fluency | `creative_burst_v2` |
| convergent_constrained | Constrained / convergent creativity: high anchor schedule | `creative_burst_v2` |
| novelty_boden | Boden exploratory: high novelty_weight within space | `creative_burst_v2` |
| layer_cot | CoT scaffolding: forward layer_bias | `creative_burst_v2` |
| creative_burst_v2 | P0 hybrid: novelty+motif+anchor+layer (recommended defaults) | `creative_burst_v2` |
| multipath_tot | ToT/GoT: k paths, select by CreativityMeter harmonic C∧R | `creative_burst_v2` |

## Summary (CreativityMeter)

| condition | C | R | H | CxR | entropy | anchor_R | layer_mono | novelty | flex |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| linear | 0.688 | 0.645 | 0.657 | 0.440 | 2.147 | 0.625 | 0.683 | 0.792 | 0.330 |
| random | 0.744 | 0.701 | 0.713 | 0.520 | 2.279 | 0.764 | 0.583 | 0.847 | 0.476 |
| motif_jump | 0.590 | 0.956 | 0.725 | 0.566 | 1.855 | 0.950 | 0.967 | 0.667 | 0.110 |
| creative_burst_v1 | 0.778 | 0.721 | 0.745 | 0.564 | 2.363 | 0.812 | 0.550 | 0.889 | 0.560 |
| divergent_guilford | 0.787 | 0.666 | 0.711 | 0.524 | 2.474 | 0.738 | 0.533 | 0.944 | 0.490 |
| convergent_constrained | 0.655 | 0.896 | 0.750 | 0.583 | 1.977 | 0.983 | 0.733 | 0.722 | 0.310 |
| novelty_boden | 0.756 | 0.732 | 0.739 | 0.554 | 2.363 | 0.829 | 0.550 | 0.889 | 0.448 |
| layer_cot | 0.716 | 0.812 | 0.752 | 0.578 | 2.203 | 0.917 | 0.617 | 0.820 | 0.400 |
| creative_burst_v2 | 0.726 | 0.795 | 0.754 | 0.576 | 2.241 | 0.900 | 0.600 | 0.833 | 0.418 |
| multipath_tot | 0.720 | 0.823 | 0.766 | 0.595 | 2.213 | 0.917 | 0.650 | 0.820 | 0.418 |

## Ranked by harmonic H (C∧R)

1. `multipath_tot`
2. `creative_burst_v2`
3. `layer_cot`
4. `convergent_constrained`
5. `creative_burst_v1`
6. `novelty_boden`
7. `motif_jump`
8. `random`
9. `divergent_guilford`
10. `linear`

## Verdict

- creative_burst_v2 improved R vs v1 (0.795 > 0.721).
- v2 harmonic tradeoff H>=random (0.754 >= 0.713).
- ToT multi-path select-by-meter matched/beat single v2 on H (0.766 >= 0.754).
- Convergent/constrained condition preserved anchors >= divergent (as lit predicts).
- Divergent condition entropy >= convergent (Guilford fluency/flexibility proxy).
- Best H (C∧R): multipath_tot=0.766, creative_burst_v2=0.754, layer_cot=0.752

## Hypothesis

Lit-grounded hop policies: divergent raises C/entropy; constrained raises R/anchors; v2 hybrid and ToT multi-path improve harmonic tradeoff vs random/linear.

