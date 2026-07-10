# P0 Follow-up Experiment Results — 20260710T002719Z

Offline slate: **E1** multipath value-function · **E2** protect→burst · **E3** structured incubation.

- Fixtures: 8 · seeds: 5 · base hops: 5
- PromptDict: `promptdict`
- Commands: `python experiments/p0_followup_experiments.py`

## E1 — Multipath value function

| condition | k | select | C | R | H | anchor_R | layer_mono |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| mp_k3_C | 3 | C | 0.742 | 0.778 | 0.754 | 0.887 | 0.575 |
| mp_k3_H | 3 | H | 0.722 | 0.829 | 0.767 | 0.923 | 0.655 |
| mp_k3_R | 3 | R | 0.699 | 0.845 | 0.758 | 0.933 | 0.680 |
| mp_k3_iv_diag | 3 | iv_diag | 0.700 | 0.845 | 0.759 | 0.933 | 0.680 |
| mp_k3_product | 3 | product | 0.718 | 0.834 | 0.767 | 0.928 | 0.660 |
| mp_k5_C | 5 | C | 0.766 | 0.744 | 0.751 | 0.843 | 0.560 |
| mp_k5_H | 5 | H | 0.727 | 0.829 | 0.771 | 0.923 | 0.655 |
| mp_k5_R | 5 | R | 0.698 | 0.850 | 0.760 | 0.933 | 0.695 |
| mp_k5_iv_diag | 5 | iv_diag | 0.698 | 0.850 | 0.760 | 0.933 | 0.695 |
| mp_k5_product | 5 | product | 0.723 | 0.834 | 0.770 | 0.928 | 0.660 |
| mp_k7_C | 7 | C | 0.769 | 0.732 | 0.747 | 0.833 | 0.545 |
| mp_k7_H | 7 | H | 0.724 | 0.843 | 0.776 | 0.923 | 0.695 |
| mp_k7_R | 7 | R | 0.696 | 0.862 | 0.765 | 0.933 | 0.730 |
| mp_k7_iv_diag | 7 | iv_diag | 0.706 | 0.862 | 0.772 | 0.933 | 0.730 |
| mp_k7_product | 7 | product | 0.716 | 0.855 | 0.775 | 0.928 | 0.720 |

### Hypotheses

- **E1a_selectH_wins_H_k3**: `supported` — select-by-H ≥ select-by-R/C on H `{"mean_H_by": {"H": 0.7669, "R": 0.7585, "C": 0.7539}, "best": "mp_k3_H", "fixture_wins": "8/8"}`
- **E1b_selectR_wins_R_k3**: `supported` — select-by-R ≥ select-by-H/C on R (may cost H) `{"mean_R_by": {"H": 0.8294, "R": 0.8447, "C": 0.7778}, "mean_H_by": {"H": 0.7669, "R": 0.7585, "C": 0.7539}, "delta_H_vs_Hselect": -0.0084, "best": "mp_k3_R"}`
- **E1c_G1_H_vs_C_on_R_k3**: `supported` — select-by-H ≥ select-by-C on R `{"mean_R": {"H": 0.8294, "C": 0.7778}, "delta": 0.0516, "fixture_wins": "8/8", "strength": "strong"}`
- **E1a_selectH_wins_H_k5**: `supported` — select-by-H ≥ select-by-R/C on H `{"mean_H_by": {"H": 0.7707, "R": 0.76, "C": 0.7511}, "best": "mp_k5_H", "fixture_wins": "8/8"}`
- **E1b_selectR_wins_R_k5**: `supported` — select-by-R ≥ select-by-H/C on R (may cost H) `{"mean_R_by": {"H": 0.8294, "R": 0.8499, "C": 0.7442}, "mean_H_by": {"H": 0.7707, "R": 0.76, "C": 0.7511}, "delta_H_vs_Hselect": -0.0107, "best": "mp_k5_R"}`
- **E1c_G1_H_vs_C_on_R_k5**: `supported` — select-by-H ≥ select-by-C on R `{"mean_R": {"H": 0.8294, "C": 0.7442}, "delta": 0.0852, "fixture_wins": "8/8", "strength": "strong"}`
- **E1a_selectH_wins_H_k7**: `supported` — select-by-H ≥ select-by-R/C on H `{"mean_H_by": {"H": 0.7757, "R": 0.7648, "C": 0.7473}, "best": "mp_k7_H", "fixture_wins": "8/8"}`
- **E1b_selectR_wins_R_k7**: `supported` — select-by-R ≥ select-by-H/C on R (may cost H) `{"mean_R_by": {"H": 0.8434, "R": 0.8622, "C": 0.7324}, "mean_H_by": {"H": 0.7757, "R": 0.7648, "C": 0.7473}, "delta_H_vs_Hselect": -0.0109, "best": "mp_k7_R"}`
- **E1c_G1_H_vs_C_on_R_k7**: `supported` — select-by-H ≥ select-by-C on R `{"mean_R": {"H": 0.8434, "C": 0.7324}, "delta": 0.111, "fixture_wins": "8/8", "strength": "strong"}`
- **E1d_iv_diag_vs_H_k5**: `rejected` — iv_diag H ≥ H-select−0.01 and R ≥ H-select R (RT1 success) `{"avg_H": {"H": 0.7707, "iv_diag": 0.76}, "avg_R": {"H": 0.8294, "iv_diag": 0.8499}, "avg_layer_mono": {"H": 0.655, "iv_diag": 0.695}}`
- **E1d_iv_diag_vs_H_k7**: `supported` — iv_diag H ≥ H-select−0.01 and R ≥ H-select R (RT1 success) `{"avg_H": {"H": 0.7757, "iv_diag": 0.7717}, "avg_R": {"H": 0.8434, "iv_diag": 0.8622}, "avg_layer_mono": {"H": 0.695, "iv_diag": 0.73}}`

## E2 — Protect-compact → burst

| condition | C | R | H | anchor_R | mid_R | pool | neglect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw_v2 | 0.727 | 0.799 | 0.754 | 0.890 | 1.000 | 8.375 | 0.000 |
| truncate_v2 | 0.758 | 0.851 | 0.799 | 1.000 | 0.188 | 2.875 | 0.000 |
| protect_compact_v2 | 0.673 | 0.886 | 0.758 | 0.988 | 1.000 | 5.500 | 0.000 |
| protect_compact_mpH | 0.677 | 0.897 | 0.767 | 1.000 | 1.000 | 5.500 | 0.000 |

### Hypotheses

- **E2a_mid_R_protect_vs_truncate**: `supported` — protect mid_constraint_R ≥ 0.95 and ≫ truncate `{"protect_mid_R": 1.0, "truncate_mid_R": 0.1875}`
- **E2b_protect_mpH_beats_truncate_on_RH**: `mixed` — protect_compact→multipath_H beats truncate→v2 on R and H `{"protect_mpH": {"R": 0.8972, "H": 0.7666}, "truncate_v2": {"R": 0.8513, "H": 0.7989}}`
- **E2c_protect_v2_near_raw**: `supported` — protect→v2 R ≥ raw_v2 R − 0.05 `{"protect_R": 0.8856, "raw_R": 0.7987, "delta": 0.0869}`
- **E2d_truncate_not_pool_artifact_winner**: `artifact_risk` — If truncate H>protect H, require comparable pool (±30%); else flag artifact `{"truncate_H": 0.7989, "protect_H": 0.7579, "pools": {"truncate": 2.875, "protect": 5.5, "raw": 8.375}}`

## E3 — Structured incubation

| hops | condition | C | R | H | anchor_R | layer_mono |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 5 | convergent_fixed | 0.675 | 0.883 | 0.759 | 0.978 | 0.705 |
| 5 | creative_burst_v2 | 0.727 | 0.799 | 0.754 | 0.890 | 0.630 |
| 5 | divergent_fixed | 0.764 | 0.724 | 0.735 | 0.802 | 0.580 |
| 5 | multipath_k5_H | 0.727 | 0.829 | 0.771 | 0.923 | 0.655 |
| 5 | structured_incubation | 0.684 | 0.694 | 0.686 | 0.756 | 0.577 |
| 8 | convergent_fixed | 0.719 | 0.879 | 0.786 | 1.000 | 0.653 |
| 8 | creative_burst_v2 | 0.721 | 0.884 | 0.790 | 1.000 | 0.670 |
| 8 | divergent_fixed | 0.731 | 0.880 | 0.795 | 1.000 | 0.658 |
| 8 | multipath_k5_H | 0.736 | 0.889 | 0.803 | 1.000 | 0.683 |
| 8 | structured_incubation | 0.685 | 0.714 | 0.695 | 0.797 | 0.559 |

### Hypotheses

- **E3a_incubation_beats_v2_H_hops5**: `rejected` — structured incubation H ≥ v2_same_hops (≥5/8 fixtures) `{"mean_H": {"incubation": 0.686, "v2": 0.7539, "multipath_H": 0.7707}, "mean_C": {"incubation": 0.6842, "v2": 0.7267}, "fixture_wins_vs_v2": "0/8", "fixture_wins_vs_mp": "0/8"}`
- **E3b_incubation_vs_multipath_H_hops5**: `rejected` — incubation competitive with multipath_k5_H on H (within 0.01) `{"delta_H": -0.0847}`
- **E3a_incubation_beats_v2_H_hops8**: `rejected` — structured incubation H ≥ v2_same_hops (≥5/8 fixtures) `{"mean_H": {"incubation": 0.6954, "v2": 0.7901, "multipath_H": 0.8029}, "mean_C": {"incubation": 0.6854, "v2": 0.721}, "fixture_wins_vs_v2": "0/8", "fixture_wins_vs_mp": "0/8"}`
- **E3b_incubation_vs_multipath_H_hops8**: `rejected` — incubation competitive with multipath_k5_H on H (within 0.01) `{"delta_H": -0.1075}`

## Verdict snapshot

| ID | Verdict |
| --- | --- |
| E1a_selectH_wins_H_k3 | **supported** |
| E1b_selectR_wins_R_k3 | **supported** |
| E1c_G1_H_vs_C_on_R_k3 | **supported** |
| E1a_selectH_wins_H_k5 | **supported** |
| E1b_selectR_wins_R_k5 | **supported** |
| E1c_G1_H_vs_C_on_R_k5 | **supported** |
| E1a_selectH_wins_H_k7 | **supported** |
| E1b_selectR_wins_R_k7 | **supported** |
| E1c_G1_H_vs_C_on_R_k7 | **supported** |
| E1d_iv_diag_vs_H_k5 | **rejected** |
| E1d_iv_diag_vs_H_k7 | **supported** |
| E2a_mid_R_protect_vs_truncate | **supported** |
| E2b_protect_mpH_beats_truncate_on_RH | **mixed** |
| E2c_protect_v2_near_raw | **supported** |
| E2d_truncate_not_pool_artifact_winner | **artifact_risk** |
| E3a_incubation_beats_v2_H_hops5 | **rejected** |
| E3b_incubation_vs_multipath_H_hops5 | **rejected** |
| E3a_incubation_beats_v2_H_hops8 | **rejected** |
| E3b_incubation_vs_multipath_H_hops8 | **rejected** |
